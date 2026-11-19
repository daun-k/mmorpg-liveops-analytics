"""
리텐션 / 퍼널 테이블 내보내기 (MySQL -> CSV)

태블로 대시보드의 [신규 유저 상세] 페이지에 쓰는 테이블 2개를 SQL 로 만들어서 CSV 로 저장한다.
    output/dashboard_data/YYYYMMDD_Retention.csv : 기간 중 가입한 계정 1개당 1행. 가입 후 1, 3, 7, 14일째에 접속했는지 (1 / 0 / 빈 값)
    output/dashboard_data/YYYYMMDD_Funnel.csv    : 기간 중 가입한 계정이 도달한 퍼널 단계 1개당 1행
    (YYYYMMDD = 데이터 마지막 날짜 + 1일. update_report.py 의 파일명 규칙과 같다)

두 파일 모두 태블로에서 users.csv 와 user_id 로 연결해서 쓴다.

사용법 (load_to_db.py 로 DB 에 데이터를 넣은 뒤에 실행한다)
    python export_retention_funnel.py
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from data_source import get_engine

# 결과를 저장할 폴더: 프로젝트 폴더/output/dashboard_data
OUTPUT_FOLDER = Path(__file__).resolve().parent.parent / "output" / "dashboard_data"

# 리텐션을 볼 날짜 (가입 후 며칠째)
RETENTION_DAYS = [1, 3, 7, 14]

# 데이터의 마지막 날짜 (파일명 날짜와, 리텐션을 아직 알 수 없는 계정을 가려내는 데 쓴다)
LAST_DATE_SQL = "SELECT MAX(`date`) FROM daily_activity"

# 리텐션: 기간 중 가입한 계정마다, 가입 후 N일째 되는 날에 접속 기록이 있으면 1, 없으면 0
#   - DATEDIFF(접속일, 가입일) = N  ->  가입 후 N일째에 접속했다는 뜻
#   - 대상은 관측 기간 안에 가입한 계정 (가입일이 daily_activity 의 첫 날짜 이후)
RETENTION_SQL = """
SELECT u.user_id,
       DATE(u.signup_date) AS signup_date,
       MAX(CASE WHEN DATEDIFF(d.`date`, u.signup_date) = 1  THEN 1 ELSE 0 END) AS retained_day_1,
       MAX(CASE WHEN DATEDIFF(d.`date`, u.signup_date) = 3  THEN 1 ELSE 0 END) AS retained_day_3,
       MAX(CASE WHEN DATEDIFF(d.`date`, u.signup_date) = 7  THEN 1 ELSE 0 END) AS retained_day_7,
       MAX(CASE WHEN DATEDIFF(d.`date`, u.signup_date) = 14 THEN 1 ELSE 0 END) AS retained_day_14
FROM users AS u
LEFT JOIN daily_activity AS d ON d.user_id = u.user_id
WHERE u.signup_date >= (SELECT MIN(`date`) FROM daily_activity)
GROUP BY u.user_id, u.signup_date
ORDER BY u.user_id
"""

# 퍼널: 위쪽 SELECT 는 0단계(가입). 기간 중 가입한 모든 계정이 한 줄씩 들어간다
#       아래쪽 SELECT 는 1~4단계. funnel_events 에 그 이벤트가 있는 계정만 들어간다
#       (guild_join, reach_lv45, reach_lv60 은 4단계 퍼널에 포함하지 않는다. data/README_data.kr.md 참고)
FUNNEL_SQL = """
SELECT u.user_id,
       0        AS step_order,
       'signup' AS step_name
FROM users AS u
WHERE u.signup_date >= (SELECT MIN(`date`) FROM daily_activity)

UNION ALL

SELECT u.user_id,
       CASE e.event WHEN 'tutorial_complete' THEN 1
                    WHEN 'reach_lv10'        THEN 2
                    WHEN 'first_dungeon'     THEN 3
                    WHEN 'reach_lv30'        THEN 4 END AS step_order,
       e.event AS step_name
FROM users AS u
JOIN funnel_events AS e ON e.user_id = u.user_id
WHERE u.signup_date >= (SELECT MIN(`date`) FROM daily_activity)
  AND e.event IN ('tutorial_complete', 'reach_lv10', 'first_dungeon', 'reach_lv30')

ORDER BY user_id, step_order
"""


def main():
    # 1. DB 에서 SQL 결과를 읽는다
    engine = get_engine()
    with engine.connect() as connection:
        last_date = pd.Timestamp(connection.execute(text(LAST_DATE_SQL)).scalar())
        retention = pd.read_sql(text(RETENTION_SQL), connection, parse_dates=["signup_date"])
        funnel = pd.read_sql(text(FUNNEL_SQL), connection)

    # 2. 리텐션을 아직 알 수 없는 칸은 비운다
    #    예) 9월 25일 가입 계정의 7일째는 10월 2일인데, 데이터는 9월 28일까지만 있다.
    #        이 칸을 0 으로 두면 '돌아오지 않았다'로 계산되어 최근 가입자의 리텐션이 실제보다 낮게 나온다.
    for day in RETENTION_DAYS:
        column = f"retained_day_{day}"
        retention[column] = retention[column].astype("Int64")              # 빈 값을 넣을 수 있는 정수형
        target_date = retention["signup_date"] + pd.Timedelta(days=day)    # 가입 후 day 일째 되는 날짜
        retention.loc[target_date > last_date, column] = pd.NA

    # 3. 파일명 날짜 = 데이터 마지막 날짜 + 1일 (update_report.py 와 같은 규칙)
    report_date = last_date + pd.Timedelta(days=1)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    retention_file = OUTPUT_FOLDER / f"{report_date:%Y%m%d}_Retention.csv"
    funnel_file = OUTPUT_FOLDER / f"{report_date:%Y%m%d}_Funnel.csv"

    retention["signup_date"] = retention["signup_date"].dt.date            # 2026-07-01 00:00:00 -> 2026-07-01
    retention.to_csv(retention_file, index=False)
    funnel.to_csv(funnel_file, index=False)

    # 4. 확인용 숫자를 화면에 보여 준다
    print(f"[완료] {retention_file}  ({len(retention):,}행)")
    for day in RETENTION_DAYS:
        column = f"retained_day_{day}"
        print(f"    가입 후 {day}일째 리텐션: {retention[column].mean() * 100:.1f}%  (대상 {retention[column].notna().sum():,}계정)")
    print(f"[완료] {funnel_file}  ({len(funnel):,}행)")
    for step_name, count in funnel.groupby(["step_order", "step_name"]).size().items():
        print(f"    {step_name[0]}단계 {step_name[1]}: {count:,}계정")


if __name__ == "__main__":
    main()