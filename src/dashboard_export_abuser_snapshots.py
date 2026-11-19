"""
날짜별 어뷰저 판정 결과 내보내기 (대시보드용)

대시보드에서 조회 종료일을 바꾸면, 그 날짜 기준의 어뷰저 판정을 보여 주기 위한 파일을 만든다.
날짜마다 '그날 포함 최근 ABUSE_DAYS 일' 활동으로 판정을 돌려서(abuser.py 와 같은 규칙),
의심 / 고위험 의심 계정만 한 파일에 모은다. 파일에 없는 계정은 그날 기준 '정상'이다.

    - 첫 기준일 = 데이터 첫날 + (MIN_ACTIVE_DAYS - 1)일 (그 전에는 활동일 7일을 채운 계정이 없음)
    - 마지막 기준일 = 데이터 마지막 날
    - 저장: output/dashboard_data/YYYYMMDD_Abuser_Snapshots.csv (YYYYMMDD = 데이터 마지막 날짜 + 1일)
    - 컬럼: as_of_date, user_id, risk, n_signals, 신호 5개(1/0)

사용법
    python export_abuser_snapshots.py
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from abuser import ABUSE_DAYS, MIN_ACTIVE_DAYS, SIGNAL_COLS, detect_abusers
from data_source import get_engine, load_account_metrics


def main():
    engine = get_engine()
    with engine.connect() as conn:
        first, last = conn.execute(text("SELECT MIN(`date`), MAX(`date`) FROM daily_activity")).one()
    first, last = pd.Timestamp(first), pd.Timestamp(last)
    dates = pd.date_range(first + pd.Timedelta(days=MIN_ACTIVE_DAYS - 1), last, freq="D")

    rows = []
    for d in dates:
        acct = detect_abusers(load_account_metrics(engine, d))
        sus = acct[acct["risk"] != "normal"]
        part = sus[["user_id", "risk", "n_signals"] + SIGNAL_COLS].copy()
        part[SIGNAL_COLS] = part[SIGNAL_COLS].astype(int)
        part.insert(0, "as_of_date", d.date())
        rows.append(part)
        print(f"{d:%Y-%m-%d}: 판정 대상 {len(acct):,} / 의심 {(sus.risk == 'suspected').sum()} / 고위험 {(sus.risk == 'highly_suspected').sum()}")

    out = pd.concat(rows, ignore_index=True)
    out_dir = Path(__file__).resolve().parent.parent / "output" / "dashboard_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{last + pd.Timedelta(days=1):%Y%m%d}_Abuser_Snapshots.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[완료] {path}  ({len(out):,}행, 기준일 {len(dates)}개, 판정 기간 최근 {ABUSE_DAYS}일)")


if __name__ == "__main__":
    main()
