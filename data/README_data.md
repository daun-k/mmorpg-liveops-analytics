# Aurelion Online 라이브 서비스 시뮬레이션 데이터 명세

> 가상의 MMORPG **Aurelion Online**의 운영 로그입니다. 실제 서비스 데이터가 아니며, 라이브 서비스 분석(KPI 리포트, 이상·어뷰징 탐지, 가설 검정) 연습용으로 Claude를 사용하여 직접 생성했습니다. 생성 코드는 `gen_mmorpg_data.py`(seed 42), 정합성 검사는 `validate_data.py`입니다.

## 1. 시나리오

- 출시 약 1년이 지난 글로벌 라이브 서비스 MMORPG (PC + 모바일 크로스 플랫폼, 국가: KR/JP/US/TW/OTHER)
- 관측 기간: **2026-07-01 ~ 2026-09-28 (90일)**
- 시간 기준은 서버 시각(단일 시간대)입니다.

## 2. 서비스 타임라인

| 날짜 | 구분 | 내용 |
|---|---|---|
| 매주 수요일 05:00~09:00 | 정기 점검 | 서버 점검. 이 시간대에는 접속·결제·이벤트 기록이 없습니다 |
| 매주 목요일 | 주간 콘텐츠 | 주간 던전·퀘스트 초기화 |
| 07-21 ~ 07-27 | 여름 축제 1부 | 기간 한정 이벤트. 마케팅 광고를 함께 집행. 이벤트 코인과 한정 코스튬 판매, 결제 상품 보너스 |
| 08-15 ~ 08-21 | 여름 축제 2부 | 1부와 같은 구성의 시즌 이벤트(광고 재집행) |
| 08-30 | 성장 개편 업데이트 | ① 필드 사냥 경험치 20% 하향(성장 속도 조정) ② Lv45 이상 신규 지역 추가 ③ 장비 강화 패키지 판매 시작 ④ 대용량 클라이언트 패치(모바일은 업데이트 완료까지 시간이 걸림) |
| 09-08 | 핫픽스 | 필드 경험치 하향폭을 20% → 10%로 완화 (09-08부터 적용) |
| 09-09 ~ 09-15 | 복귀 지원 이벤트 | 일정 기간 접속하지 않은 유저 대상 복귀 보상과 일반 유저 대상 출석 보상 |

## 3. 게임 규칙 (데이터에 반영된 것)

- 레벨 상한은 60입니다. 레벨은 경험치 누적으로만 오르며 내려가지 않습니다. 레벨업에 필요한 경험치는 레벨이 높을수록 커지고, Lv10 이후와 Lv30 이후에는 성장 속도가 더 느려집니다.
- **성장 퍼널 4단계**: `tutorial_complete`(튜토리얼 완료) → `reach_lv10`(Lv10 도달) → `first_dungeon`(첫 던전 클리어) → `reach_lv30`(Lv30 도달). 앞 단계를 마쳐야 다음 단계가 열립니다.
  - 튜토리얼을 마치지 못하면 Lv5까지만 오를 수 있습니다.
  - 첫 던전을 클리어하기 전에는 Lv10을 넘길 수 없습니다(Lv10에서 레벨업이 멈춥니다).
- **길드 가입(`guild_join`)은 선택**입니다. 길드 없이도 Lv30까지 성장할 수 있고, 길드 가입은 첫 던전 클리어 이후 가능합니다.
- 피로도·자동사냥 시스템은 없습니다. 하루 플레이 시간은 접속 시간 자체입니다.
- 결제 상품은 6개 가격대(1,100 / 5,500 / 11,000 / 33,000 / 55,000 / 110,000원)입니다.

### 3-1. 레벨 성장 속도 (설계 기준)

레벨업에 필요한 경험치와 레벨별 경험치 효율에서 계산한, 업데이트 이전(필드 경험치 100%) 기준의 **누적 플레이 시간**입니다. 던전 도전과 같은 별도 조건을 제외하고 경험치만 쌓았을 때의 값입니다.

| 목표 | 누적 플레이 시간 | 비고 |
|---|---|---|
| Lv5 | 약 0.5시간 | 튜토리얼을 마치지 못하면 여기까지 |
| Lv10 | 약 2.2시간 | |
| Lv30 | 약 11.9시간 | Lv10 → Lv30은 약 9.7시간 |
| Lv45 | 약 38.5시간 | 신규 지역(8/30 이후) 입장 레벨 |
| Lv60 | 약 126.7시간 | 만렙 |

- 하루 1시간씩 플레이하면 Lv10까지 약 2~3일, Lv30까지 약 12일 걸리는 속도입니다.
- 8/30 업데이트로 필드 경험치가 20% 줄면 같은 레벨까지 걸리는 시간이 약 25% 늘어나고, 09-08 핫픽스 이후(10% 감소)에는 약 11% 늘어납니다.
- 첫 던전 클리어는 레벨 조건이 아니라 별도 도전이라 위 표에 시간이 없습니다.

## 4. 파일과 규모

| 파일 | 행 수 | 설명 |
|---|---|---|
| `users.csv` | 34,000 | 계정 마스터 |
| `daily_activity.csv` | 268,799 | 계정·날짜별 활동(접속한 날만 기록) |
| `payments.csv` | 2,917 | 결제 1건당 1행 |
| `funnel_events.csv` | 18,504 | 성장·길드 이벤트 1건당 1행 |

파일 하나의 최대 크기는 약 9.8MB(GitHub 웹 업로드 한도 25MB 이내)입니다.

## 5. 테이블별 명세

### 5.1 `users` — 계정 마스터

계정 1개당 1행. **90일 이상 연속 접속하지 않은 휴면 계정은 포함하지 않습니다.** 기간 중 신규 가입 계정은 모두 포함됩니다.

| 컬럼 | 타입 | 설명 | 비고 |
|---|---|---|---|
| `user_id` | INT | 계정 ID (PK) | 가입 순서대로 부여 |
| `signup_date` | DATE | 가입일 | 2025-07-01 ~ 2026-09-28 |
| `country` | VARCHAR | 가입 국가 | KR, JP, US, TW, OTHER |
| `platform` | VARCHAR | 주 이용 플랫폼 | PC, Mobile |
| `device_id` | VARCHAR | 기기 식별자 | `DV` + 대문자 16진수 10자리. 한 기기에서 여러 계정을 쓰면 값이 같음 |

### 5.2 `daily_activity` — 일별 활동

접속한 날에만 행이 있습니다(`user_id`, `date` 조합은 유일). 접속하지 않은 날은 행이 없습니다.

| 컬럼 | 타입 | 설명 | 비고 |
|---|---|---|---|
| `user_id` | INT | 계정 ID (FK → users) | |
| `date` | DATE | 접속일 | 2026-07-01 ~ 2026-09-28, 가입일 이후 |
| `sessions` | INT | 그날의 접속 세션 수 | 1 이상 |
| `playtime_min` | FLOAT | 그날의 총 플레이 시간(분) | 0 초과, 1,440 이하 |
| `level` | INT | 그날 마지막 시점의 캐릭터 레벨 | 1~60, 계정별로 날짜가 지나도 줄지 않음 |
| `gold_earned` | INT | 그날 획득한 골드 | 0 이상 |
| `items_acquired` | INT | 그날 획득한 아이템 수 | 0 이상 |

### 5.3 `payments` — 결제

| 컬럼 | 타입 | 설명 | 비고 |
|---|---|---|---|
| `user_id` | INT | 계정 ID (FK → users) | 결제일에 접속 기록이 있는 계정만 |
| `paid_at` | DATETIME | 결제 시각 | 정기 점검 시간대(수 05~09시)에는 없음 |
| `amount_krw` | INT | 결제 금액(원) | 6개 가격대 중 하나 |

### 5.4 `funnel_events` — 성장 이벤트

| 컬럼 | 타입 | 설명 | 비고 |
|---|---|---|---|
| `user_id` | INT | 계정 ID (FK → users) | 해당 시각에 접속 기록이 있는 계정만 |
| `event` | VARCHAR | 이벤트 이름 | `tutorial_complete`, `reach_lv10`, `first_dungeon`, `reach_lv30`, `guild_join` |
| `event_time` | DATETIME | 발생 시각 | 정기 점검 시간대에는 없음 |

- 계정·이벤트 조합은 유일합니다(같은 이벤트가 두 번 찍히지 않음).
- **관측 기간 안에서 일어난 이벤트만 기록됩니다.** 기간 시작 전에 가입한 계정은 튜토리얼·Lv10·첫 던전을 이미 지났을 수 있어도 해당 행이 없습니다. 이런 계정에는 기간 안에 발생한 `guild_join`, `reach_lv30`만 나타납니다. 따라서 퍼널 전환율은 **기간 중 가입한 계정(`signup_date >= '2026-07-01'`)만** 대상으로 계산해야 합니다.

## 6. 데이터를 쓸 때 알아둘 점

- **활동 기록이 없는 계정이 많습니다.** `users`의 기존 계정(기간 이전 가입, 28,000명) 중 절반 이상은 기간 안에 한 번도 접속하지 않아 `daily_activity`에 행이 없습니다. 최근 90일 안에는 접속했지만 기간에는 접속하지 않은 계정입니다. 지표의 분모를 `users` 전체로 할지, 활동한 계정으로 할지 정의하고 시작하세요.
- 활동 없는 계정을 포함해 집계하려면 `users LEFT JOIN daily_activity`를 쓰세요.
- 기간 시작 이전의 활동은 기록되어 있지 않습니다. 기존 계정의 "기간 이전 마지막 접속일"은 알 수 없습니다.
- 레벨은 감소하지 않습니다. 같은 계정의 레벨이 줄어든 것처럼 보이면 쿼리 오류입니다.
- 이벤트와 결제는 모두 그 계정이 접속한 날에만 존재합니다. 가입한 날에는 항상 접속 기록이 있습니다.
- 접속 기록이 하루도 없는 신규 가입 계정은 없습니다(가입일에 한 번은 접속).
- 기기 하나를 여러 계정이 쓰는 경우가 있습니다(가족, PC방 등).
- 이 데이터는 시뮬레이션이므로 값의 분포는 임의로 설정한 것이며, 실제 게임의 벤치마크가 아닙니다. 시뮬레이션 설계와 실제 게임의 차이(예: 유저 간 상호작용, 세밀한 콘텐츠 구조, 환불·취소 결제)는 반영하지 않았습니다.

## 7. 생성·검증 스크립트

| 파일 | 역할 | 실행 (레포 루트에서) |
|---|---|---|
| `gen_mmorpg_data.py` | 시뮬레이션 데이터 생성기. 계정마다 하루씩 레벨·경험치·퍼널 진행 상태를 갱신하며 접속, 결제, 이벤트를 만들어 CSV 4개와 라벨 파일(`_answer_key_labels.csv`)로 저장합니다. seed가 고정되어 같은 명령이면 같은 데이터가 나옵니다. | `python data/generator/gen_mmorpg_data.py --seed 42 --out data --answer-out answer_key` |
| `validate_data.py` | 생성된 CSV의 정합성 검사기. 키·형식, 가입 전 활동, 레벨 감소, 퍼널 선행 조건과 순서, 접속하지 않은 날의 이벤트·결제, 점검 시간대 기록 등 40여 개 항목을 확인하고 위반 건수를 출력합니다(위반이 있으면 종료 코드 1). 현재 데이터는 위반 0건입니다. | `python data/generator/validate_data.py data` |

- 필요한 패키지는 `numpy`, `pandas`입니다.
- `gen_mmorpg_data.py`의 `--no-update` 옵션은 8/30 업데이트, 09-08 핫픽스, 복귀 이벤트를 뺀 비교용 데이터를 만듭니다. 분석에는 필요하지 않습니다.
- 분석에는 CSV만 있으면 됩니다. 두 스크립트는 데이터가 어떻게 만들어지고 검증되었는지 보여 주는 용도입니다.

## 라이선스

본 프로젝트는 포트폴리오 목적으로 제작되었으며, 모든 권리는 작성자에게 있습니다. 허락 없는 복제, 배포 및 상업적 이용은 제한됩니다.

---

# Aurelion Online: Live-Service Simulation Data Specification

> Operational logs of a fictional MMORPG, **Aurelion Online**. This is not real service data. I generated it myself with Claude for practicing live-service analytics (KPI reporting, anomaly and abuse detection, hypothesis testing). The generator is `gen_mmorpg_data.py` (seed 42) and the consistency checker is `validate_data.py`.

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
- **Four-step growth funnel**: `tutorial_complete` -> `reach_lv10` -> `first_dungeon` (first dungeon cleared) -> `reach_lv30`. Each step unlocks only after the previous one.
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
| `funnel_events.csv` | 18,504 | One row per growth/guild event |

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
| `event` | VARCHAR | Event name | `tutorial_complete`, `reach_lv10`, `first_dungeon`, `reach_lv30`, `guild_join` |
| `event_time` | DATETIME | When it happened | None during weekly maintenance |

- An (account, event) pair is unique; the same event is never logged twice.
- **Only events that happened inside the window are recorded.** An account that signed up before the window may have passed the tutorial, Lv10 and the first dungeon already, but those rows do not exist. Such accounts only show `guild_join` and `reach_lv30` if they happened inside the window. Funnel conversion should therefore be computed **only for accounts that signed up inside the window (`signup_date >= '2026-07-01'`)**.

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
| `validate_data.py` | Consistency checker for the generated CSVs. It checks about 40 items, including keys and formats, activity before sign-up, level decreases, funnel prerequisites and order, events and payments on days without a login, and records inside the maintenance window, and prints the number of violations (exit code 1 if any). The current data has 0 violations. | `python data/generator/validate_data.py data` |

- Required packages: `numpy`, `pandas`.
- The `--no-update` option of `gen_mmorpg_data.py` creates a comparison dataset without the 08-30 update, the 09-08 hotfix and the comeback event. It is not needed for the analysis.
- The analysis only needs the CSV files. The two scripts show how the data was created and verified.

## License

This project was created for portfolio purposes, and all rights are reserved by the author. Please refrain from copying, distributing, or using it commercially without permission.

