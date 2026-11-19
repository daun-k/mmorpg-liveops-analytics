"""
CSV -> MySQL 적재

원본 CSV 4개를 DB 테이블로 넣는다. 데이터가 새로 생겼을 때만 실행하면 된다 (같은 이름의 테이블은 지우고 새로 만든다).

사용법
    python load_to_db.py
    python load_to_db.py --data-dir ../data
"""
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.types import String

from data_source import get_engine

# 테이블 이름: (CSV 파일, 날짜로 읽을 컬럼, 문자열 컬럼의 길이)
TABLES = {
    "users": ("users.csv", ["signup_date"], {"country": String(8), "platform": String(16), "device_id": String(32)}),
    "daily_activity": ("daily_activity.csv", ["date"], {}),
    "payments": ("payments.csv", ["paid_at"], {}),
    "funnel_events": ("funnel_events.csv", ["event_time"], {"event": String(32)}),
}

# 조회가 빨라지도록 만드는 인덱스: (이름, 테이블, 컬럼)
INDEXES = [
    ("idx_daily_user", "daily_activity", "user_id"),
    ("idx_daily_date", "daily_activity", "`date`"),
    ("idx_pay_user", "payments", "user_id"),
    ("idx_events_user_event", "funnel_events", "user_id, event"),
]


def load_all(engine, data_dir):
    for name, (csv, date_cols, dtypes) in TABLES.items():
        df = pd.read_csv(Path(data_dir) / csv, parse_dates=date_cols)
        df.to_sql(name, engine, if_exists="replace", index=False, chunksize=10000, dtype=dtypes)
        print(f"{name}: {len(df):,}행")

    with engine.begin() as conn:
        for idx, table, cols in INDEXES:
            conn.execute(text(f"CREATE INDEX {idx} ON {table} ({cols})"))

    with engine.connect() as conn:
        for name in TABLES:
            print(f"[확인] {name}: DB {conn.execute(text(f'SELECT COUNT(*) FROM {name}')).scalar():,}행")


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(here.parent / "data"), help="CSV 폴더")
    args = ap.parse_args()
    load_all(get_engine(), args.data_dir)


if __name__ == "__main__":
    main()
