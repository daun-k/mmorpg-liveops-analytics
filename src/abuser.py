"""
어뷰저 탐지 (규칙 기반)

계정별 지표(data_source.load_account_metrics 가 SQL 로 계산)에 판정 기준을 적용해서
신호 5개 / 신호 수 / 등급을 붙인다. 활동일 MIN_ACTIVE_DAYS 이상 계정만 반환한다.

판정 기간: 기준일(asof) 포함 최근 ABUSE_DAYS 일의 활동만 본다 (전체 기간 X).
    예) 기준일 9/28, ABUSE_DAYS = 30 -> 8/30 ~ 9/28 의 일별 활동으로 계정 지표를 계산
    오래전에 어뷰징을 그만둔 계정은 빠지고, 최근에 시작한 어뷰징은 긴 기간 평균에 묻히지 않는다.
    '빠른 성장' 신호는 첫 던전 클리어가 이 기간 안에 있을 때만 계산한다.
"""
import numpy as np
import pandas as pd

# ============================================================
# 설정 (판정 기준을 바꾸고 싶으면 여기만 수정)
# ============================================================
ABUSE_DAYS = 30          # 판정 기간: 기준일 포함 최근 며칠의 활동으로 판정할지
MIN_ACTIVE_DAYS = 7      # 판정 기간 안의 활동일이 이보다 적은 계정은 어뷰저 판정 대상에서 제외
GOLD_CV_MAX = 0.3        # 골드 일별 변동계수가 이보다 작으면 '규칙적 획득'
ITEM_CV_MAX = 0.35       # 아이템 일별 변동계수가 이보다 작으면 '규칙적 획득'
FAST_DUNGEON_HRS = 1.7   # 튜토리얼 -> 첫 던전이 이보다 빠르면 '빠른 성장'
SIGNAL_COLS = ["flag_playtime", "flag_gold_speed", "flag_item_speed", "flag_regular", "flag_fast_growth"]


def upper_fence(s):
    """IQR 상한 = Q3 + 1.5 x IQR"""
    q1, q3 = s.quantile([0.25, 0.75])
    return q3 + 1.5 * (q3 - q1)


def detect_abusers(acct):
    """계정별 지표 -> 어뷰저 신호/등급. 02_abuser_analysis.ipynb 의 규칙 기반 탐지."""
    acct = acct.copy()
    acct["gold_per_hour"] = acct["total_gold"] / (acct["total_playtime"] / 60)
    acct["items_per_hour"] = acct["total_items"] / (acct["total_playtime"] / 60)
    acct["gold_cv"] = acct["gold_std"] / acct["gold_mean"]
    acct["item_cv"] = acct["item_std"] / acct["item_mean"]

    # 튜토리얼 -> 첫 던전까지 걸린 시간(시간 단위). 둘 중 하나라도 없으면 비어 있음
    acct["tut_to_dungeon_hrs"] = (acct["dungeon_time"] - acct["tutorial_time"]).dt.total_seconds() / 3600
    acct = acct.drop(columns=["tutorial_time", "dungeon_time"])
    acct = acct[acct["active_days"] >= MIN_ACTIVE_DAYS].reset_index(drop=True)

    fence = {"play": upper_fence(acct["avg_playtime_min"]), "gold": upper_fence(acct["gold_per_hour"]),
             "item": upper_fence(acct["items_per_hour"])}
    acct["flag_playtime"] = acct["avg_playtime_min"] > fence["play"]
    acct["flag_gold_speed"] = acct["gold_per_hour"] > fence["gold"]
    acct["flag_item_speed"] = acct["items_per_hour"] > fence["item"]
    acct["flag_regular"] = (acct["gold_cv"] < GOLD_CV_MAX) | (acct["item_cv"] < ITEM_CV_MAX)
    acct["flag_fast_growth"] = acct["tut_to_dungeon_hrs"] < FAST_DUNGEON_HRS
    acct["n_signals"] = acct[SIGNAL_COLS].sum(axis=1)
    acct["risk"] = np.select([acct["n_signals"] >= 3, acct["n_signals"] == 2],
                             ["highly_suspected", "suspected"], default="normal")
    return acct
