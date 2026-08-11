# Recommended SQL Views and CTE Templates for LLM SQL Agent

## Purpose

현재 LLM SQL agent는 전체 DB 스키마를 보고 직접 SQL을 생성한다. 이 방식은 유연하지만, 모델이 매번 같은 조인 경로와 metric 정의를 다시 추론해야 하므로 다음 오류가 반복될 수 있다.

- `fighter`, `fighter_match`, `match`, `event`, `weight_class` 조인 누락 또는 중복
- 예정 경기와 완료 경기 혼합
- 승률, 피니시율, KO/TKO 승리 같은 metric denominator 오류
- `ranking = 0` 챔피언 규칙 누락
- 라운드별 통계를 fighter-side 집계로 잘못 합산
- Tapology 커리어 기록과 UFCStats 경기 기록의 scope 혼동

아래 view와 CTE 템플릿은 모든 질문을 미리 예측하기 위한 것이 아니다. 모델이 자주 헷갈리는 기본 fact path와 metric 정의를 고정해서 SQL 생성 정확도를 높이기 위한 추천 목록이다.

## Design Principles

- View는 "모델이 자주 써야 하는 검증된 조인 경로"에 이름을 붙이는 용도다.
- 원본 테이블은 계속 프롬프트에 제공하되, Query Map에서는 view를 우선 사용하도록 안내한다.
- 집계 view는 denominator와 scope가 명확한 metric만 포함한다.
- Tapology 기반 커리어 기록과 UFCStats 기반 경기 기록은 view 이름과 컬럼명에서 scope를 분명히 나눈다.
- 처음부터 모든 view를 만들지 말고, Priority 1부터 평가셋으로 효과를 확인하며 추가한다.

## Priority 1 Views

### 1. `v_fighter_fight_results`

**Purpose:** 선수 한 명의 bout-side 결과를 event/match/weight class 정보와 함께 한 줄로 제공하는 핵심 fact view.

**Source tables:**
- `fighter`
- `fighter_match`
- `match`
- `event`
- `weight_class`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `nickname`
- `match_id`
- `event_id`
- `event_name`
- `event_date`
- `event_location`
- `weight_class_id`
- `weight_class_name`
- `result`
- `method`
- `result_round`
- `time`
- `is_main_event`
- `is_title_bout`
- `bout_status`
- `cancellation_reason`
- `fight_order`

**Questions it supports:**
- "이슬람 마카체프 최근 경기"
- "존 존스 타이틀전 전적"
- "라이트급 2024년 경기 결과"
- "KO로 끝난 경기 Top N"

**LLM errors it reduces:**
- `fighter_match -> match -> event` 조인 누락
- 체급이 `match.weight_class_id`에 있다는 사실 누락
- 최근 경기에서 `event_date` 정렬 누락
- Tapology bout status와 UFCStats result/method 혼동

### 2. `v_completed_fighter_fights`

**Purpose:** 완료된 경기만 포함하는 안전한 subset. "최근", "마지막", "전적", "승률" 질문의 기본 view로 사용한다.

**Source view:**
- `v_fighter_fight_results`

**Recommended filter policy:**
- `event_date <= CURRENT_DATE`
- `result IS NOT NULL`
- 필요 시 `bout_status IS NULL OR bout_status IN ('completed', 'unknown')`

**Recommended columns:**
- `v_fighter_fight_results`의 주요 컬럼 전체
- `is_win`
- `is_loss`
- `is_draw`
- `is_no_contest`
- `is_ko_tko`
- `is_submission`
- `is_decision`
- `is_finish`

**Questions it supports:**
- "최근 5경기"
- "UFC 전적"
- "KO/TKO 승리 수"
- "서브미션 승률"

**LLM errors it reduces:**
- 예정 경기 포함
- `method`가 비어 있는 최근 미수집 경기까지 완료 경기로 계산
- `result='win'`과 method category 조건 조합 누락

### 3. `v_current_rankings`

**Purpose:** 현재 랭킹과 챔피언 조회를 단순화한다.

**Source tables:**
- `ranking`
- `fighter`
- `weight_class`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `weight_class_id`
- `weight_class_name`
- `ranking`
- `is_champion`

**Derived fields:**
- `is_champion = ranking = 0`
- `display_rank = CASE WHEN ranking = 0 THEN 'champion' ELSE ranking::text END`

**Questions it supports:**
- "라이트급 챔피언 누구야?"
- "페더급 랭킹 Top 10"
- "체급별 챔피언 목록"

**LLM errors it reduces:**
- `ranking = 0` 챔피언 규칙 누락
- `ranking`과 `weight_class` 조인 누락
- 챔피언을 `fighter.belt`만으로 판단하는 오류

### 4. `v_fighter_record_summary`

**Purpose:** 선수별 완료 경기 기준 record와 승률을 제공한다.

**Source view:**
- `v_completed_fighter_fights`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `total_completed_fights`
- `wins`
- `losses`
- `draws`
- `no_contests`
- `win_rate_including_draw_nc`
- `win_rate_excluding_draw_nc`
- `last_fight_date`
- `first_fight_date`

**Metric policy to define explicitly:**
- Product default 승률을 하나 선택해야 한다.
- 추천 default: `wins / NULLIF(wins + losses, 0)` for clean win/loss rate.
- 별도 컬럼으로 draw/nc 포함 승률도 제공하면 질문 의도에 맞게 선택 가능하다.

**Questions it supports:**
- "맥그리거 승률"
- "승률 Top 10"
- "가장 많이 싸운 선수"
- "최근 활동 선수 중 승률 높은 선수"

**LLM errors it reduces:**
- 승률 denominator 불일치
- draw/no contest 처리 임의 추론
- `fighter.wins/losses`와 UFC fight-side results scope 혼동

## Priority 2 Views

### 5. `v_fighter_method_summary`

**Purpose:** 선수별 승리/패배 방식 집계를 제공한다.

**Source view:**
- `v_completed_fighter_fights`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `ko_tko_wins`
- `submission_wins`
- `decision_wins`
- `dq_wins`
- `other_wins`
- `ko_tko_losses`
- `submission_losses`
- `decision_losses`
- `finish_wins`
- `finish_losses`
- `finish_win_rate_over_wins`
- `finish_win_rate_over_total_fights`

**Method classification policy:**
- `method ILIKE 'KO-%' OR method ILIKE 'TKO-%'` -> KO/TKO
- `method ILIKE 'SUB-%'` -> submission
- `method IN ('U-DEC', 'S-DEC', 'M-DEC') OR method ILIKE '%DEC%'` -> decision

**Questions it supports:**
- "KO 승리 많은 선수"
- "서브미션 승률 Top 5"
- "피니시율 높은 라이트급 선수"

**LLM errors it reduces:**
- decision을 `result='win'` 없이 participation으로 세는 오류와, decision wins 질문을 participation으로 세는 반대 오류
- KO/TKO/SUB method pattern 누락
- finish rate denominator 불일치

### 6. `v_fighter_stat_totals`

**Purpose:** fighter-side 라운드 통계를 선수별로 집계한다.

**Source tables/views:**
- `fighter`
- `fighter_match`
- `match_statistics`
- optional: `v_completed_fighter_fights`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `stat_rounds`
- `knockdowns`
- `sig_str_landed`
- `sig_str_attempted`
- `sig_str_accuracy`
- `total_str_landed`
- `total_str_attempted`
- `total_str_accuracy`
- `td_landed`
- `td_attempted`
- `td_accuracy`
- `submission_attempts`
- `control_time_seconds`

**Questions it supports:**
- "테이크다운 성공률 높은 선수"
- "유효타 정확도 비교"
- "그래플링 지표 좋은 라이트급 선수"

**LLM errors it reduces:**
- 라운드별 row를 fight row처럼 세는 오류
- `td_landed / td_attempted` denominator 누락
- fighter-side stats를 match-level stats로 오해

### 7. `v_fighter_strike_profile`

**Purpose:** 타격 타깃/포지션별 집계와 정확도를 제공한다.

**Source tables:**
- `fighter`
- `fighter_match`
- `strike_detail`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `head_strikes_landed`
- `head_strikes_attempts`
- `head_strike_accuracy`
- `body_strikes_landed`
- `body_strikes_attempts`
- `body_strike_accuracy`
- `leg_strikes_landed`
- `leg_strikes_attempts`
- `leg_strike_accuracy`
- `clinch_strikes_landed`
- `clinch_strikes_attempts`
- `ground_strikes_landed`
- `ground_strikes_attempts`
- `strike_detail_rounds`

**Questions it supports:**
- "헤드 스트라이크 비중 높은 선수"
- "맥그리거 타격 부위 분석"
- "클린치 타격 많은 선수"

**LLM errors it reduces:**
- target별 landed/attempts 컬럼명 혼동
- 1행 다중 숫자 시각화에 필요한 stable column 제공

### 8. `v_fighter_profile_enriched`

**Purpose:** UFCStats fighter profile과 Tapology profile enrichment를 함께 제공한다.

**Source table:**
- `fighter`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `nickname`
- `height_cm`
- `weight_kg`
- `reach_cm`
- `stance`
- `birthdate`
- `nationality`
- `belt`
- `tapology_url`
- `born`
- `fighting_out_of`
- `affiliation`
- `gym`
- `current_streak`
- `last_fight_name`
- `last_fight_date`
- `last_fight_promotion`
- `tapology_last_scraped_at`

**Questions it supports:**
- "선수 프로필"
- "어느 팀 소속이야?"
- "국적/스탠스/리치 알려줘"

**LLM errors it reduces:**
- profile 질문에서 fight result 테이블을 불필요하게 조인
- UFCStats/Tapology profile field scope 혼동

## Priority 3 Views

### 9. `v_fighter_career_promotion_summary`

**Purpose:** Tapology promotion-level career record를 fighter profile과 함께 제공한다.

**Source tables:**
- `fighter`
- `fighter_promotion_record`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `promotion_name`
- `wins`
- `losses`
- `draws`
- `no_contests`
- `total_bouts`
- `promotion_win_rate`

**Questions it supports:**
- "UFC 외 커리어"
- "Bellator 전적"
- "프로모션별 기록"

**LLM errors it reduces:**
- Tapology career record를 UFCStats completed fight record와 섞는 오류
- promotion scope 누락

### 10. `v_fighter_career_method_summary`

**Purpose:** Tapology method-level all-career record를 fighter profile과 함께 제공한다.

**Source tables:**
- `fighter`
- `fighter_method_record`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `scope`
- `result`
- `method_category`
- `count`

**Optional pivoted columns:**
- `career_ko_tko_wins`
- `career_submission_wins`
- `career_decision_wins`
- `career_ko_tko_losses`
- `career_submission_losses`
- `career_decision_losses`

**Questions it supports:**
- "전체 커리어 기준 피니시 성향"
- "UFC 밖 기록 포함하면?"
- "커리어 서브미션 승리"

**LLM errors it reduces:**
- all-career Tapology scope와 UFC-only scope 혼동
- `result`, `method_category` 조합 누락

### 11. `v_event_fight_card`

**Purpose:** 이벤트별 fight card 조회를 단순화한다.

**Source tables:**
- `event`
- `match`
- `fighter_match`
- `fighter`
- `weight_class`

**Recommended columns:**
- `event_id`
- `event_name`
- `event_date`
- `event_location`
- `match_id`
- `fight_order`
- `is_main_event`
- `is_title_bout`
- `weight_class_name`
- `fighter_1_id`
- `fighter_1_name`
- `fighter_2_id`
- `fighter_2_name`
- `bout_status`
- `method`
- `result_round`
- `time`

**Questions it supports:**
- "이번 주 UFC 대진"
- "UFC 300 메인카드"
- "다가오는 이벤트 타이틀전"

**LLM errors it reduces:**
- bout 하나에 fighter_match 두 row가 있다는 구조를 잘못 펼치는 오류
- card order/main event 해석 오류

### 12. `v_title_fights`

**Purpose:** 타이틀전 질문을 단순화한다.

**Source view:**
- `v_fighter_fight_results`

**Recommended filter:**
- `is_title_bout = true`

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `match_id`
- `event_name`
- `event_date`
- `weight_class_name`
- `result`
- `method`
- `result_round`
- `opponent_name` if practical

**Questions it supports:**
- "타이틀전 전적"
- "라이트급 타이틀전 결과"
- "타이틀전 KO 승리"

**LLM errors it reduces:**
- title bout filter 누락
- champion ranking과 title bout을 혼동

## Optional Helper Views

### `v_fighter_opponents`

**Purpose:** 상대 선수 이름을 포함한 completed fight view.

**Why optional:** 구현이 약간 더 까다롭다. `fighter_match` self join으로 같은 `match_id`의 다른 fighter를 찾아야 한다.

**Recommended columns:**
- `fighter_id`
- `fighter_name`
- `opponent_id`
- `opponent_name`
- `match_id`
- `event_name`
- `event_date`
- `result`
- `method`
- `weight_class_name`

**Useful for:**
- "누구랑 싸웠어?"
- "공통 상대"
- "최근 5경기 상대"

### `v_weight_class_activity_summary`

**Purpose:** 체급별 경기 수, 피니시 수, 평균 라운드 등 dashboard/analysis용 집계.

**Useful for:**
- "가장 피니시가 많은 체급"
- "체급별 경기 수"
- "2024년 체급별 트렌드"

### `v_recent_collection_health`

**Purpose:** 최신 데이터 수집 상태를 LLM에 제공하기 위한 메타 view.

**Recommended columns:**
- `latest_event_date`
- `latest_event_with_results_date`
- `events_in_last_14_days`
- `recent_completed_matches_missing_result`
- `last_tapology_scraped_at`

**Useful for:**
- 최근 이벤트 결과가 DB에 아직 반영되지 않았을 때 과신 방지
- "DB는 app source of truth지만 최근 수집 지연 가능" 메시지의 근거 제공

## Recommended CTE Templates

CTE 템플릿은 실제 DB view를 만들기 전에도 프롬프트에 넣을 수 있는 표준 SQL 패턴이다. 모델이 복잡한 query를 만들 때 이 패턴을 복사해 확장하도록 유도한다.

### CTE 1. Completed Fighter Fights

```sql
WITH completed_fights AS (
  SELECT
    f.id AS fighter_id,
    f.name AS fighter_name,
    fm.match_id,
    fm.result,
    m.method,
    m.result_round,
    e.name AS event_name,
    e.event_date,
    wc.name AS weight_class_name
  FROM fighter_match fm
  JOIN fighter f ON f.id = fm.fighter_id
  JOIN match m ON m.id = fm.match_id
  JOIN event e ON e.id = m.event_id
  LEFT JOIN weight_class wc ON wc.id = m.weight_class_id
  WHERE e.event_date <= CURRENT_DATE
    AND fm.result IS NOT NULL
)
```

**Use for:** record, recent fights, method summaries, per-fighter aggregations.

### CTE 2. Fighter Record Summary

```sql
WITH completed_fights AS (...),
record_summary AS (
  SELECT
    fighter_id,
    fighter_name,
    COUNT(*) AS total_completed_fights,
    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN result = 'nc' THEN 1 ELSE 0 END) AS no_contests,
    ROUND(
      100.0 * SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END)
      / NULLIF(
          SUM(CASE WHEN result IN ('win', 'loss') THEN 1 ELSE 0 END),
          0
        ),
      2
    ) AS win_rate_excluding_draw_nc
  FROM completed_fights
  GROUP BY fighter_id, fighter_name
)
```

**Use for:** "승률", "전적", "Top N by wins/losses".

### CTE 3. Method Category Summary

```sql
WITH completed_fights AS (...),
method_summary AS (
  SELECT
    fighter_id,
    fighter_name,
    SUM(CASE WHEN result = 'win' AND (method ILIKE 'KO-%' OR method ILIKE 'TKO-%') THEN 1 ELSE 0 END) AS ko_tko_wins,
    SUM(CASE WHEN result = 'win' AND method ILIKE 'SUB-%' THEN 1 ELSE 0 END) AS submission_wins,
    SUM(CASE WHEN result = 'win' AND method ILIKE '%DEC%' THEN 1 ELSE 0 END) AS decision_wins,
    SUM(CASE WHEN result = 'win' AND (
      method ILIKE 'KO-%' OR method ILIKE 'TKO-%' OR method ILIKE 'SUB-%'
    ) THEN 1 ELSE 0 END) AS finish_wins
  FROM completed_fights
  GROUP BY fighter_id, fighter_name
)
```

**Use for:** KO/TKO wins, submission wins, decision wins, finish rate.

### CTE 4. Current Rankings

```sql
WITH current_rankings AS (
  SELECT
    f.id AS fighter_id,
    f.name AS fighter_name,
    wc.id AS weight_class_id,
    wc.name AS weight_class_name,
    r.ranking,
    (r.ranking = 0) AS is_champion
  FROM ranking r
  JOIN fighter f ON f.id = r.fighter_id
  JOIN weight_class wc ON wc.id = r.weight_class_id
)
```

**Use for:** current champion, weight-class ranking, ranked fighter filters.

### CTE 5. Fighter-Side Round Stats

```sql
WITH fighter_round_stats AS (
  SELECT
    f.id AS fighter_id,
    f.name AS fighter_name,
    fm.match_id,
    ms.round,
    ms.knockdowns,
    ms.sig_str_landed,
    ms.sig_str_attempted,
    ms.total_str_landed,
    ms.total_str_attempted,
    ms.td_landed,
    ms.td_attempted,
    ms.submission_attempts,
    ms.control_time_seconds
  FROM fighter_match fm
  JOIN fighter f ON f.id = fm.fighter_id
  JOIN match_statistics ms ON ms.fighter_match_id = fm.id
)
```

**Use for:** striking/grappling aggregate metrics.

### CTE 6. Event Fight Card Pairing

```sql
WITH fight_card AS (
  SELECT
    e.id AS event_id,
    e.name AS event_name,
    e.event_date,
    m.id AS match_id,
    m."order" AS fight_order,
    m.is_main_event,
    m.is_title_bout,
    wc.name AS weight_class_name,
    MAX(CASE WHEN rn = 1 THEN fighter_id END) AS fighter_1_id,
    MAX(CASE WHEN rn = 1 THEN fighter_name END) AS fighter_1_name,
    MAX(CASE WHEN rn = 2 THEN fighter_id END) AS fighter_2_id,
    MAX(CASE WHEN rn = 2 THEN fighter_name END) AS fighter_2_name
  FROM (
    SELECT
      fm.match_id,
      f.id AS fighter_id,
      f.name AS fighter_name,
      ROW_NUMBER() OVER (PARTITION BY fm.match_id ORDER BY f.name) AS rn
    FROM fighter_match fm
    JOIN fighter f ON f.id = fm.fighter_id
  ) fighters
  JOIN match m ON m.id = fighters.match_id
  JOIN event e ON e.id = m.event_id
  LEFT JOIN weight_class wc ON wc.id = m.weight_class_id
  GROUP BY e.id, e.name, e.event_date, m.id, m."order", m.is_main_event, m.is_title_bout, wc.name
)
```

**Use for:** event card, upcoming bouts, main event, title bout list.

## Suggested Query Map for Prompt

프롬프트에는 전체 스키마 앞에 아래처럼 짧은 Query Map을 넣는 것을 추천한다.

```text
## Preferred Query Map

Fighter fight results, records, recent fights:
- Prefer v_completed_fighter_fights.
- Use v_fighter_fight_results when scheduled/cancelled/postponed bouts may matter.

Current champions and rankings:
- Prefer v_current_rankings.
- ranking = 0 means champion.

Win/loss/draw/nc summaries:
- Prefer v_fighter_record_summary.

KO/TKO, submission, decision, finish rate:
- Prefer v_fighter_method_summary.

Striking and grappling totals:
- Prefer v_fighter_stat_totals.

Strike target or position breakdown:
- Prefer v_fighter_strike_profile.

UFCStats profile plus Tapology profile fields:
- Prefer v_fighter_profile_enriched.

Tapology all-career promotion or method records:
- Prefer v_fighter_career_promotion_summary or v_fighter_career_method_summary.
- Do not mix these with UFC-only fight result views unless the user asks to compare scopes.

Event fight cards and upcoming bouts:
- Prefer v_event_fight_card.
```

## Implementation Order

1. `v_fighter_fight_results`
2. `v_completed_fighter_fights`
3. `v_current_rankings`
4. `v_fighter_record_summary`
5. `v_fighter_method_summary`
6. `v_fighter_stat_totals`
7. `v_event_fight_card`
8. `v_fighter_profile_enriched`
9. Tapology career summary views
10. Optional helper views based on observed user questions

## Validation Checklist

For each view, add small SQL tests or eval questions that verify:

- Row counts are not unexpectedly duplicated.
- A known fighter's recent fights match source data.
- Champion rows use `ranking = 0`.
- Win rate denominator is documented and consistent.
- Method buckets classify KO/TKO, SUB, and DEC correctly.
- Upcoming fights do not appear in completed-fight views.
- Tapology all-career views are not used for UFC-only questions.
