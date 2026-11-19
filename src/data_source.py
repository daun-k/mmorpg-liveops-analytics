"""
데이터 읽기 (MySQL)

접속 정보는 프로젝트 폴더의 .env 파일에서 읽는다 (GitHub 에는 올리지 않는다. .env.example 참고).
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, URL

PROJECT_DIR = Path(__file__).resolve().parent.parent        # src 폴더의 상위 폴더 (.env 가 있는 곳)


def get_engine():
    """.env 의 접속 정보로 DB 연결(engine)을 만든다."""
    load_dotenv(PROJECT_DIR / ".env")
    keys = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise SystemExit(f"{PROJECT_DIR / '.env'} 에 {', '.join(missing)} 값이 없습니다. .env.example 을 참고해서 채워 주세요.")

    url = URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


def load_tables(engine):
    """리포트의 숨김 시트에 넣을 원본 4개 테이블을 읽는다."""
    with engine.connect() as conn:
        users = pd.read_sql(text("SELECT * FROM users"), conn, parse_dates=["signup_date"])
        daily = pd.read_sql(text("SELECT * FROM daily_activity"), conn, parse_dates=["date"])
        pay = pd.read_sql(text("SELECT * FROM payments"), conn, parse_dates=["paid_at"])
        events = pd.read_sql(text("SELECT * FROM funnel_events"), conn, parse_dates=["event_time"])
    pay["date"] = pay["paid_at"].dt.normalize()
    return users, daily, pay, events


# 계정별 지표: 판정 기간(:start_date ~ :end_date)의 일별 활동(daily_activity)을 계정 단위로 집계하고,
# 튜토리얼 완료 / 첫 던전 시각(funnel_events)을 계정별 최초 시각으로 붙인다.
# 첫 던전 시각은 판정 기간 안에 있을 때만 붙인다 (기간 밖이면 비어 있음 -> '빠른 성장' 신호 없음).
# (* 1e0 은 정수 컬럼의 평균/표준편차가 소수점 4자리로 잘려서 나오지 않게 실수로 계산하려는 것)
ACCOUNT_METRICS_SQL = """
SELECT d.user_id,
       d.active_days,
       d.avg_playtime_min,
       d.total_playtime,
       d.total_gold,
       d.total_items,
       d.gold_mean,
       d.gold_std,
       d.item_mean,
       d.item_std,
       e.tutorial_time,
       e.dungeon_time
FROM (
    SELECT user_id,
           COUNT(DISTINCT `date`)        AS active_days,
           AVG(playtime_min)             AS avg_playtime_min,
           SUM(playtime_min)             AS total_playtime,
           SUM(gold_earned)              AS total_gold,
           SUM(items_acquired)           AS total_items,
           AVG(gold_earned * 1e0)        AS gold_mean,
           STDDEV_SAMP(gold_earned * 1e0)      AS gold_std,
           AVG(items_acquired * 1e0)           AS item_mean,
           STDDEV_SAMP(items_acquired * 1e0)   AS item_std
    FROM daily_activity
    WHERE `date` BETWEEN :start_date AND :end_date
    GROUP BY user_id
) AS d
LEFT JOIN (
    SELECT user_id,
           MIN(CASE WHEN event = 'tutorial_complete' THEN event_time END) AS tutorial_time,
           MIN(CASE WHEN event = 'first_dungeon'
                     AND DATE(event_time) BETWEEN :start_date AND :end_date THEN event_time END) AS dungeon_time
    FROM funnel_events
    WHERE event IN ('tutorial_complete', 'first_dungeon')
    GROUP BY user_id
) AS e ON d.user_id = e.user_id
ORDER BY d.user_id
"""


def get_last_date(engine):
    """데이터 마지막 날짜 (daily_activity 의 가장 늦은 date)"""
    with engine.connect() as conn:
        return pd.Timestamp(conn.execute(text("SELECT MAX(`date`) FROM daily_activity")).scalar())


def load_account_metrics(engine, asof=None, days=None):
    """기준일(asof) 포함 최근 days 일의 계정별 지표.
    asof 를 비우면 데이터 마지막 날짜, days 를 비우면 abuser.ABUSE_DAYS 를 쓴다."""
    from abuser import ABUSE_DAYS
    asof = pd.Timestamp(asof) if asof is not None else get_last_date(engine)
    days = days or ABUSE_DAYS
    start = asof - pd.Timedelta(days=days - 1)
    params = {"start_date": start.date(), "end_date": asof.date()}
    with engine.connect() as conn:
        return pd.read_sql(text(ACCOUNT_METRICS_SQL), conn, params=params, parse_dates=["tutorial_time", "dungeon_time"])
