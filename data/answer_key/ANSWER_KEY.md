# 정답지: 심어둔 시나리오와 측정값

> ⚠️ **분석을 마치기 전에는 열어보지 마세요.** 이 문서와 `_answer_key_labels.csv`는 분석을 끝낸 뒤 레포에 추가하고, 분석 결과와 비교해 검증합니다.

효과 크기는 설정값이 아니라 **실제 측정값**입니다. 같은 seed(42)로 업데이트·핫픽스·복귀 이벤트만 뺀 반사실 데이터(`python gen_mmorpg_data.py --seed 42 --no-update`)를 만들어 비교했습니다. 반사실 데이터는 8/30 이전 구간이 실제 데이터와 같습니다. 특별한 언급이 없으면 어뷰저와 장시간 정상 유저를 뺀 일반 유저 기준입니다.

## 라벨 파일 `_answer_key_labels.csv`

| 컬럼 | 설명 |
|---|---|
| `user_id` | 계정 ID |
| `true_segment` | `lapsed`(기간 중 거의 접속하지 않는 기존 유저), `casual`, `core`, `whale`, `bot`, `workshop`, `longplay_human` |
| `abuse_type` | `bot`, `workshop`, 그 외는 빈 값 (`longplay_human`은 정상 유저라 빈 값) |
| `longplay_reason` | `longplay_human`의 사유: `shop`(상점 거래 대기), `idle`(방치), `hardcore`(장시간 플레이) |

계정 수: lapsed 18,500 / casual 8,655 / core 5,265 / whale 1,040 / workshop 240 / bot 180 / longplay_human 120.

## 기준 지표

- 기간 중 접속한 계정 18,401개(전체 34,000개의 54.1%): 기존 12,401 + 신규 6,000. 기존 계정 15,599개는 기간 중 접속 기록이 없음
- 평균 DAU 2,987. 신규 가입 계정이 DAU에서 차지하는 비중 평균 13.4%
- 신규 가입자 리텐션(전체 / 어뷰저 제외): D1 38.8% / 37.3%, D7 16.2% / 14.1%, D30 8.1% / 5.9%
- 결제자 1,525명(활동 계정의 8.3%, 전체의 4.5%), 결제 2,917건, 총 결제액 118,336,900원, 평균 40,568원
- 결제 요일 지수(평균 1.0): 월 0.93, 화 0.89, 수 0.78, 목 0.98, 금 1.09, 토 1.23, 일 1.11
- 기존 유저 DAU 요일 지수: 월 0.97, 화 0.97, 수 0.90, 목 1.02, 금 0.99, 토 1.08, 일 1.07 (수요일 낮음은 05~09시 점검 때문)

## 이벤트 시나리오와 판정

| 시기 | 이벤트 | 판정 | 요약 |
|---|---|---|---|
| 7/21~27 | 여름 축제 1부 | **성공** | 신규 가입 6배, 신규 정착 상승, 기존 유저 DAU·결제 상승 |
| 8/15~21 | 여름 축제 2부 | **부분 성공** | 가입 급증은 같지만 정착 효과와 기존 유저 반응이 1부보다 약함 |
| 8/30 | 성장 개편 업데이트 | **실패** | 경험치 −20%로 성장이 느려져 DAU 하락, 신규는 초반 이탈. 핵심·고래는 강화 패키지로 결제 상승 |
| 9/8 | 핫픽스 | **부분 성공** | 하락은 멈추고 접속이 회복되지만 이탈한 유저는 돌아오지 않고, 신규 리텐션은 일부만 회복 |
| 9/9~15 | 복귀 지원 이벤트 | **단기 성공** | 이탈 유저가 일주일간 돌아와 DAU가 오르지만 지속되지 않음. 신규 리텐션에는 영향 없음 |

### 1. 신규 가입 코호트 리텐션 (주 코호트, 어뷰저 제외, %)

| 가입 주 | 인원 | D1 | D3 | D7 | D14 | D30 |
|---|---|---|---|---|---|---|
| 06-29 | 268 | 38.1 | 22.0 | 14.6 | 10.4 | 6.7 |
| 07-06 | 326 | 38.3 | 23.0 | 13.8 | 9.2 | 5.8 |
| 07-13 | 360 | 35.8 | 22.2 | 12.8 | 8.6 | 5.0 |
| **07-20 (축제 1부)** | 1,024 | **39.7** | **28.7** | **18.5** | **11.0** | **7.5** |
| 07-27 | 345 | 37.7 | 24.1 | 14.5 | 8.7 | 4.3 |
| 08-03 | 359 | 36.2 | 22.6 | 13.4 | 9.2 | 4.7 |
| 08-10 (축제 2부 2일) | 745 | 39.6 | 24.8 | 15.6 | 9.1 | 5.2 |
| 08-17 (축제 2부 5일) | 644 | 38.2 | 27.0 | 15.1 | 8.9 | 5.9 |
| 08-24 | 357 | 35.6 | 21.3 | 10.6 | 7.3 | - |
| **08-31 (업데이트)** | 340 | **30.6** | **16.5** | **9.1** | **5.3** | - |
| 09-07 | 344 | 35.8 | 19.5 | 10.5 | 7.3 | - |
| 09-14 (핫픽스 이후) | 333 | 35.4 | 19.8 | 10.2 | - | - |

가입 시기로 묶어 비교하면 다음과 같습니다(어뷰저 제외).

| 구분 | 인원 | D1 | D3 | D7 | D14 | D30 |
|---|---|---|---|---|---|---|
| 평소 (7/1~19) | 944 | 36.8 | 21.9 | 13.1 | 8.9 | 5.3 |
| 축제 1부 (7/21~27) | 1,039 | 39.1 | 28.7 | 18.4 | 10.9 | 7.4 |
| 축제 2부 (8/15~21) | 1,027 | 39.4 | 27.3 | 16.3 | 9.3 | 5.6 |
| 업데이트 (8/30~9/7) 실제 / 반사실 | 437 | 30.4 / 37.3 | 16.5 / 22.2 | 8.7 / 13.3 | 5.5 / 8.5 | - |
| 핫픽스 이후 (9/8~21) 실제 / 반사실 | 676 | 35.1 / 37.3 | 19.1 / 22.3 | 9.8 / 13.2 | 7.5 / 8.7 | - |

- **축제 1부 효과는 D60까지 이어집니다.** D45 5.6% vs 평소 3.1~4.1%, D60 5.0% vs 평소 2.8~3.4% (7/20 주 코호트 vs 6/29~7/13 주 코호트). 평소 코호트는 D30의 약 70%가 D45에, 약 55%가 D60에 남습니다.
- **D30 이후는 관측 한계가 있습니다.** D60까지 볼 수 있는 코호트는 7/30 이전 가입자(주 코호트 4개)뿐이고, 업데이트 이후 가입한 코호트는 D30도 볼 수 없습니다.
- **측정일의 달력 효과**: 8/22~8/29 가입자(업데이트 직전)는 D7 날짜가 업데이트 구간(8/29~9/5)에 걸려 D7이 10.9%로 반사실(13.6%)보다 낮습니다. D-n 리텐션은 가입일만이 아니라 측정일의 이벤트에도 영향을 받습니다.
- 가입 시기에 따른 구성(캐주얼/코어/고래) 차이는 없습니다. 차이는 시나리오의 효과에서만 옵니다.
- 신규 가입 접속은 가입일 코호트별 층화 추출로 만들어 코호트 곡선이 부드럽습니다. 실제 서비스 데이터는 이보다 노이즈가 큽니다.

### 2. 8/30 업데이트의 영향 (실제 vs 반사실, 기간별 합계 비율)

설계 이야기: 필드 경험치 20% 하향으로 성장이 느려져 라이트 유저가 불만을 느끼고 접속·플레이 시간이 줄었습니다. 핵심 유저·고래는 강화 패키지와 신규 지역으로 영향이 작거나 오히려 결제가 늘었습니다. 모바일은 대용량 패치 때문에 초반 3일 접속이 더 줄었습니다. 09-08 핫픽스로 경험치 하향이 20% → 10%로 완화되고, 09-09~15 복귀 이벤트가 이어지며 DAU가 일시적으로 반등했습니다.

| 지표 | 업데이트 (8/30~9/7) | 핫픽스 주 (9/8~9/15) | 이후 (9/16~9/28) |
|---|---|---|---|
| 일반 유저 DAU | 0.896 | 1.137 | 0.994 |
| 　캐주얼 | 0.783 | 1.166 | 0.897 |
| 　코어 | 0.907 | 1.090 | 1.019 |
| 　고래 | 1.004 | 1.061 | 1.032 |
| 　모바일 / PC | 0.891 / 0.899 | 1.137 / 1.137 | 0.984 / 1.000 |
| 　(8/30~9/1만) 모바일 / PC | 0.825 / 0.902 | | |
| 　신규 가입자 / 기존 유저 | 0.872 / 0.901 | 0.903 / 1.179 | 0.898 / 1.011 |
| 어뷰저 DAU | 0.996 | 1.008 | 1.005 |
| 평균 플레이 시간 (실제 vs 반사실, 분) | 131 vs 144 | 137 vs 142 | 146 vs 143 |
| 총 결제액 | 1.337 | 1.292 | 1.133 |

- 결제액은 업데이트 구간에 고래 1.38배, 코어 1.04배로 늘고 캐주얼은 0.81배로 줄었습니다. DAU가 줄어도 매출이 오른 구간이 있으므로 DAU와 매출을 따로 봐야 합니다.
- **영구 이탈**: 8/2~8/29에 접속한 기존 일반 유저 중 9/16 이후 한 번도 접속하지 않은 비율은 31.0%(반사실 27.5%, +3.5%p)입니다. 핫픽스로 DAU가 올라와도 이미 나간 유저는 돌아오지 않습니다.
- **복귀 이벤트**: 기간 중 거의 접속하지 않던 기존 유저(lapsed)의 일 접속자가 평소 12~26명에서 9/9~15에 111~135명으로 오르고 9/16부터 다시 17~26명이 됩니다. 이 반등이 "9/8 이후 원복"처럼 보이게 합니다. 복귀 이벤트는 신규 가입자 리텐션에는 영향이 없습니다.
- 8/2~8/29 같은 요일 평균과 비교한 기존 일반 유저 DAU는 업데이트 구간 0.855, 핫픽스 주 1.103, 이후 0.939입니다. 이후 구간의 0.939에는 업데이트 효과 외에 자연 이탈(약 −6%)이 섞여 있어, 반사실 없이 단순 전후 비교를 하면 업데이트 영향을 과대평가합니다.
- **신규 가입자 성장**: 튜토리얼 완료자 중 Lv10 도달률이 업데이트 구간(8/30~9/7 가입)에 54.5%(반사실 77.7%), 핫픽스 후 9/8~9/21 가입은 64.3%(반사실 72.6%)로 낮아졌습니다(8/2~8/29 가입은 83.8%, 반사실 86.8%).

### 3. 여름 축제 프로모션 (기존 유저 DAU·결제는 평소 같은 요일 평균 대비)

- 가입 급증: 07-21 321명, 08-15 312명으로 평소 중앙값(하루 52명)의 약 6배. 5일 안에 평소 수준으로 돌아옴
- 기존 일반 유저 DAU: 1부 +27%, 2부 +16%
- 결제액: 1부 +111%, 2부 +84%
- 신규 가입자 정착: 1절 표의 축제 1부, 2부 코호트 참조(1부 > 2부)

### 4. 성장 퍼널 병목 (신규 가입 계정 6,000명 기준)

| 단계 | 인원 | 직전 단계 대비 | 가입자 전체 대비 |
|---|---|---|---|
| tutorial_complete | 5,590 | 93.2% | 93.2% |
| reach_lv10 | 4,455 | 79.7% | 74.2% |
| first_dungeon | 1,897 | **42.6%** | 31.6% |
| reach_lv30 | 1,220 | 64.3% | 20.3% |

- 병목은 `reach_lv10` → `first_dungeon`입니다. 첫 던전을 클리어하기 전에는 Lv10에서 성장이 멈추기 때문에 던전에 도전하지 않거나 막힌 유저는 정체됩니다. 정체 구간에서 이탈도 일어납니다.
- 가입 후 30일 이상 관측된 계정(4,502명)만 보면 93%, 87%, **43%**, 69%로 병목은 그대로이고 뒤 단계 전환율이 올라갑니다(우측 절단의 영향).
- 던전 클리어율(Lv10 도달자 대비)은 평소 40.6%, 축제 1부 41.9%, 2부 40.1%, 업데이트 구간 39.2%로 이벤트와 무관합니다. 이벤트의 영향은 Lv10 도달률에서 나타납니다(축제 1부 91.6%, 2부 85.7%, 평소 89.4%, 업데이트 53.1%, 튜토리얼 완료자 기준).
- 길드 가입은 선택이며 신규 계정 1,258명이 가입했습니다. 길드 가입과 Lv30 도달은 서로 필수 조건이 아닙니다.

### 5. 이상 계정

| 유형 | 인원 | 특징 |
|---|---|---|
| `bot` | 180 (기존 110 + 신규 70) | 접속한 날은 거의 매일, 하루 약 19~20시간 플레이. 일 골드 획득량의 변동계수(CV) 평균 0.13(최대 0.25). 결제 없음 |
| `workshop` (골드 작업장) | 240 (기존 150 + 신규 90) | 12개 공용 기기에 11~28계정씩 묶여 있음. 일 평균 골드 약 12.0만(코어 2.7만, 고래 4.9만, 봇 4.7만). 플레이 시간은 최대 620분(10.3시간)이라 18시간 기준에 안 걸림. 결제 없음 |
| `longplay_human` (정상 장시간 유저) | 120 (기존 75 + 신규 45) | 18시간 이상 접속한 날이 반드시 하루 이상 있는 정상 유저. 사유 `shop` 48 / `idle` 41 / `hardcore` 31. 18시간 이상 날의 골드 CV 평균 0.45 (봇보다 큼). 결제 가능 |

- 일반 유저(casual/core/whale/lapsed)의 최대 플레이 시간은 508분(8.5시간)입니다.
- 하루 18시간(1,080분) 이상 플레이한 계정은 300개이며 봇 180개와 정상 유저 120개입니다. 이 기준만 쓰면 정밀도는 60%입니다.
- 연속 N일 이상 18시간 이상 기준: N=2 → 268개(봇 180 / 정상 88), N=3 → 243(179 / 64), N=5 → 214(179 / 35), N=7 → 203(179 / 24). N=7에서 정밀도 88%, 봇 재현율 99%입니다.
- 작업장은 플레이 시간이 아니라 **골드 획득량 + 기기 공유**로 찾아야 합니다. 일반 유저의 기기 공유는 최대 10계정(PC방 유형)이고 작업장은 최소 11계정이라 기기당 계정 수 11 이상이면 작업장 240개가 모두 걸립니다. 일반 유저 669개가 기기를 공유하는 점이 오탐 연습 요소입니다.
- 어뷰저(봇 + 작업장 420개)는 기간 중 접속 계정의 2.3%지만 DAU의 평균 11.0%(최대 14.2%)를 차지합니다. DAU, 리텐션, 골드 지표를 볼 때 어뷰저를 제외하지 않으면 왜곡됩니다.
- 봇·작업장의 신규 가입 계정은 가입 직후부터 높은 접속 빈도를 유지해 신규 유저 리텐션(D7, D30)을 부풀립니다. 전체 D30 8.1% vs 어뷰저 제외 5.9%.

## 한계

- 봇·작업장·장시간 정상 유저의 행동은 제가 정한 분포(접속 빈도, 변동계수, 기기 공유)에서 나온 것이며 실제 어뷰저를 그대로 재현한 것이 아닙니다.
- 효과 크기는 이 seed에서의 측정값이라 seed가 바뀌면 조금씩 달라집니다. 방향은 같습니다.
- 반사실 비교는 업데이트·핫픽스·복귀 이벤트를 모두 뺀 한 가지 시나리오입니다. 개별 요소(예: 핫픽스만)의 효과는 분리해 측정하지 않았습니다.
- 신규 가입자의 접속은 코호트별 층화 추출로 만들어 코호트 리텐션이 실제 서비스보다 부드럽습니다.

---

# Answer Key: Planted Scenario and Measured Values

> ⚠️ **Do not open this before finishing the analysis.** Add this document and `_answer_key_labels.csv` to the repository only after the analysis is done, and use them to check your findings.

Effect sizes are **measured values, not configured values**. With the same seed (42), I generated a counterfactual dataset without the update, the hotfix and the comeback event (`python gen_mmorpg_data.py --seed 42 --no-update`) and compared it with the real data. The counterfactual is identical to the real data before 8/30. Unless stated otherwise, figures refer to ordinary players (abusers and long-session normal players excluded).

## Label file `_answer_key_labels.csv`

| Column | Description |
|---|---|
| `user_id` | Account ID |
| `true_segment` | `lapsed` (existing players who rarely log in during the window), `casual`, `core`, `whale`, `bot`, `workshop`, `longplay_human` |
| `abuse_type` | `bot`, `workshop`, otherwise empty (`longplay_human` are normal players, so empty) |
| `longplay_reason` | Reason for `longplay_human`: `shop` (waiting on shop trades), `idle` (left running), `hardcore` (long sessions) |

Account counts: lapsed 18,500 / casual 8,655 / core 5,265 / whale 1,040 / workshop 240 / bot 180 / longplay_human 120.

## Reference metrics

- 18,401 accounts were active in the window (54.1% of 34,000): 12,401 existing + 6,000 new. 15,599 existing accounts have no activity in the window
- Mean DAU 2,987. New accounts make up 13.4% of DAU on average
- New-signup retention (all / excluding abusers): D1 38.8% / 37.3%, D7 16.2% / 14.1%, D30 8.1% / 5.9%
- 1,525 payers (8.3% of active accounts, 4.5% of all), 2,917 purchases, total revenue KRW 118,336,900, average purchase KRW 40,568
- Payment weekday index (mean 1.0): Mon 0.93, Tue 0.89, Wed 0.78, Thu 0.98, Fri 1.09, Sat 1.23, Sun 1.11
- Existing-player DAU weekday index: Mon 0.97, Tue 0.97, Wed 0.90, Thu 1.02, Fri 0.99, Sat 1.08, Sun 1.07 (Wednesday is low because of the 05-09h maintenance)

## Event scenario and verdicts

| When | Event | Verdict | Summary |
|---|---|---|---|
| 7/21-27 | Summer Festival part 1 | **Hit** | Sign-ups 6x, new players stay longer, existing players' DAU and revenue rise |
| 8/15-21 | Summer Festival part 2 | **Partial hit** | Same sign-up surge, but weaker retention gain and weaker reaction from existing players |
| 8/30 | Growth overhaul update | **Flop** | XP -20% slows growth, so DAU falls and new players leave early. Core players and whales spend more on enhancement packs |
| 9/8 | Hotfix | **Partial hit** | The decline stops and logins recover, but players who left do not return and new-player retention recovers only partly |
| 9/9-15 | Comeback support event | **Short-lived hit** | Lapsed players return for a week and DAU rises, but it does not last. No effect on new-player retention |

### 1. New-signup cohort retention (weekly cohorts, abusers excluded, %)

| Sign-up week | Size | D1 | D3 | D7 | D14 | D30 |
|---|---|---|---|---|---|---|
| 06-29 | 268 | 38.1 | 22.0 | 14.6 | 10.4 | 6.7 |
| 07-06 | 326 | 38.3 | 23.0 | 13.8 | 9.2 | 5.8 |
| 07-13 | 360 | 35.8 | 22.2 | 12.8 | 8.6 | 5.0 |
| **07-20 (festival 1)** | 1,024 | **39.7** | **28.7** | **18.5** | **11.0** | **7.5** |
| 07-27 | 345 | 37.7 | 24.1 | 14.5 | 8.7 | 4.3 |
| 08-03 | 359 | 36.2 | 22.6 | 13.4 | 9.2 | 4.7 |
| 08-10 (festival 2, 2 days) | 745 | 39.6 | 24.8 | 15.6 | 9.1 | 5.2 |
| 08-17 (festival 2, 5 days) | 644 | 38.2 | 27.0 | 15.1 | 8.9 | 5.9 |
| 08-24 | 357 | 35.6 | 21.3 | 10.6 | 7.3 | - |
| **08-31 (update)** | 340 | **30.6** | **16.5** | **9.1** | **5.3** | - |
| 09-07 | 344 | 35.8 | 19.5 | 10.5 | 7.3 | - |
| 09-14 (after hotfix) | 333 | 35.4 | 19.8 | 10.2 | - | - |

Grouped by sign-up period (abusers excluded):

| Group | Size | D1 | D3 | D7 | D14 | D30 |
|---|---|---|---|---|---|---|
| Usual (7/1-19) | 944 | 36.8 | 21.9 | 13.1 | 8.9 | 5.3 |
| Festival 1 (7/21-27) | 1,039 | 39.1 | 28.7 | 18.4 | 10.9 | 7.4 |
| Festival 2 (8/15-21) | 1,027 | 39.4 | 27.3 | 16.3 | 9.3 | 5.6 |
| Update (8/30-9/7), actual / counterfactual | 437 | 30.4 / 37.3 | 16.5 / 22.2 | 8.7 / 13.3 | 5.5 / 8.5 | - |
| After hotfix (9/8-21), actual / counterfactual | 676 | 35.1 / 37.3 | 19.1 / 22.3 | 9.8 / 13.2 | 7.5 / 8.7 | - |

- **The festival 1 effect lasts to D60.** D45 5.6% vs 3.1-4.1% usual, D60 5.0% vs 2.8-3.4% (week of 7/20 vs weeks of 6/29-7/13). Usual cohorts keep about 70% of their D30 players at D45 and about 55% at D60.
- **Observation limits beyond D30.** Only sign-ups before 7/30 (4 weekly cohorts) can be followed to D60, and cohorts that signed up after the update cannot be followed to D30.
- **Calendar effect of the measurement day.** Players who signed up 8/22-8/29 (just before the update) have their D7 fall inside the update period (8/29-9/5), so their D7 is 10.9% against 13.6% in the counterfactual. D-n retention depends not only on the sign-up date but on events on the measurement day.
- The class mix (casual/core/whale) does not differ by sign-up period; differences come only from the scenario effects.
- New-player logins were generated with stratified sampling inside each sign-up-day cohort, so the cohort curves are smooth. Real service data is noisier.

### 2. Impact of the 8/30 update (real vs counterfactual, ratio of period totals)

The story: the 20% field-XP cut slowed growth, so light players grew dissatisfied and logged in and played less. Core players and whales were barely affected, or even spent more, thanks to enhancement packs and the new region. Mobile logins fell further in the first 3 days because of the large patch. The 09-08 hotfix eased the cut from 20% to 10%, and the 09-09 to 09-15 comeback event pushed DAU up temporarily.

| Metric | Update (8/30-9/7) | Hotfix week (9/8-9/15) | After (9/16-9/28) |
|---|---|---|---|
| Ordinary-player DAU | 0.896 | 1.137 | 0.994 |
| - casual | 0.783 | 1.166 | 0.897 |
| - core | 0.907 | 1.090 | 1.019 |
| - whale | 1.004 | 1.061 | 1.032 |
| - mobile / PC | 0.891 / 0.899 | 1.137 / 1.137 | 0.984 / 1.000 |
| - (8/30-9/1 only) mobile / PC | 0.825 / 0.902 | | |
| - new sign-ups / existing players | 0.872 / 0.901 | 0.903 / 1.179 | 0.898 / 1.011 |
| Abuser DAU | 0.996 | 1.008 | 1.005 |
| Mean playtime (real vs counterfactual, min) | 131 vs 144 | 137 vs 142 | 146 vs 143 |
| Total revenue | 1.337 | 1.292 | 1.133 |

- During the update, revenue was 1.38x for whales and 1.04x for core players, and 0.81x for casual players. DAU fell while revenue rose in some periods, so DAU and revenue need to be read separately.
- **Permanent churn**: of existing ordinary players seen in 8/2-8/29, 31.0% were never seen again from 9/16 (counterfactual 27.5%, +3.5 points). Even when DAU recovers after the hotfix, players who already left do not come back.
- **Comeback event**: daily active lapsed players go from 12-26 to 111-135 during 9/9-9/15 and back to 17-26 from 9/16. This rebound makes it look like "back to normal after 9/8". The event has no effect on new-player retention.
- Compared with the same-weekday average of 8/2-8/29 (not with the counterfactual), existing ordinary-player DAU is 0.855 in the update period, 1.103 in the hotfix week and 0.939 afterwards. The 0.939 includes natural attrition (about -6%) on top of the update effect, so a plain before/after comparison overstates the update's impact.
- **New-player growth**: among tutorial completers, the Lv10 rate is 54.5% for sign-ups during the update (counterfactual 77.7%) and 64.3% for 9/8-9/21 sign-ups (counterfactual 72.6%), versus 83.8% for 8/2-8/29 sign-ups (counterfactual 86.8%).

### 3. Summer Festival promotions (existing players' DAU and revenue vs the same-weekday average of non-event days)

- Sign-up spikes: 321 on 07-21 and 312 on 08-15, about 6x the usual median of 52 per day; back to normal within about 5 days
- Existing ordinary-player DAU: +27% in part 1, +16% in part 2
- Revenue: +111% in part 1, +84% in part 2
- New-player retention: see the cohort tables in section 1 (part 1 > part 2)

### 4. Growth-funnel bottleneck (6,000 accounts that signed up in the window)

| Step | Accounts | vs previous step | vs all sign-ups |
|---|---|---|---|
| tutorial_complete | 5,590 | 93.2% | 93.2% |
| reach_lv10 | 4,455 | 79.7% | 74.2% |
| first_dungeon | 1,897 | **42.6%** | 31.6% |
| reach_lv30 | 1,220 | 64.3% | 20.3% |

- The bottleneck is `reach_lv10` -> `first_dungeon`. Leveling stops at Lv10 until the first dungeon is cleared, so players who skip or get stuck on the dungeon stall, and some leave while stalled.
- For accounts observed for 30+ days (4,502 accounts) the steps are 93%, 87%, **43%** and 69%: the bottleneck stays and the later steps rise (right-censoring).
- The dungeon clear rate (among players who reached Lv10) is 40.6% usual, 41.9% festival 1, 40.1% festival 2 and 39.2% update period, independent of events. Events show up in the Lv10 rate (festival 1 91.6%, festival 2 85.7%, usual 89.4%, update 53.1%, among tutorial completers).
- Guild membership is optional; 1,258 new accounts joined a guild. Neither guild membership nor Lv30 is a prerequisite of the other.

### 5. Abnormal accounts

| Type | Count | Characteristics |
|---|---|---|
| `bot` | 180 (110 existing + 70 new) | Log in almost every day, play about 19-20 hours a day. Coefficient of variation (CV) of daily gold averages 0.13 (max 0.25). No purchases |
| `workshop` (gold farming) | 240 (150 existing + 90 new) | Grouped on 12 shared devices with 11-28 accounts each. About 120k gold per day on average (core 27k, whale 49k, bot 47k). Max playtime is 620 min (10.3 h), so an 18-hour rule does not catch them. No purchases |
| `longplay_human` (normal long-session players) | 120 (75 existing + 45 new) | Normal players who always have at least one day with 18+ hours. Reasons: `shop` 48 / `idle` 41 / `hardcore` 31. Mean gold CV on 18+ hour days is 0.45 (higher than bots). May make purchases |

- Ordinary players (casual/core/whale/lapsed) have a maximum playtime of 508 min (8.5 h).
- 300 accounts played 18 hours (1,080 min) or more in a day: 180 bots and 120 normal players. The 18-hour rule alone gives a precision of 60%.
- Rule "N or more consecutive days with 18+ hours": N=2 -> 268 accounts (180 bots / 88 normal), N=3 -> 243 (179 / 64), N=5 -> 214 (179 / 35), N=7 -> 203 (179 / 24). At N=7 precision is 88% and bot recall is 99%.
- Workshop accounts must be found by **gold gained + shared devices**, not playtime. Ordinary shared devices hold at most 10 accounts (internet-cafe type) while workshop devices hold at least 11, so "11 or more accounts per device" catches all 240 workshop accounts. The 669 ordinary accounts that share devices are the false-positive exercise.
- Abusers (bots + workshop, 420 accounts) are 2.3% of active accounts but make up on average 11.0% of DAU (max 14.2%). Leaving them in distorts DAU, retention and gold metrics.
- New-signup bots and workshop accounts keep a high login rate from day one, which inflates new-player retention (D30: 8.1% with them vs 5.9% without).

## Limitations

- The behavior of bots, workshops and long-session normal players comes from distributions I chose (login frequency, CV, device sharing) and does not reproduce real abusers.
- Effect sizes are measurements for this seed and shift slightly with other seeds; the direction stays the same.
- The counterfactual removes the update, the hotfix and the comeback event together. The effect of a single component (for example the hotfix alone) was not isolated.
- New players' logins were generated with stratified sampling per sign-up-day cohort, so cohort retention is smoother than in real service data.
