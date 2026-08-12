# LLM SQL Agent Prompt Feedback

## Context

현재 AI 채팅은 많은 도메인별 tool 대신 `execute_raw_sql_query` 단일 tool을 사용한다. 모델은 전체 DB 스키마를 프롬프트로 받고, 사용자 질문에 맞는 SQL을 직접 생성한 뒤 SQL 결과를 근거로 답변한다.

이 접근은 tool 선택 오류를 줄이는 데 유리하지만, 위험의 중심이 "tool routing"에서 "SQL 의미 정확도"로 이동한다. 따라서 프롬프트는 단순히 SQL 생성을 유도하는 역할을 넘어, 모델이 자주 틀리는 도메인 의미와 응답 경계를 명확히 제한해야 한다.

## Summary Recommendation

단일 SQL tool 방향은 유지하되, 프롬프트는 더 작고 명확한 책임 단위로 나누는 것이 좋다.

- SQL agent는 "정확한 SQL 실행과 결과 기반 초안"까지만 책임진다.
- 사용자에게 보여줄 자연어 답변은 별도 response node가 항상 담당한다.
- Supervisor는 "명시적 선수 간 비교"와 "그룹 내 지표 비교/랭킹"을 구분해야 한다.
- 전체 스키마는 유지할 수 있지만, 자주 틀리는 metric 정의와 canonical query pattern을 스키마보다 더 강한 지시로 제공해야 한다.

## Priority 1. Remove Conflicting Verification Instructions

### Current Issue

`src/llm/prompts.py`의 SQL agent prompt는 verification을 두 방식으로 말한다.

- "Verify data characteristics before main query (MANDATORY)"
- "Verify field values ONLY when filtering on ambiguous text fields"
- "Skipping verification step"을 common mistake로 경고

이 조합은 모델에게 매번 verification query를 실행하라는 뜻인지, 특정 상황에서만 실행하라는 뜻인지 모호하다. 결과적으로 불필요한 tool call이 늘거나, 반대로 필요한 검증을 생략할 수 있다.

### Recommended Change

verification 규칙을 decision tree로 바꾼다.

```text
Before the main query, decide whether a verification query is required:

Run a verification query only if:
1. The user filters on ambiguous free-text fields such as match.method or fighter_match.result.
2. The user uses Korean/English natural terms that may not match stored DB values.
3. A previous query returned 0 rows and the likely cause is a text value mismatch.

Do not run a verification query if:
1. The query uses only IDs from conversation context.
2. The query uses boolean fields such as belt = true.
3. The query is a simple ranking/profile lookup with no ambiguous text filter.
```

## Priority 2. Do Not Reuse SQL Agent Reasoning Directly as User Answer

### Current Issue

`text_response_node` reuses a single agent's `reasoning` as `final_response` without calling the response prompt again. This saves one model call, but it weakens safety and style guarantees.

This is especially risky because the SQL prompt instructs the model to include entity IDs in `SELECT`, while user-facing style rules say entity IDs must never be shown. If the SQL agent mentions internal IDs in its final reasoning, the user can see them.

### Recommended Change

Make SQL agent output private by default.

Implement this as a hard contract:

- Always route SQL results through `text_response_node`, even for a single agent.
- SQL agent `reasoning` is private execution context and must never be copied into `final_response`.
- Remove both reasoning reuse paths:
  - the single-agent fast path that skips the response LLM call
  - the exception fallback that returns agent `reasoning`
- If `text_response_node` fails, fail closed with a controlled fallback message or deterministic sanitized summary from SQL rows. Do not reuse SQL agent reasoning as user-visible text.

The final response node is the only component allowed to produce user-visible text.

## Priority 3. Split Response Style Prompts by Node Responsibility

### Current Issue

`RESPONSE_STYLE_GUIDE` is shared by direct response, text response, and visualization prompts. It includes SQL-grounding rules such as "provided SQL results only", which do not fit general MMA knowledge answers.

This creates unnecessary tension:

- `direct_response` handles MMA rules, techniques, and general knowledge where no SQL result exists.
- `visualization` chooses chart metadata, not conversational answer content.
- `text_response` is the only node that should strictly depend on SQL result data.

### Recommended Change

Split the guide into separate prompt fragments.

```text
GENERAL_MMA_STYLE
- Natural Korean
- MMA-specific
- Refuse non-MMA questions
- Do not claim live database facts

SQL_GROUNDED_RESPONSE_STYLE
- Use only SQL result data
- Never expose entity IDs
- Do not add background knowledge
- Explain numbers naturally

VISUALIZATION_DECISION_STYLE
- Choose only supported chart types
- Use only actual returned columns
- Return chart metadata and insights only
```

## Priority 4. Improve Supervisor Routing Rules

### Current Issue

The supervisor prompt routes based on broad keywords such as "비교", "vs", "차이", and "누가 더". This can misclassify group ranking questions as fighter-to-fighter comparison.

Example:

```text
라이트급 상위 5명 테이크다운 비교해줘
```

This asks for a group metric comparison/ranking, not necessarily a head-to-head fighter comparison. It can be handled by `mma_analysis`.

### Recommended Change

Add a sharper distinction:

```text
fighter_comparison:
- Use only when the question names two or more specific fighters, or explicitly asks for a head-to-head matchup.
- Examples: "존 존스 vs 알렉스 페레이라", "마카체프랑 올리베이라 비교"

mma_analysis:
- Use for rankings, top N, group comparisons, weight-class leaderboards, trend analysis, and aggregated metrics.
- Examples: "라이트급 상위 5명 테이크다운 비교", "KO 승률 Top 10"

complex:
- Use when the user asks for both a single-fighter analysis and a named fighter comparison in one request.
```

## Priority 5. Clarify "DB Is Ground Truth" vs Data Freshness

### Current Issue

The prompt says SQL results are live ground truth, while also saying data updates are performed every Tuesday and recent event results may not yet be reflected.

This is not technically contradictory, but it can cause overconfident answers. The database is ground truth for the app, but not necessarily real-world complete if the collector has not yet ingested the latest event.

### Recommended Change

Change the wording:

```text
Treat the database as the source of truth for this application. Do not override SQL results with model knowledge.

However, if the query concerns events within the latest collection window and result/method fields are empty, state that the app's database may not have ingested those results yet.
```

## Priority 6. Add Canonical Metric Definitions

### Current Issue

The prompt includes schema and examples, but not enough canonical metric definitions. This leaves the model to infer business logic for common MMA metrics.

### Recommended Change

Add a compact "Metric Definitions" section before query examples.

Recommended examples:

```text
## Canonical Metric Definitions

completed_fight:
- event_date <= current_date
- fighter_match.result IS NOT NULL
- COALESCE(bout_status, 'completed') NOT IN ('scheduled', 'cancelled', 'postponed')
- bout_status is sparse in the current DB, so NULL is treated as completed only when result/date conditions are satisfied.

ufc_wins:
- Count fighter_match rows where result = 'win'.

ufc_losses:
- Count fighter_match rows where result = 'loss'.

win_rate:
- wins / (wins + losses + draws + no_contests).
- Use the same denominator consistently across prompts, schema metadata, and canonical views.

finish_wins:
- Wins where match.method indicates KO/TKO or submission.

finish_rate:
- finish_wins / total_completed_fights.
- Use this default unless the user explicitly asks for a different denominator.

recent_fights:
- event_date <= current_date
- ORDER BY event_date DESC
```

Metric definitions reduce reliance on model intuition and keep SQL generation aligned with product policy.

## Priority 7. Keep Full Schema, But Add a Task-Specific Schema Index

### Current Issue

The full schema is not too large for Gemini 3 Flash Preview, but more schema does not automatically mean better SQL. Full schemas increase the chance that the model sees multiple plausible paths and chooses the wrong one.

### Recommended Change

Keep the full schema available, but put a short "query map" before it.

```text
## Query Map

Fighter identity/profile:
- fighter

Fight-side result and fighter-specific stats:
- fighter_match
- Join fighter.id = fighter_match.fighter_id

Bout/event metadata:
- match
- event
- Join fighter_match.match_id = match.id
- Join match.event_id = event.id

Current rankings:
- ranking
- weight_class
```

The query map should encode the preferred path, while the full schema remains available for uncommon questions.

## Priority 8. Add DB View Metadata and Usage Guidance

### Current Issue

The recommended SQL views in `docs/feedback/2026-08-10-001-recommended-sql-views-and-cte-templates.md` only help the SQL agent if the agent can see them and is instructed to prefer them. The current prompt path loads `src/schema.json` through `load_schema_prompt()`, so creating DB views alone will not change model behavior.

### Recommended Change

Treat DB views as the canonical source for common fact paths and metric definitions. Prompt/schema should expose view metadata and usage guidance, not duplicate the full SQL logic.

For this implementation, the initial canonical DB view scope is:

- `v_fighter_fight_results`
- `v_completed_fighter_fights`
- `v_fighter_opponents`
- `v_current_rankings`
- `v_fighter_record_summary`
- `v_fighter_method_summary`

After creating these views:

1. Add each view to `src/schema.json` with:
   - purpose
   - source tables/views
   - output columns
   - relationships to base tables
   - metric policies and denominator notes
   - "prefer this view for..." guidance
2. Update `format_schema_for_prompt()` so the prompt renders:
   - Preferred Query Map first
   - View metadata second
   - Full raw table schema after that
3. Update both SQL prompts to say:
   - Prefer canonical views for supported query families.
   - Use raw tables only when the user asks for data outside the view's scope.
   - Do not reimplement a view's metric definition with ad hoc joins unless the query requires dimensions the view does not expose.
4. Keep CTE templates as temporary bootstrap/examples only. Once a DB view exists, the prompt should prefer the view over copying CTE logic.

Recommended initial Query Map additions:

```text
Fighter fight results, records, recent fights:
- Prefer v_completed_fighter_fights.
- Use v_fighter_fight_results when scheduled/cancelled/postponed bouts may matter.
- Prefer v_fighter_opponents for opponent, common-opponent, and recent-opponent questions.

Current champions and rankings:
- Prefer v_current_rankings.
- ranking = 0 means champion.

Record/win-rate summaries:
- Prefer v_fighter_record_summary.
- Default win rate is wins / (wins + losses + draws + no_contests).

Method/finish summaries:
- Prefer v_fighter_method_summary.
- Current DB canonical KO/TKO pattern is method ILIKE 'KO/TKO%'.
- Default finish rate is finish_wins / total_completed_fights.
```

### Completed Fight Prompt Policy

For completed-fight views, the prompt should describe the product policy:

```text
completed_fight:
- event_date <= current_date
- fighter_match.result IS NOT NULL
- exclude non-completed Tapology statuses with COALESCE(bout_status, 'completed') NOT IN ('scheduled', 'cancelled', 'postponed')
- bout_status is sparse in the current DB, so NULL is treated as completed only when result/date conditions are satisfied
```

### Method Bucket Prompt Policy

Based on the 2026-08-11 DB check:

```text
method buckets:
- KO/TKO: method ILIKE 'KO/TKO%' (also accept KO-% or TKO-% only for future/legacy data)
- Submission: method ILIKE 'SUB-%'
- Decision: method IN ('U-DEC', 'S-DEC', 'M-DEC') OR method ILIKE '%DEC%'
- DQ: method ILIKE 'DQ%'
- Other/non-standard: Overturned%, CNC, Other, or unmatched non-null methods
```

### Column Naming Policy

The prompt/schema metadata should expose view output columns with `*_attempted` suffixes. The raw `strike_detail` table currently uses `*_attempts`, while `match_statistics` uses `*_attempted`; this is a source-table naming difference, not a semantic difference. Both mean attempts made by the fighter.

## Priority 9. Reduce Prompt Duplication Between SQL Agents

### Current Issue

`SQL_AGENT_PROMPT` and `FIGHTER_COMPARISON_PROMPT` duplicate DB trust, response style, temporal awareness, table naming, aliases, ID rules, and lowercase rules. Duplicated policy tends to drift.

### Recommended Change

Create shared prompt fragments:

- `DB_SCHEMA_BLOCK`
- `SQL_SAFETY_AND_STYLE_RULES`
- `TEMPORAL_RULES`
- `DATA_GROUNDING_RULES`
- `METRIC_DEFINITIONS`
- `MMA_ANALYSIS_TASK_RULES`
- `FIGHTER_COMPARISON_TASK_RULES`

This makes future prompt tuning safer and easier to evaluate.

## Priority 10. Add Prompt-Level Refusal for Unsupported Data

### Current Issue

If the DB schema does not contain a requested concept, the model may improvise with nearby columns or background knowledge.

### Recommended Change

Add a refusal rule:

```text
If the requested data is not represented in the schema or SQL results, say that the current database cannot answer that part. Do not infer it from model knowledge.
```

This is important for questions about betting odds, injuries, unofficial news, camp changes, or non-UFC records if those fields are not present.

## Suggested Implementation Order

1. Stop direct reuse of SQL agent reasoning as final user answer, including failure fallbacks.
2. Remove SQL verification instruction conflicts.
3. Add canonical metric definitions and Preferred Query Map before the raw schema.
4. Create the initial canonical DB views listed in Priority 8 and add their metadata to `src/schema.json`.
5. Refine supervisor routing examples.
6. Split response style fragments by node responsibility.
7. Add unsupported-data refusal rule.
8. Refactor duplicated prompt fragments.

## Evaluation Recommendations

Prompt changes should be measured with a small gold set before rollout.

Minimum recommended eval cases:

- Simple fighter profile
- Fighter current record
- Recent fights
- Upcoming fights
- Top N by KO wins
- Win rate by weight class
- Named fighter comparison
- Group ranking comparison
- Follow-up using "그 선수" or "1위"
- Empty result recovery
- Recent event with missing result/method
- Unsupported data request

For each case, capture:

- Route selected by supervisor
- SQL generated
- Tool result row count
- Final user answer
- Whether entity IDs leaked
- Whether answer added facts not in SQL results
