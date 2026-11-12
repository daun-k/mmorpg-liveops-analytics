# Aurelion Online: Live-Service Simulation Data Specification

[한국어](README_data.kr.md) | [English](README_data.md)

> Operational logs of a fictional MMORPG, **Aurelion Online**. This is not real service data. It was generated with Claude for practicing live-service analytics (KPI reporting, anomaly and abuse detection, hypothesis testing). The generator is `gen_mmorpg_data.py` (seed 42) and the consistency checker is `validate_data.py`.

## 1. Scenario

- A global live-service MMORPG about one year after launch (PC + mobile cross-platform; countries KR/JP/US/TW/OTHER)
- Observation window: **2026-07-01 to 2026-09-28 (90 days)**
- All times are server time (a single time zone).

## 2. Service timeline

| Date | Type | Content |
|---|---|---|
| Every Wednesday 05:00-09:00 | Weekly maintenance | Server maintenance. No logins, payments or events are recorded in this window |
| Every Thursday | Weekly content | Weekly dungeons and quests reset |
| 07-21 to 07-27 | Summer Festival, part 1 | Limited-time event with a marketing ad campaign. Event coins, limited costumes, bonus payment bundles |
| 08-15 to 08-21 | Summer Festival, part 2 | Same format as part 1 (ads run again) |
| 08-30 | Growth overhaul update | (1) Field hunting XP cut by 20% (growth pacing) (2) New region for Lv45+ (3) Equipment enhancement packs go on sale (4) Large client patch (mobile takes longer to finish updating) |
| 09-08 | Hotfix | The XP cut is eased from 20% to 10% (effective from 09-08) |
| 09-09 to 09-15 | Comeback support event | Return rewards for players who have been away, attendance rewards for everyone else |

## 3. Game rules reflected in the data

- The level cap is 60. Level rises only with accumulated XP and never goes down. The XP needed per level grows with level, and leveling slows down further after Lv10 and again after Lv30.
- **Four-step growth funnel**: `tutorial_complete` -> `reach_lv10` -> `first_dungeon` (first dungeon cleared) -> `reach_lv30`. Each step unlocks only after the previous one. Later milestones `reach_lv45` and `reach_lv60` (level cap) are also recorded, but they are not part of the four-step funnel.
  - A player who does not finish the tutorial can only reach Lv5.
  - Before clearing the first dungeon, a player cannot go past Lv10 (leveling stops at Lv10).
- **Joining a guild (`guild_join`) is optional.** Players can reach Lv30 without a guild; joining becomes possible after the first dungeon is cleared.
- There is no stamina/fatigue system and no auto-hunting. Daily playtime is simply time spent in game.
- Purchases come in six price points (KRW 1,100 / 5,500 / 11,000 / 33,000 / 55,000 / 110,000).

### 3-1. Leveling speed (design reference)

**Cumulative play time** computed from the XP needed per level and the XP efficiency by level, before the update (field XP at 100%). It assumes only XP accumulation, ignoring separate requirements such as attempting a dungeon.

| Target | Cumulative play time | Note |
|---|---|---|
| Lv5 | about 0.5 h | The limit if the tutorial is not finished |
| Lv10 | about 2.2 h | |
| Lv30 | about 11.9 h | Lv10 to Lv30 takes about 9.7 h |
| Lv45 | about 38.5 h | Entry level of the new region (from 08-30) |
| Lv60 | about 126.7 h | Level cap |

- Playing 1 hour a day, this means about 2 to 3 days to Lv10 and about 12 days to Lv30.
- After the 08-30 update cut field XP by 20%, reaching the same level takes about 25% longer; after the 09-08 hotfix (10% cut) it takes about 11% longer.
- Clearing the first dungeon is a separate challenge, not a level requirement, so it has no time in the table above.

## 4. Files and sizes

| File | Rows | Description |
|---|---|---|
| `users.csv` | 34,000 | Account master |
| `daily_activity.csv` | 268,799 | One row per account per active day |
| `payments.csv` | 2,917 | One row per purchase |
| `funnel_events.csv` | 23,597 | One row per growth/guild event |

The largest file is about 9.8 MB (under GitHub's 25 MB web upload limit).

## 5. Table specifications

### 5.1 `users`: account master

One row per account. **Dormant accounts (no login for 90+ consecutive days) are excluded.** Every account that signed up inside the window is included.

| Column | Type | Description | Notes |
|---|---|---|---|
| `user_id` | INT | Account ID (PK) | Assigned in sign-up order |
| `signup_date` | DATE | Sign-up date | 2025-07-01 to 2026-09-28 |
| `country` | VARCHAR | Country at sign-up | KR, JP, US, TW, OTHER |
| `platform` | VARCHAR | Main platform | PC, Mobile |
| `device_id` | VARCHAR | Device identifier | `DV` + 10 uppercase hex digits. Accounts used on the same device share a value |

### 5.2 `daily_activity`: daily activity

A row exists only on days the account logged in (`user_id` + `date` is unique). Days without a login have no row.

| Column | Type | Description | Notes |
|---|---|---|---|
| `user_id` | INT | Account ID (FK -> users) | |
| `date` | DATE | Login date | 2026-07-01 to 2026-09-28, on or after sign-up |
| `sessions` | INT | Number of sessions that day | At least 1 |
| `playtime_min` | FLOAT | Total play time that day (minutes) | Above 0, at most 1,440 |
| `level` | INT | Character level at the end of the day | 1 to 60; never decreases over time for an account |
| `gold_earned` | INT | Gold earned that day | 0 or more |
| `items_acquired` | INT | Items acquired that day | 0 or more |

### 5.3 `payments`: purchases

| Column | Type | Description | Notes |
|---|---|---|---|
| `user_id` | INT | Account ID (FK -> users) | Only accounts that were active on the payment day |
| `paid_at` | DATETIME | Payment time | None during weekly maintenance (Wed 05-09h) |
| `amount_krw` | INT | Amount in KRW | One of the six price points |

### 5.4 `funnel_events`: growth events

| Column | Type | Description | Notes |
|---|---|---|---|
| `user_id` | INT | Account ID (FK -> users) | Only accounts that were active at that time |
| `event` | VARCHAR | Event name | `tutorial_complete`, `reach_lv10`, `first_dungeon`, `reach_lv30`, `reach_lv45`, `reach_lv60`, `guild_join` |
| `event_time` | DATETIME | When it happened | None during weekly maintenance |

- An (account, event) pair is unique; the same event is never logged twice.
- **Only events that happened inside the window are recorded.** An account that signed up before the window may have passed the tutorial, Lv10 and the first dungeon already, but those rows do not exist. Such accounts only show `guild_join`, `reach_lv30`, `reach_lv45` and `reach_lv60` if they happened inside the window, and an account that had already passed a level before the window has no row for that level. Funnel conversion should therefore be computed **only for accounts that signed up inside the window (`signup_date >= '2026-07-01'`)**.

## 6. Notes for using the data

- **Many accounts have no activity rows.** More than half of the existing accounts in `users` (signed up before the window, 28,000) never logged in during the window and have no rows in `daily_activity`. They logged in within the 90 days before the window but not during it. Decide whether the denominator of each metric is all of `users` or only active accounts before you start.
- To include accounts without activity, use `users LEFT JOIN daily_activity`.
- Activity before the window is not recorded, so the "last login before the window" of an existing account is unknown.
- Levels never decrease. If an account's level seems to drop, the query is wrong.
- Events and payments exist only on days when the account logged in. A new account always has activity on its sign-up day.
- Every account that signed up inside the window has at least one activity row (the sign-up day).
- Several accounts may share a device (families, internet cafes, and so on).
- This is a simulation: value distributions are set by hand and are not real-game benchmarks. Things the simulation does not model include player-to-player interaction, detailed content structure, and refunds or cancelled payments.

## 7. Generation and validation scripts

| File | Role | Run (from the repository root) |
|---|---|---|
| `gen_mmorpg_data.py` | Simulation data generator. It updates each account's level, XP and funnel progress day by day, produces logins, purchases and events, and writes the four CSV files plus the label file (`_answer_key_labels.csv`). The seed is fixed, so the same command produces the same data. | `python data/generator/gen_mmorpg_data.py --seed 42 --out data --answer-out answer_key` |
| `validate_data.py` | Consistency checker for the generated CSVs. It checks about 50 items, including keys and formats, activity before sign-up, level decreases, funnel prerequisites and order, events and payments on days without a login, and records inside the maintenance window, and prints the number of violations (exit code 1 if any). The current data has 0 violations. | `python data/generator/validate_data.py data` |

- `reach_lv45` and `reach_lv60` are derived from the finished `daily_activity` table after the simulation (with a separate random stream), so the other tables and the earlier events are not affected.
- Required packages: `numpy`, `pandas`.
- The `--no-update` option of `gen_mmorpg_data.py` creates a comparison dataset without the 08-30 update, the 09-08 hotfix and the comeback event. It is not needed for the analysis.
- The analysis only needs the CSV files. The two scripts show how the data was created and verified.

## License

This project was created for portfolio purposes, and all rights are reserved by the author. Please refrain from copying, distributing, or using it commercially without permission.
