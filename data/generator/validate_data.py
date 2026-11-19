"""Consistency checks for the simulated MMORPG tables.  usage: python validate_data.py <data_dir>"""
import re
import sys

import pandas as pd

d = sys.argv[1] if len(sys.argv) > 1 else "final/data"
u = pd.read_csv(f"{d}/users.csv", parse_dates=["signup_date"])
a = pd.read_csv(f"{d}/daily_activity.csv", parse_dates=["date"])
p = pd.read_csv(f"{d}/payments.csv", parse_dates=["paid_at"])
f = pd.read_csv(f"{d}/funnel_events.csv", parse_dates=["event_time"])
W0, W1 = pd.Timestamp("2026-07-01"), pd.Timestamp("2026-09-28")
bad = {}


def chk(name, mask):
    n = int(mask.sum()) if hasattr(mask, "sum") else int(mask)
    bad[name] = n
    print(("OK   " if n == 0 else "FAIL ") + f"{name}: {n}")


# keys / formats
chk("users.user_id unique", u.user_id.duplicated())
chk("users nulls", u.isna().any(axis=1))
chk("device_id format DV+10 hex", ~u.device_id.str.fullmatch(r"DV[0-9A-F]{10}"))
chk("platform values", ~u.platform.isin(["PC", "Mobile"]))
chk("signup_date <= window end", u.signup_date > W1)
for n, t in [("daily_activity", a), ("payments", p), ("funnel_events", f)]:
    chk(f"{n}.user_id in users", ~t.user_id.isin(u.user_id))
chk("daily_activity (user,date) unique", a.duplicated(["user_id", "date"]))
chk("activity dates inside window", (a.date < W0) | (a.date > W1))
chk("activity nulls", a.isna().any(axis=1))
chk("sessions>=1, playtime>0", (a.sessions < 1) | (a.playtime_min <= 0))
chk("playtime <= 1440", a.playtime_min > 1440)
chk("level >= 1", a.level < 1)
chk("gold/items >= 0", (a.gold_earned < 0) | (a.items_acquired < 0))

# activity vs signup
m = a.merge(u[["user_id", "signup_date"]], on="user_id")
chk("no activity before signup", m.date < m.signup_date)
new = u[u.signup_date >= W0]
first = a.groupby("user_id").date.min()
nn = new.set_index("user_id").signup_date
fl = first.reindex(nn.index)
chk("new accounts: first activity on signup day (or none)", fl.notna() & (fl != nn))
chk("new accounts all active on signup day", fl.isna())

# level monotone per user
s = a.sort_values(["user_id", "date"])
chk("level never decreases", (s.groupby("user_id")["level"].diff() < 0))

# payments
chk("payments nulls", p.isna().any(axis=1))
chk("payments amount > 0", p.amount_krw <= 0)
chk("payments inside window", (p.paid_at < W0) | (p.paid_at >= W1 + pd.Timedelta(days=1)))
pd_ = p.assign(date=p.paid_at.dt.normalize()).merge(a[["user_id", "date"]], on=["user_id", "date"], how="left", indicator=True)
chk("payments only on active days", pd_._merge != "both")
mt = lambda t: (t.dt.dayofweek == 2) & (t.dt.hour >= 5) & (t.dt.hour < 9)
chk("payments outside Wed 05-09 maintenance", mt(p.paid_at))
chk("funnel events outside Wed 05-09 maintenance", mt(f.event_time))

# funnel
chk("funnel event names", ~f.event.isin(["tutorial_complete", "reach_lv10", "first_dungeon", "reach_lv30", "reach_lv45", "reach_lv60", "guild_join"]))
chk("funnel duplicates", f.duplicated(["user_id", "event"]))
fd = f.assign(date=f.event_time.dt.normalize()).merge(a[["user_id", "date"]], on=["user_id", "date"], how="left", indicator=True)
chk("funnel events only on active days", fd._merge != "both")
chk("funnel inside window", (f.event_time < W0) | (f.event_time >= W1 + pd.Timedelta(days=1)))
pv = f.pivot(index="user_id", columns="event", values="event_time")
for c in ["tutorial_complete", "reach_lv10", "first_dungeon", "reach_lv30", "reach_lv45", "reach_lv60", "guild_join"]:
    if c not in pv:
        pv[c] = pd.NaT
pv = pv.join(u.set_index("user_id").signup_date)
pn = pv[pv.signup_date >= W0]
chk("new: lv10 requires tutorial", pn.reach_lv10.notna() & pn.tutorial_complete.isna())
chk("new: first_dungeon requires lv10", pn.first_dungeon.notna() & pn.reach_lv10.isna())
chk("new: lv30 requires first_dungeon", pn.reach_lv30.notna() & pn.first_dungeon.isna())
chk("new: lv45 requires lv30", pn.reach_lv45.notna() & pn.reach_lv30.isna())
chk("new: lv60 requires lv45", pn.reach_lv60.notna() & pn.reach_lv45.isna())
chk("new: guild_join requires first_dungeon", pn.guild_join.notna() & pn.first_dungeon.isna())
chk("new: step order", (pn.reach_lv10 < pn.tutorial_complete) | (pn.first_dungeon < pn.reach_lv10) | (pn.reach_lv30 < pn.first_dungeon)
    | (pn.reach_lv45 <= pn.reach_lv30) | (pn.reach_lv60 <= pn.reach_lv45))
chk("new: guild_join later than first_dungeon", pn.guild_join <= pn.first_dungeon)
pe = pv[pv.signup_date < W0]
chk("existing: lv60 after lv45 and lv45 after lv30 when both exist", (pe.reach_lv45 <= pe.reach_lv30) | (pe.reach_lv60 <= pe.reach_lv45))
chk("existing: only guild_join/lv30/lv45/lv60 events", pe.tutorial_complete.notna() | pe.reach_lv10.notna() | pe.first_dungeon.notna())
# level consistency with funnel events
lv = a.merge(f[f.event == "reach_lv30"].assign(date=lambda x: x.event_time.dt.normalize())[["user_id", "date"]], on=["user_id", "date"])
chk("level >= 30 on reach_lv30 day", lv.level < 30)
l10 = a.merge(f[f.event == "reach_lv10"].assign(date=lambda x: x.event_time.dt.normalize())[["user_id", "date"]], on=["user_id", "date"])
chk("level >= 10 on reach_lv10 day", l10.level < 10)
for th, ev_ in [(45, "reach_lv45"), (60, "reach_lv60")]:
    x = f[f.event == ev_].assign(date=lambda t: t.event_time.dt.normalize())[["user_id", "date"]]
    chk(f"level >= {th} on {ev_} day", a.merge(x, on=["user_id", "date"]).level.lt(th))
    # first crossing: the previous recorded level of that account is still below the threshold
    aa = a.sort_values(["user_id", "date"]).assign(prev=lambda t: t.groupby("user_id")["level"].shift(1))
    chk(f"{ev_} is the first crossing", aa.merge(x, on=["user_id", "date"]).prev.ge(th))
    first_day = aa[aa.level >= th].groupby("user_id").head(1)[["user_id", "date"]]
    chk(f"{ev_} on the first day level >= {th}", x.merge(first_day, on=["user_id", "date"], how="left", indicator=True)._merge.ne("both"))
# level caps: <=5 w/o tutorial, <=10 w/o first dungeon (new accounts)
mn = a.merge(pn[["tutorial_complete", "first_dungeon"]], left_on="user_id", right_index=True)
chk("new: level<=5 until tutorial", (mn.tutorial_complete.isna() | (mn.date < mn.tutorial_complete.dt.normalize())) & (mn.level > 5))
chk("new: level<=10 until first_dungeon", (mn.first_dungeon.isna() | (mn.date < mn.first_dungeon.dt.normalize())) & (mn.level > 10))

print("\nTOTAL violations:", sum(bad.values()))
sys.exit(1 if sum(bad.values()) else 0)
