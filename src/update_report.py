"""
Aurelion Online 일일 리포트 업데이트

MySQL 에 들어 있는 원본 데이터를 SQL 로 읽어서, 빈 포맷(엑셀 템플릿)에 넣고 월 블록을 만들어 xlsx 로 내보낸다.
    1. data_source.py : DB 에서 데이터 읽기 (원본 테이블 + SQL 로 집계한 계정별 지표)
    2. abuser.py      : 어뷰저 판정 (판정 기준과 판정 기간 ABUSE_DAYS 는 abuser.py 위쪽 설정에서 수정)
    3. excel_report.py: 엑셀 리포트 만들기
    4. output/reports/YYYYMMDD_Aurelion_Daily_Report.xlsx 와 output/abuser_list/YYYYMMDD_Abuser_List.csv 로 저장한다
       (YYYYMMDD = 데이터 마지막 날짜 + 1일)

사용법 (처음 한 번은 CSV 를 DB 에 넣는다)
    python load_to_db.py
    python update_report.py
    python update_report.py --template ../report_template/aurelion_report_template.xlsx --out-dir ../output

필요 패키지: pandas, numpy, openpyxl, sqlalchemy, pymysql, python-dotenv  (requirements.txt)
참고: 이 파일로 만든 xlsx 는 수식 계산 결과가 저장되어 있지 않다. 엑셀에서 열면(편집 사용 클릭) 바로 계산된다.
"""
import argparse
from pathlib import Path

import pandas as pd

from abuser import SIGNAL_COLS, detect_abusers
from data_source import get_engine, load_account_metrics, load_tables
from excel_report import build_workbook, save_workbook


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    ap.add_argument("--template", default=str(here.parent / "report_template" / "aurelion_report_template.xlsx"),
                    help="빈 포맷 엑셀")
    ap.add_argument("--out-dir", default=str(here.parent / "output"), help="산출물 폴더 (reports/, abuser_list/ 가 만들어짐)")
    args = ap.parse_args()

    engine = get_engine()
    users, daily, pay, events = load_tables(engine)
    asof = daily["date"].max()
    acct = detect_abusers(load_account_metrics(engine, asof))   # 리포트 날짜 기준 최근 ABUSE_DAYS 일로 판정

    wb, sus = build_workbook(args.template, users, daily, pay, events, acct, asof)

    out_dir = Path(args.out_dir)
    (out_dir / "reports").mkdir(parents=True, exist_ok=True)
    (out_dir / "abuser_list").mkdir(parents=True, exist_ok=True)
    report_date = asof + pd.Timedelta(days=1)                    # 파일명 날짜 = 데이터 마지막 날짜 + 1일 (리포트는 데이터가 완성된 다음 날 본다)
    xlsx = out_dir / "reports" / f"{report_date:%Y%m%d}_Aurelion_Daily_Report.xlsx"
    save_workbook(wb, xlsx)

    csv = out_dir / "abuser_list" / f"{report_date:%Y%m%d}_Abuser_List.csv"
    cols = ["user_id", "risk", "n_signals"] + SIGNAL_COLS
    acct.loc[sorted(sus.index), cols].to_csv(csv, index=False, encoding="utf-8-sig")
    print(f"[완료] {xlsx}")
    print(f"[완료] {csv}  (의심 {int((sus.risk == 'suspected').sum())}계정 / 고위험 의심 {int((sus.risk == 'highly_suspected').sum())}계정)")


if __name__ == "__main__":
    main()
