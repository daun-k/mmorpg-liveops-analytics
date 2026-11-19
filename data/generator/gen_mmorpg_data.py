"""
Aurelion Online - simulated live-service logs (NOT real data).

A fictional MMORPG that launched about a year before the observation window
(2026-07-01 .. 2026-09-28).  Every account is simulated day by day with a persistent
state (xp, level, funnel progress), so the logs are internally consistent by construction:
  * level never decreases
  * funnel events and payments only happen on days the account was active, inside that day's play window
  * funnel steps follow the game's unlock rules (see README_data.md)

Accounts
  * existing accounts (signed up before the window, not dormant on 2026-07-01); many of them never log in
    during the window (lapsed), which is why `users` is larger than the set of active accounts
  * new sign-ups inside the window
The story behind each pattern (seasonal promotions, the 08-30 update, the 09-08 hotfix, weekly
maintenance, abusive accounts) is documented in README_data.md and ANSWER_KEY.md.

Usage (from the repository root):
    python data/generator/gen_mmorpg_data.py --seed 42 --out data --answer-out answer_key

    --no-update   counterfactual run without the 08-30 update, the 09-08 hotfix and the return event
                  (only used to measure the size of those effects for ANSWER_KEY.md)
"""
import argparse
import os

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--out", default="data", help="folder for the four CSV tables")
parser.add_argument("--answer-out", default=None, help="folder for _answer_key_labels.csv (default: same as --out)")
parser.add_argument("--no-update", action="store_true", help="counterfactual: no 08-30 update / 09-08 hotfix")
args = parser.parse_args()

rng = np.random.default_rng(args.seed)
DAYS = 90
START = pd.Timestamp("2026-07-01")
os.makedirs(args.out, exist_ok=True)
ans_dir = args.answer_out or args.out
os.makedirs(ans_dir, exist_ok=True)

day_idx = np.arange(DAYS)
dow_day = (START + pd.to_timedelta(day_idx, unit="D")).dayofweek.to_numpy()   # Mon=0

CAS, COR, WHA, BOT, AFK, FAR, LAP = range(7)
SEG_NAMES = np.array(["casual", "core", "whale", "bot", "longplay_human", "workshop", "lapsed"])
HUM_STD = [CAS, COR, WHA, LAP]          # ordinary players (lapsed = existing accounts that mostly stopped playing)
HUM_ALL = [CAS, COR, WHA, LAP, AFK]

# ------------------------------------------------------------------ calendar (day index 0 = 2026-07-01)
SF1 = (20, 26)          # summer festival part 1   07-21 .. 07-27
SF2 = (45, 51)          # summer festival part 2   08-15 .. 08-21
PATCH_DAY = 60          # growth overhaul update   08-30
HOTFIX_DAY = 69         # hotfix                   09-08 (effective from that day)
RET = (70, 76)          # comeback support event   09-09 .. 09-15
if args.no_update:
    PATCH_DAY = HOTFIX_DAY = 10 ** 6
    RET = (10 ** 6, 10 ** 6)
event_day = np.zeros(DAYS, bool)
for a_, b_ in (SF1, SF2):
    event_day[a_:b_ + 1] = True
FEST_SCALE = np.zeros(DAYS)                           # how strongly the festival moves existing players: part 1 strong, part 2 weaker
FEST_SCALE[SF1[0]:SF1[1] + 1] = 1.0
FEST_SCALE[SF2[0]:SF2[1] + 1] = 0.6
ret_day = np.zeros(DAYS, bool)
if RET[0] < DAYS:
    ret_day[RET[0]:RET[1] + 1] = True

# dissatisfaction after the update: full effect until the hotfix, then fades over about a week
D = np.zeros(DAYS)
XPM = np.ones(DAYS)                                   # field xp multiplier (-20% -> -10%)
for d_ in range(DAYS):
    if PATCH_DAY <= d_ < HOTFIX_DAY:
        D[d_], XPM[d_] = 1.0, 0.8
    elif d_ >= HOTFIX_DAY:
        D[d_], XPM[d_] = np.exp(-(d_ - HOTFIX_DAY + 1) / 2.5), 0.9

# ------------------------------------------------------------------ weekly pattern (Mon..Sun)
# Wednesday = weekly maintenance (05:00-09:00), Thursday = fresh weekly content, weekend peak
WD_ACT = np.array([0.98, 0.97, 0.90, 1.04, 1.00, 1.12, 1.10])
WD_PAY = np.array([1.00, 0.95, 0.85, 1.00, 1.15, 1.25, 1.05])
MAINT_DOW, MAINT_START, MAINT_END = 2, 5 * 60, 9 * 60

# ------------------------------------------------------------------ population
N_NEW = 6000
VET = {CAS: 5040, COR: 3480, WHA: 645, LAP: 18500, BOT: 110, FAR: 150, AFK: 75}
NEW_AB = {BOT: 70, FAR: 90, AFK: 45}

seg_v = np.concatenate([np.full(c, s) for s, c in VET.items()])
n_vet = len(seg_v)
# existing accounts: sign-up 2025-07-01 .. 2026-06-30; active ones skew recent, lapsed ones skew old
ages = np.arange(1, 366)
sd_v = np.zeros(n_vet, int)
pos = 0
for s, c in VET.items():
    w = (0.5 + ages / 365.0) if s == LAP else (np.exp(-ages / 240.0) + 0.02)
    sd_v[pos:pos + c] = -rng.choice(ages, size=c, p=w / w.sum())
    pos += c

# new sign-ups: steady inflow + two seasonal promotions (decaying peak)
w0 = np.where(dow_day >= 5, 1.2, 1.0)
sf1_x = np.where((day_idx >= SF1[0]) & (day_idx <= SF1[1]), 5.5 * np.exp(-(day_idx - SF1[0]) / 2.5), 0.0)
sf2_x = np.where((day_idx >= SF2[0]) & (day_idx <= SF2[1]), 5.0 * np.exp(-(day_idx - SF2[0]) / 2.5), 0.0)
w_tot = w0 + sf1_x + sf2_x
sd_n = np.sort(rng.choice(DAYS, N_NEW, p=w_tot / w_tot.sum()))
promo_n = rng.random(N_NEW) < ((sf1_x + sf2_x) / w_tot)[sd_n]
seg_n = np.full(N_NEW, -1)
perm_n = rng.permutation(N_NEW)
pos = 0
for s, c in NEW_AB.items():
    seg_n[perm_n[pos:pos + c]] = s
    pos += c
u_ = rng.random(N_NEW)
cas_th = np.where(promo_n, 0.62, 0.62)
cor_th = np.where(promo_n, 0.93, 0.93)
seg_n = np.where(seg_n < 0, np.where(u_ < cas_th, CAS, np.where(u_ < cor_th, COR, WHA)), seg_n)

N = n_vet + N_NEW
seg = np.concatenate([seg_v, seg_n])
signup_day = np.concatenate([sd_v, sd_n])
is_vet = np.concatenate([np.ones(n_vet, bool), np.zeros(N_NEW, bool)])
promo_driven = np.concatenate([np.zeros(n_vet, bool), promo_n])
order = np.lexsort((rng.random(N), signup_day))        # user_id follows sign-up order
seg, signup_day, is_vet, promo_driven = seg[order], signup_day[order], is_vet[order], promo_driven[order]
user_id = np.arange(1, N + 1)
is_human = np.isin(seg, HUM_ALL)

country = rng.choice(["KR", "JP", "US", "TW", "OTHER"], N, p=[0.45, 0.20, 0.18, 0.10, 0.07])
platform = rng.choice(["PC", "Mobile"], N, p=[0.6, 0.4])


# ------------------------------------------------------------------ device ids (one uniform format for everyone)
def make_ids(k):
    ids = np.unique(rng.integers(0, 16 ** 10, size=k + 100))
    while len(ids) < k:
        ids = np.unique(np.concatenate([ids, rng.integers(0, 16 ** 10, size=k)]))
    ids = rng.permutation(ids)[:k]
    return np.array([f"DV{int(x):010X}" for x in ids], dtype=object)


N_FARM_DEV = 12
all_ids = make_ids(N + N_FARM_DEV)
device_id = all_ids[:N].copy()
farm_pool = all_ids[N:]
farm_pool_platform = rng.choice(["PC", "Mobile"], N_FARM_DEV, p=[0.75, 0.25])
far_i = np.where(seg == FAR)[0]
pool_pick = rng.integers(0, N_FARM_DEV, len(far_i))
device_id[far_i] = farm_pool[pool_pick]
platform[far_i] = farm_pool_platform[pool_pick]

# ~2% of ordinary accounts share a device: families (2-4 accounts) and PC cafes (3-10 accounts, PC only)
normal_idx = rng.permutation(np.where(np.isin(seg, HUM_STD))[0])
target_share = int(0.02 * len(normal_idx))
pos, shared = 0, 0
while shared < target_share and pos < len(normal_idx):
    cafe = rng.random() >= 0.7
    size = int(rng.integers(3, 11)) if cafe else int(rng.integers(2, 5))
    members = normal_idx[pos:pos + size]
    pos += size
    if len(members) < 2:
        break
    device_id[members] = device_id[members[0]]
    platform[members] = "PC" if cafe else platform[members[0]]
    shared += len(members)
is_mobile = platform == "Mobile"

# ------------------------------------------------------------------ constants (index = segment id)
#                 CAS    COR    WHA    BOT   AFK    FAR    LAP
PLAY_MU = np.array([60.0, 150.0, 200.0, 0.0, 0.0, 0.0, 60.0])
PLAY_SD = np.array([30.0, 50.0, 60.0, 0.0, 0.0, 0.0, 30.0])
SESS_L = np.array([2.0, 3.5, 4.0, 1.0, 2.5, 3.0, 2.0])
GOLD_RATE = np.array([80.0, 80.0, 100.0, 0.0, 100.0, 0.0, 80.0])     # gold per minute of play
ITEM_RATE = np.array([6.0, 9.0, 12.0, 0.0, 12.0, 0.0, 6.0])          # items per hour of play
BASE_N = np.array([0.55, 0.72, 0.85, 1.00, 0.85, 0.95, 0.10])        # new accounts: p = base * (age+1) ** -decay
DECAY_N = np.array([0.90, 0.50, 0.35, 0.00, 0.25, 0.10, 0.00])
PAY_P = np.array([0.0012, 0.0045, 0.040, 0.0, 0.0045, 0.0, 0.0004])
PM_MULT = np.array([1.25, 1.15, 1.05, 1.0, 1.15, 1.0, 1.0])          # seasonal promotion: login
PM_ADD = np.array([0.03, 0.02, 0.01, 0.0, 0.02, 0.0, 0.004])
PM_PAY = np.array([1.6, 1.8, 2.0, 1.0, 1.8, 1.0, 1.4])
RET_MULT = np.array([1.10, 1.05, 1.02, 1.0, 1.05, 1.0, 1.0])         # comeback event: login
RET_ADD = np.array([0.035, 0.025, 0.010, 0.0, 0.025, 0.0, 0.006])
EFF_DIP = np.array([0.20, 0.10, 0.03, 0.0, 0.05, 0.0, 0.20])         # login drop after the update (x D)
EFF_PLAY = np.array([0.20, 0.12, 0.05, 0.0, 0.06, 0.0, 0.20])        # play-time drop after the update (x D)
H_PATCH = np.array([0.008, 0.003, 0.001, 0.0, 0.002, 0.0, 0.002])   # permanent churn caused by the update (x D)
H_ATT = np.array([0.0015, 0.0006, 0.0002, 0.0, 0.0004, 0.0, 0.0])    # existing accounts: slow daily attrition
ENH_A = np.array([0.0, 0.20, 0.35, 0.0, 0.20, 0.0, 0.0])             # enhancement pack payments (x D)
ENH_B = np.array([0.0, 0.05, 0.10, 0.0, 0.05, 0.0, 0.0])             # ... lasting part
TIERS = np.array([1100, 5500, 11000, 33000, 55000, 110000])
TIER_W = {CAS: [0.35, 0.35, 0.20, 0.07, 0.03, 0.00],
          COR: [0.15, 0.30, 0.30, 0.15, 0.08, 0.02],
          WHA: [0.00, 0.05, 0.15, 0.30, 0.30, 0.20]}
TIER_KEY = {CAS: CAS, COR: COR, WHA: WHA, AFK: COR, LAP: CAS}
XP_RATE, XP_EXP, XP_EXP2, XP_EARLY = 48.0, 0.3, 2.5, 0.5     # xp per minute; leveling slows down above Lv10 and again above Lv30

# funnel behaviour of new accounts
TUT_P = np.array([0.90, 0.97, 0.99, 1.00, 0.99, 1.00, 0.90])
DUN_P = np.array([0.45, 0.60, 0.80, 1.00, 0.80, 1.00, 0.45])
DUN_DELAY_P = np.array([0.45, 0.55, 0.70, 1.00, 0.70, 1.00, 0.45])
STUCK_P = np.array([0.50, 0.35, 0.25, 1.00, 0.25, 1.00, 0.50])
GUILD_P = np.array([0.75, 0.90, 0.95, 0.25, 0.95, 0.35, 0.75])
GUILD_DELAY_P = np.array([0.50, 0.55, 0.60, 1.00, 0.60, 0.80, 0.50])
GUILD_VET = np.array([0.60, 0.85, 0.93, 0.20, 0.85, 0.30, 0.40])     # share of existing accounts already in a guild


def need(level):                                  # cumulative xp needed to reach `level`
    return 60.0 * (np.asarray(level, float) - 1.0) ** 1.8


def level_from_xp(xp):
    return np.clip(np.floor((xp / 60.0) ** (1 / 1.8) + 1e-9) + 1, 1, 60).astype(int)


# ------------------------------------------------------------------ per-account parameters
reason = np.zeros(N, int)                         # long-play reason: 1 shop, 2 idle, 3 hardcore
afk_i = np.where(seg == AFK)[0]
reason[afk_i] = rng.choice([1, 2, 3], len(afk_i), p=[0.40, 0.35, 0.25])
heavy = np.zeros(N, bool)
heavy[afk_i] = rng.random(len(afk_i)) < 0.30

base_u = BASE_N[seg].copy()
decay_u = DECAY_N[seg].copy()
base_u[heavy], decay_u[heavy] = 0.98, 0.03

# cohort effect on new accounts' login probability, decided by the day they sign up:
#   festival part 1 (hit)   -> they stay clearly longer;  part 2 (repeat) -> a smaller lift
#   update (flop)           -> sign-ups during it leave early;  after the hotfix -> only half recovered
COH_AMP = np.zeros(N)
COH_RAMP = np.ones(N)
new_std = (~is_vet) & np.isin(seg, [CAS, COR, WHA])
for lo, hi, amp, ramp in [(SF1[0], SF1[1], 0.50, 5.0), (SF2[0], SF2[1], 0.24, 3.0),
                          (PATCH_DAY, HOTFIX_DAY - 1, -0.40, 8.0), (HOTFIX_DAY, DAYS - 1, -0.30, 6.0)]:
    mk = new_std & (signup_day >= lo) & (signup_day <= hi)
    COH_AMP[mk], COH_RAMP[mk] = amp, ramp

# existing accounts: constant daily login probability
pv = np.zeros(N)
pv_draw = {
    LAP: np.clip(rng.lognormal(np.log(0.0007), 1.0, N), 0.0001, 0.02),
    CAS: np.clip(rng.lognormal(np.log(0.08), 0.6, N), 0.01, 0.50),
    COR: np.clip(rng.lognormal(np.log(0.35), 0.4, N), 0.08, 0.95),
    WHA: np.clip(rng.lognormal(np.log(0.60), 0.3, N), 0.25, 0.98),
}
for s, arr in pv_draw.items():
    pv = np.where(seg == s, arr, pv)
pv = np.where(seg == BOT, 1.0, pv)
pv = np.where(seg == FAR, 0.93, pv)
pv = np.where(seg == AFK, np.where(heavy, 0.97, rng.uniform(0.5, 0.9, N)), pv)

bot_mu = rng.normal(1190, 25, N)
g_cv = np.where(seg == BOT, rng.uniform(0.03, 0.22, N), rng.uniform(0.18, 0.70, N))
i_cv = np.where(seg == BOT, rng.uniform(0.03, 0.22, N), rng.uniform(0.18, 0.70, N))
g_mean = np.select(
    [seg == BOT, (seg == AFK) & (reason == 1), (seg == AFK) & (reason == 2), seg == FAR],
    [rng.lognormal(np.log(45000), 0.30, N), rng.lognormal(np.log(25000), 0.35, N),
     rng.lognormal(np.log(3000), 0.50, N), rng.lognormal(np.log(120000), 0.20, N)], 1.0)
i_mean = np.select(
    [seg == BOT, (seg == AFK) & (reason == 1), (seg == AFK) & (reason == 2)],
    [rng.lognormal(np.log(400), 0.35, N), rng.lognormal(np.log(150), 0.40, N),
     rng.lognormal(np.log(15), 0.50, N)], 1.0)
q_left = np.where(reason == 3, rng.uniform(0.25, 0.55, N),
                  np.where(heavy, rng.uniform(0.88, 0.98, N), rng.uniform(0.10, 0.45, N)))

# funnel draws (only new accounts use them; existing accounts are overridden below)
tut_ok = rng.random(N) < TUT_P[seg]
dun_ok = rng.random(N) < DUN_P[seg]
dun_delay = rng.geometric(DUN_DELAY_P[seg])
stuck_tol = rng.geometric(STUCK_P[seg])
guild_ok = rng.random(N) < GUILD_P[seg]
guild_delay = rng.geometric(GUILD_DELAY_P[seg])

# ------------------------------------------------------------------ initial state
lv_lo = np.array([15, 32, 48, 50, 25, 35, 12])
lv_hi = np.array([38, 56, 60, 60, 55, 60, 40])
lv0 = np.ones(N, int)
lv0_v = rng.integers(lv_lo[seg], lv_hi[seg] + 1)
lv0_v = np.where((seg == AFK) & (reason == 3), rng.integers(45, 61, N), lv0_v)
lv0 = np.where(is_vet, lv0_v, 1)
xp = np.where(is_vet, need(lv0) + rng.random(N) * 0.8 * (need(lv0 + 1) - need(lv0)), 0.0)
level = lv0.copy()

tut_ok = np.where(is_vet, True, tut_ok)
dun_ok = np.where(is_vet, True, dun_ok)
guild_done = is_vet & (rng.random(N) < GUILD_VET[seg])
guild_ok = np.where(is_vet, rng.random(N) < 0.5, guild_ok)
lv10_done = is_vet.copy()
dun_done = is_vet.copy()
lv30_done = is_vet & (level >= 30)
gone = np.zeros(N, bool)
cap_days = np.zeros(N, int)
guild_cnt = np.zeros(N, int)

act_chunks, pay_rows, ev_rows = [], [], []
pay_carry = rng.random()
tier_ctr = {s_: rng.random() for s_ in HUM_ALL}
STEP_ORDER = {"tutorial_complete": 0, "reach_lv10": 1, "first_dungeon": 2, "guild_join": 3, "reach_lv30": 4}


def shift_maint(d, t):
    """nothing happens during the weekly maintenance window: push those timestamps to after it"""
    t = np.asarray(t, float).copy()
    if dow_day[d] == MAINT_DOW:
        w = (t >= MAINT_START) & (t < MAINT_END)
        t[w] += 240
    return t


# ------------------------------------------------------------------ day-by-day simulation
for d in range(DAYS):
    age = d - signup_day
    started = age >= 0
    a = np.maximum(age, 0)
    dow = dow_day[d]

    p = np.where(is_vet, pv, base_u * (a + 1.0) ** (-decay_u) * (1.0 + COH_AMP * np.minimum(1.0, a / COH_RAMP)))
    p = np.where(is_human, p * WD_ACT[dow], p)
    if event_day[d]:
        fs = FEST_SCALE[d]
        p = np.where(is_human & is_vet, p * (1 + (PM_MULT[seg] - 1) * fs) + PM_ADD[seg] * fs, p)   # festival lifts existing players; new players' reaction is in COH_AMP
    if ret_day[d]:
        p = np.where(is_human & is_vet, p * RET_MULT[seg] + RET_ADD[seg], p)   # return rewards are aimed at existing accounts
    if d >= PATCH_DAY:
        p = p * (1 - EFF_DIP[seg] * D[d])
        p = np.where(np.isin(seg, [COR, WHA, AFK]) & (level >= 45), p * 1.06, p)   # new region (Lv45+)
        if d <= PATCH_DAY + 2:                          # large client patch: some mobile players update late
            p = np.where(is_human & is_mobile, p * 0.88, p)
    pc = np.clip(p, 0, 1)
    act = (rng.random(N) < pc) & started & ~gone & is_vet
    # new accounts: systematic sampling inside each sign-up-day cohort, so the number of logins per cohort-day
    # follows the designed probabilities closely (who logs in stays random) -> cohort retention is not drowned in noise
    nv = np.flatnonzero((~is_vet) & started & ~gone & (age >= 1))
    if len(nv):
        ordr = nv[np.lexsort((rng.random(len(nv)), signup_day[nv]))]
        gday = signup_day[ordr]
        cuts = np.r_[0, np.flatnonzero(np.diff(gday)) + 1, len(ordr)]
        for lo_, hi_ in zip(cuts[:-1], cuts[1:]):
            members = ordr[lo_:hi_]
            c_ = np.cumsum(pc[members])
            u_ = rng.random()
            sel = np.floor(c_ - u_) > np.floor(np.r_[0.0, c_[:-1]] - u_)
            act[members[sel]] = True
    act |= (age == 0)
    idx = np.flatnonzero(act)
    k = len(idx)
    u_att = rng.random(N)
    u_hz = rng.random(N)
    if k == 0:
        continue
    sg = seg[idx]

    # ---- play time, sessions
    play = np.zeros(k)
    idle_mode = np.zeros(k, bool)
    scale_bot = np.ones(k)
    m = np.isin(sg, HUM_STD)
    if m.any():
        x = np.clip(rng.normal(PLAY_MU[sg[m]], PLAY_SD[sg[m]]), 5, 600)
        if dow >= 5:
            x = x * 1.08
        if d >= PATCH_DAY:
            x = x * (1 - EFF_PLAY[sg[m]] * D[d])
        play[m] = np.clip(x, 5, 600)
    m = sg == AFK
    if m.any():
        j = idx[m]
        longd = rng.random(m.sum()) < q_left[j]
        hi = np.where(reason[j] == 3, 1320.0, 1440.0)
        play[m] = np.where(longd, rng.uniform(1080, hi), np.clip(rng.normal(300, 120, m.sum()), 30, 900))
        idle_mode[m] = longd & (reason[j] != 3)
    m = sg == BOT
    if m.any():
        mu = bot_mu[idx[m]]
        x = np.clip(rng.normal(mu, 20), 1080, 1440)
        crash = rng.random(m.sum()) < 0.01           # occasional restart day
        x = np.where(crash, rng.uniform(500, 1000, m.sum()), x)
        play[m] = x
        scale_bot[m] = np.where(crash, x / mu, 1.0)
    m = sg == FAR
    if m.any():
        play[m] = np.clip(rng.normal(400, 60, m.sum()), 120, 700)

    sess = np.ones(k, int)
    m = np.isin(sg, HUM_STD)
    sess[m] = np.maximum(1, rng.poisson(SESS_L[sg[m]]))
    m = sg == AFK
    sess[m] = np.where(idle_mode[m], 1 + rng.poisson(0.3, m.sum()), 1 + rng.poisson(2.5, m.sum()))
    m = sg == BOT
    sess[m] = 1 + (rng.random(m.sum()) < 0.05)
    m = sg == FAR
    sess[m] = np.maximum(1, rng.poisson(3.0, m.sum()))

    # ---- play window inside the day (used to place event / payment timestamps)
    long_ = play >= 900
    mix = rng.random(k)
    start_min = np.where(mix < 0.55, rng.normal(21 * 60, 100, k),
                         np.where(mix < 0.80, rng.normal(13 * 60, 90, k), rng.uniform(0, 1440, k)))
    start_min = np.clip(start_min, 0, 1439)
    start_min = np.where(long_, rng.uniform(0, np.maximum(1440 - play, 1.0)), start_min)
    end_min = np.minimum(start_min + play, 1439.9)
    S_full, E_full = np.zeros(N), np.zeros(N)
    S_full[idx], E_full[idx] = start_min, end_min

    # ---- funnel state machine (uses state as of the start of the day)
    dun_start = dun_done.copy()
    day_events = {name: np.zeros(N, bool) for name in STEP_ORDER}
    day_events["tutorial_complete"][idx[(age[idx] == 0) & tut_ok[idx]]] = True

    cond_d = act & lv10_done & ~dun_done
    cap_days[cond_d] += 1
    clear = cond_d & dun_ok & (cap_days >= dun_delay)
    dun_done[clear] = True
    day_events["first_dungeon"][clear] = True
    stuck_leave = cond_d & ~dun_ok & (cap_days >= stuck_tol)

    cond_g = act & dun_start & ~guild_done & guild_ok
    guild_cnt[cond_g] += 1
    join = cond_g & (guild_cnt >= guild_delay)
    guild_done[join] = True
    day_events["guild_join"][join] = True

    # ---- xp and level (level is capped by the unlock rule, so it can only go up)
    lvb = level[idx]
    f = (np.minimum(1.0, (10.0 / np.maximum(lvb, 10)) ** XP_EXP)
         * np.where(lvb > 30, (30.0 / np.maximum(lvb, 30)) ** XP_EXP2, 1.0)
         * np.where(lvb < 10, XP_EARLY, 1.0))   # leveling slows down at higher levels; the first levels are gentle
    eff = np.where(idle_mode, 0.15 * play, play)                      # a shop left open earns little xp
    gain = np.zeros(k)
    m = np.isin(sg, HUM_STD) | (sg == AFK)
    gain[m] = eff[m] * XP_RATE * rng.lognormal(-0.02, 0.2, m.sum())
    m = sg == BOT
    gain[m] = rng.uniform(4000, 8000, m.sum())
    m = sg == FAR
    gain[m] = play[m] * 15.0 * rng.lognormal(-0.02, 0.2, m.sum())
    gain = gain * f * XPM[d]

    cap = np.where(~tut_ok[idx], 5, np.where(~dun_done[idx], 10, 60))
    xp_new = np.minimum(xp[idx] + gain, need(cap + 1) - 1e-6)
    xp[idx] = np.maximum(xp[idx], xp_new)
    level[idx] = np.maximum(level[idx], level_from_xp(xp[idx]))

    new10 = act & ~lv10_done & (level >= 10)
    lv10_done[new10] = True
    day_events["reach_lv10"][new10] = True
    new30 = act & ~lv30_done & (level >= 30)
    lv30_done[new30] = True
    day_events["reach_lv30"][new30] = True

    # ---- gold / items
    gold = np.zeros(k)
    items = np.zeros(k)
    lv_now = level[idx]
    mh = np.isin(sg, HUM_STD) | ((sg == AFK) & ~idle_mode)
    if mh.any():
        sig = 0.5
        gold[mh] = (GOLD_RATE[sg[mh]] * play[mh] * (1 + 0.03 * lv_now[mh])
                    * rng.lognormal(-0.5 * sig ** 2, sig, mh.sum()))
        items[mh] = rng.poisson(ITEM_RATE[sg[mh]] * play[mh] / 60 * rng.lognormal(-0.5 * sig ** 2, sig, mh.sum()))
    m = idle_mode
    if m.any():
        j = idx[m]
        gold[m] = g_mean[j] * rng.lognormal(-0.5 * g_cv[j] ** 2, g_cv[j])
        items[m] = np.round(i_mean[j] * rng.lognormal(-0.5 * i_cv[j] ** 2, i_cv[j]))
    m = sg == BOT
    if m.any():
        j = idx[m]
        gold[m] = g_mean[j] * scale_bot[m] * rng.lognormal(-0.5 * g_cv[j] ** 2, g_cv[j])
        items[m] = np.round(i_mean[j] * scale_bot[m] * rng.lognormal(-0.5 * i_cv[j] ** 2, i_cv[j]))
    m = sg == FAR
    if m.any():
        j = idx[m]
        gold[m] = g_mean[j] * rng.lognormal(-0.5 * 0.15 ** 2, 0.15, m.sum())
        items[m] = rng.poisson(30.0 * play[m] / 60 * rng.lognormal(-0.5 * 0.15 ** 2, 0.15, m.sum()))

    act_chunks.append(pd.DataFrame({
        "user_id": user_id[idx], "day": d, "sessions": sess, "playtime_min": np.round(play, 1),
        "level": level[idx], "gold_earned": gold.astype(int), "items_acquired": items.astype(int)}))

    # ---- payments (people only)
    hm = np.isin(sg, HUM_ALL)
    pp = PAY_P[sg] * WD_PAY[dow]
    if event_day[d]:
        pp = pp * (1 + (PM_PAY[sg] - 1) * FEST_SCALE[d])
    if d >= PATCH_DAY:
        pp = pp * (1 + ENH_A[sg] * D[d] + ENH_B[sg] * (1 - D[d]))    # enhancement packs
    # systematic sampling carried across days: the number (and mix) of purchases follows the designed rates closely
    ppm = np.where(hm, pp, 0.0)
    perm_ = rng.permutation(k)
    c_ = pay_carry + np.cumsum(ppm[perm_])
    sel_ = np.floor(c_) > np.floor(np.r_[pay_carry, c_[:-1]])
    pay_carry = c_[-1]
    paid = np.zeros(k, bool)
    paid[perm_[sel_]] = True
    pj = np.flatnonzero(paid)
    if len(pj):
        amt = np.zeros(len(pj), int)
        for s_ in HUM_ALL:
            mm = sg[pj] == s_
            if mm.any():
                n_ = int(mm.sum())
                q_ = rng.permutation((tier_ctr[s_] + 0.6180339887498949 * np.arange(1, n_ + 1)) % 1.0)
                tier_ctr[s_] += 0.6180339887498949 * n_
                amt[mm] = TIERS[np.minimum(np.searchsorted(np.cumsum(TIER_W[TIER_KEY[s_]]), q_), len(TIERS) - 1)]
        t = start_min[pj] + rng.random(len(pj)) * (end_min[pj] - start_min[pj])
        pay_rows.append(pd.DataFrame({"user_id": user_id[idx[pj]], "day": d,
                                      "t_min": shift_maint(d, t), "amount_krw": amt}))

    # ---- funnel event timestamps
    for name, mask in day_events.items():
        ej = np.flatnonzero(mask)
        if len(ej):
            t = S_full[ej] + rng.random(len(ej)) * (E_full[ej] - S_full[ej])
            ev_rows.append(pd.DataFrame({"user_id": user_id[ej], "day": d, "step": STEP_ORDER[name],
                                         "event": name, "t_min": shift_maint(d, t)}))

    # ---- who leaves for good
    gone[idx[(age[idx] == 0) & ~tut_ok[idx]]] = True      # left during the tutorial
    gone[stuck_leave] = True                              # gave up while stuck at the level-10 wall
    gone |= is_vet & (u_att < H_ATT[seg]) & is_human      # slow attrition of existing accounts
    if d >= PATCH_DAY:
        gone |= (u_hz < H_PATCH[seg] * D[d]) & started & (age >= 1)

# ------------------------------------------------------------------ build tables
act = pd.concat(act_chunks, ignore_index=True)
act["date"] = (START + pd.to_timedelta(act["day"], unit="D")).dt.strftime("%Y-%m-%d")
act = act[["user_id", "date", "sessions", "playtime_min", "level", "gold_earned", "items_acquired"]]
act = act.sort_values(["user_id", "date"], kind="stable").reset_index(drop=True)

# every long-play account leaves the client on at least once (keeps the 18h+ user count at bots + long-play people)
has_long = act.loc[act["playtime_min"] >= 1080, "user_id"].unique()
for uid in np.setdiff1d(user_id[seg == AFK], has_long):
    rows = act.index[act["user_id"] == uid]
    if len(rows) == 0:
        continue
    j = int(rng.choice(rows))
    i = uid - 1
    pl = float(rng.uniform(1080, 1300))
    act.loc[j, ["sessions", "playtime_min"]] = [1, round(pl, 1)]
    if reason[i] == 3:
        lv = int(act.loc[j, "level"])
        act.loc[j, "gold_earned"] = int(GOLD_RATE[AFK] * pl * (1 + 0.03 * lv) * rng.lognormal(-0.125, 0.5))
        act.loc[j, "items_acquired"] = int(rng.poisson(ITEM_RATE[AFK] * pl / 60 * rng.lognormal(-0.125, 0.5)))
    else:
        act.loc[j, "gold_earned"] = int(g_mean[i] * rng.lognormal(-0.5 * g_cv[i] ** 2, g_cv[i]))
        act.loc[j, "items_acquired"] = int(round(i_mean[i] * rng.lognormal(-0.5 * i_cv[i] ** 2, i_cv[i])))


def stamp(day, t_min):
    return (START + pd.to_timedelta(np.asarray(day), unit="D")
            + pd.to_timedelta(np.floor(np.asarray(t_min, float) * 60), unit="s")).strftime("%Y-%m-%d %H:%M:%S")


pay = pd.concat(pay_rows, ignore_index=True)
pay["paid_at"] = stamp(pay["day"].to_numpy(), pay["t_min"].to_numpy())
pay = pay.sort_values(["user_id", "paid_at"], kind="stable")[["user_id", "paid_at", "amount_krw"]]

ev = pd.concat(ev_rows, ignore_index=True)
sorted_t = ev.sort_values(["user_id", "day", "t_min"], kind="stable")["t_min"].to_numpy()
ev = ev.sort_values(["user_id", "day", "step"], kind="stable").reset_index(drop=True)
ev["t_min"] = sorted_t                                 # events of one user-day follow the funnel order
ev["event_time"] = stamp(ev["day"].to_numpy(), ev["t_min"].to_numpy())
fun = ev[["user_id", "event", "event_time"]]

users = pd.DataFrame({
    "user_id": user_id,
    "signup_date": (START + pd.to_timedelta(signup_day, unit="D")).strftime("%Y-%m-%d"),
    "country": country, "platform": platform, "device_id": device_id})

labels = pd.DataFrame({"user_id": user_id, "true_segment": SEG_NAMES[seg]})
labels["abuse_type"] = np.where(seg == BOT, "bot", np.where(seg == FAR, "workshop", ""))
labels["longplay_reason"] = np.array(["", "shop", "idle", "hardcore"])[reason]


# ------------------------------------------------------------------ extra level events (post-processing)
# reach_lv45 / reach_lv60 are derived from the finished daily table with a separate RNG, so the simulation
# above, every other table and all earlier funnel events stay exactly as they were.
# An event is recorded on the first active day a level threshold is reached, only if the account started
# the window below that level (same rule as reach_lv10 / reach_lv30).
rng_x = np.random.default_rng([args.seed, 45])
start_lv = pd.Series(lv0, index=user_id)
tod = ev.loc[ev["event"].isin(["reach_lv30", "guild_join"]), "t_min"].to_numpy() % 1440   # time-of-day pool
last_t = ev.groupby(["user_id", "day"])["t_min"].max()                                      # latest earlier event of that user-day
act_d = act.assign(day=(pd.to_datetime(act["date"]) - START).dt.days)
extra = []
for name, th in [("reach_lv45", 45), ("reach_lv60", 60)]:
    first = act_d[act_d["level"] >= th].sort_values(["user_id", "day"]).groupby("user_id").head(1)
    first = first[start_lv.reindex(first["user_id"]).to_numpy() < th]
    extra.append(first[["user_id", "day"]].assign(event=name))
xe = pd.concat(extra, ignore_index=True)
xe["t_min"] = rng_x.choice(tod, len(xe))
lo = last_t.reindex(pd.MultiIndex.from_frame(xe[["user_id", "day"]])).fillna(0).to_numpy()
late = xe["t_min"].to_numpy() <= lo
xe.loc[late, "t_min"] = lo[late] + rng_x.random(late.sum()) * (1439.0 - lo[late])
xe = xe.sort_values(["user_id", "day", "event"], kind="stable").reset_index(drop=True)
both = xe.duplicated(["user_id", "day"], keep=False).to_numpy()                            # lv45 and lv60 on the same day
i45 = np.flatnonzero(both & (xe["event"] == "reach_lv45").to_numpy())
tt = xe["t_min"].to_numpy().copy()
for i in i45:
    tt[i], tt[i + 1] = sorted([tt[i], tt[i + 1]])
tt = tt + 0.0
wed = np.array([dow_day[d_] == MAINT_DOW for d_ in xe["day"]])
inw = wed & (tt >= MAINT_START) & (tt < MAINT_END)
tt[inw] = np.minimum(tt[inw] + 240, 1439.9)
xe["event_time"] = stamp(xe["day"].to_numpy(), tt)
fun = pd.concat([fun, xe[["user_id", "event", "event_time"]]], ignore_index=True)
fun = fun.sort_values(["user_id", "event_time"], kind="stable").reset_index(drop=True)

users.to_csv(f"{args.out}/users.csv", index=False)
act.to_csv(f"{args.out}/daily_activity.csv", index=False)
pay.to_csv(f"{args.out}/payments.csv", index=False)
fun.to_csv(f"{args.out}/funnel_events.csv", index=False)
labels.to_csv(f"{ans_dir}/_answer_key_labels.csv", index=False)   # do NOT peek while analysing

print({"users": len(users), "daily_activity": len(act), "payments": len(pay), "funnel_events": len(fun)})
print(labels["true_segment"].value_counts().to_dict())
print({"active_accounts": int(act["user_id"].nunique()), "inactive_accounts": int(len(users) - act["user_id"].nunique())})
