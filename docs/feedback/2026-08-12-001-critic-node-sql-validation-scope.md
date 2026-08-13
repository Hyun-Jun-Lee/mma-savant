# Critic Node SQL Validation Scope

## Context

`docs/feedback/2026-08-09-001-llm-prompt-sql-feedback.md`의 여러 권고 중 이번 작업은 `critic` 노드 자체에 집중한다.

다음 항목은 별도 에이전트나 별도 작업에서 다룬다.

- 최종 응답 소유권 및 `text_response_node`의 SQL agent reasoning 재사용 제거
- SQL agent prompt 강화
- SQL 효율성 평가
- SQL AST/parser 도입
- collector freshness metadata 주입
- specialized SQL tools 또는 query builder 전환

따라서 이번 범위의 목표는 critic이 SQL agent가 만든 SQL과 결과를 보고, 제품의 metric 정책과 사용자 질문에 의미적으로 맞는지 더 안정적으로 검증하도록 만드는 것이다.

## Why Metric Policy Belongs in Critic

metric 정책을 critic에 반영하는 이유는 SQL agent가 만든 SQL이 제품 기준의 "정답 SQL"인지 확인하기 위해서다.

예를 들어 SQL agent가 `win_rate = wins / total_fights`로 계산하면 SQL 문법은 맞고 결과도 정상 범위일 수 있다. 하지만 제품 기본 정책이 `wins / (wins + losses + draws + no_contests)`라면 의미적으로는 틀린 SQL이다.

critic이 이런 차이를 판단하려면 다음과 같은 canonical metric policy를 알아야 한다.

- win rate의 기본 denominator
- draw/no contest 포함 여부
- completed fight의 정의
- KO/TKO, submission, decision bucket 정의
- recent/upcoming 시간 조건

다만 이 정책은 LLM prompt에만 넣기보다, 가능한 범위에서는 deterministic validator의 기준값으로 쓰는 것이 더 안정적이다.

## Recommended Phase 1 Scope

### 1. Clarify Critic Responsibility

critic은 SQL을 더 효율적으로 작성했는지 평가하지 않는다.

critic의 책임은 다음으로 제한한다.

- 사용자 질문과 SQL 의미의 일치 여부
- metric/window/filter 조건 누락 여부
- 제품 canonical metric policy 위반 여부
- 결과값 sanity check
- retry가 필요한 경우 구체적인 machine feedback 생성

critic은 raw table SQL을 사용했다는 이유만으로 실패시키지 않는다. canonical view를 쓰지 않았더라도 metric/window/filter 의미가 맞으면 통과할 수 있어야 한다.

### 2. Define Canonical Metric Policy for Critic

critic 내부 기준으로 다음 정책을 둔다.

```text
completed_fight:
- event_date <= current_date
- fighter-side result IS NOT NULL
- exclude non-completed bout statuses:
  COALESCE(bout_status, 'completed') NOT IN ('scheduled', 'cancelled', 'postponed')

win_rate:
- wins / (wins + losses + draws + no_contests)
- this must match the SQL agent prompt, schema metadata, and `v_fighter_record_summary.win_rate`
- if the user explicitly asks for clean win/loss rate excluding draws and no contests, use wins / (wins + losses)

finish_rate:
- default finish_wins / total_completed_fights
- if the user explicitly asks for finish rate among wins, use finish_wins / wins

KO/TKO wins:
- fighter-side result = 'win'
- method ILIKE 'KO/TKO%'
- accept KO-% or TKO-% only for future or legacy data

submission wins:
- fighter-side result = 'win'
- method ILIKE 'SUB-%'

decision participation/fights:
- decision method bucket required
- do not require result = 'win' unless the user asks for decision wins

decision wins:
- fighter-side result = 'win'
- decision method bucket required
```

### 3. Strengthen Deterministic Phase A Guardrails

현재 critic Phase A는 SQL syntax, empty result, value range 중심이다. 여기에 질문 intent와 metric keyword 기반 검사를 추가한다.

권장 guardrail:

- `recent`, `latest`, `last`, `최근`, `마지막` 질문이면 completed view 또는 completed-fight 조건이 필요하다.
- `upcoming`, `next`, `다음`, `예정` 질문이면 future event 조건이 필요하다.
- KO/TKO wins 질문이면 win 조건과 KO/TKO method bucket이 모두 필요하다.
- submission wins 질문이면 win 조건과 submission method bucket이 모두 필요하다.
- decision wins 질문이면 win 조건과 decision method bucket이 모두 필요하다.
- decision participation/fights 질문이면 decision method bucket은 필요하지만 `result = 'win'`을 강제하면 안 된다.
- win rate 질문이면 canonical record summary view를 쓰거나 `wins / (wins + losses + draws + no_contests)` 정책을 따라야 한다.
- rate/pct/percentage/accuracy류 결과값은 0~100 범위를 벗어나면 실패한다.
- count/wins/losses/total/fights류 결과값은 음수면 실패한다.

1차 구현에서는 SQL AST 없이 문자열/정규식과 결과값 기반으로 명백한 위반만 잡는다.

정규식 guardrail은 "필요 키워드가 SQL 어딘가에 있다"는 사실만 확인할 수 있으므로, alias/scope/grain/precedence까지 맞다고 증명하지 않는다. 따라서 다음 경계를 둔다.

```text
Phase A deterministic failure:
- canonical view가 없고, 필수 metric/window/filter 조각이 SQL 전체에서 명백히 빠진 경우
- 결과값 sanity check가 명백히 깨진 경우
- 질문 intent와 반대되는 조건이 명백히 들어간 경우

Phase B semantic escalation:
- self join, 여러 alias, nested CTE, window function, OR/AND 혼합 조건처럼 정규식이 scope를 오판하기 쉬운 SQL
- 필수 조건 문자열은 보이지만 어느 table alias/grain에 적용됐는지 확신할 수 없는 SQL
- recent N, opponent comparison, denominator 계산처럼 row grain이 결과 의미를 바꾸는 SQL

Pass without Phase B concern:
- canonical view/summary column을 사용했고 질문 intent와 필요한 filter가 직접적으로 드러나는 SQL
- raw table SQL이지만 단일 fact path이고 필수 조건이 단순 WHERE/CASE에 고립되어 있어 오탐 가능성이 낮은 SQL
```

즉 Phase A는 high-confidence blocker만 실패시키고, 복잡한 SQL의 의미 검증은 Phase B에 맡긴다. eval에서 alias/grain/OR precedence 오류가 반복되면 그때 SQL AST/parser 기반 validator를 별도 작업으로 도입한다.

### 4. Redesign Empty Result Handling

0행 결과를 항상 critic failure로 처리하면 안 된다.

권장 정책:

```text
0 rows + ambiguous text filter likely:
- fail with retry feedback
- suggest verifying method/result/name/weight_class/event text values

0 rows + query conditions are valid and unambiguous:
- pass critic
- downstream response can say the current DB did not find matching rows

requested data is outside schema coverage:
- route to unsupported-data response or controlled refusal
- do not retry the same SQL repeatedly
```

예를 들어 특정 선수명, method, weight class, event name처럼 저장값 mismatch 가능성이 큰 free-text filter가 있을 때는 retry feedback이 유효하다. 반대로 "2024년 헤비급 여성 챔피언"처럼 조건 자체가 명확하지만 결과가 없을 수 있는 질문은 0행이 정상 결과일 수 있다.

critic은 단순 bool만 반환하지 않고 validation status를 함께 반환한다.

```python
validation_status: Literal["passed", "retry_needed", "valid_empty", "unsupported"]
```

상태별 라우팅 정책:

- `passed`: `critic_passed=True`, 기존 통과 경로로 `text_response`와 필요한 경우 `visualization`으로 이동한다.
- `retry_needed`: `critic_passed=False`, `critic_feedback`을 포함해 SQL agent retry 경로로 이동한다.
- `valid_empty`: `critic_passed=True`, `text_response`로 이동해 현재 DB에서 조건에 맞는 결과를 찾지 못했다는 응답을 생성한다.
- `unsupported`: `critic_passed=False`로 기록하되 retry하지 않고 `text_response`로 이동한다. `text_response`는 unsupported-data boundary를 사용자에게 설명하고 모델 지식으로 보강하지 않는다.

이를 위해 `critic_route`는 `critic_passed=False`만으로 항상 retry/END를 선택하지 말고, `validation_status == "unsupported"`인 경우에는 `text_response`로 분기해야 한다.

### 5. Keep LLM Phase B as a Secondary Semantic Check

LLM critic은 deterministic Phase A를 대체하지 않는다. Phase A가 잡을 수 있는 것은 코드로 먼저 잡고, LLM Phase B는 애매한 의미 정합성만 검토한다.

LLM Phase B prompt에는 다음 방향을 반영한다.

```text
You are not evaluating SQL efficiency.
Validate only semantic correctness against the user request and canonical metric policies.
Do not fail raw-table SQL only because it did not use a canonical view.
Fail only when the metric, window, filter, or comparison basis appears incorrect.
When failing, name the exact issue and the minimal correction.
```

Phase B가 timeout/error인 경우에는 Phase A가 충분히 강하다는 전제에서 fail-open을 유지할 수 있다. 단, deterministic high-risk guardrail 실패는 항상 failure로 처리해야 한다.

### 6. Add Seeded Bad-SQL Tests

critic 개선은 실제 LLM 호출 없이도 테스트 가능해야 한다.

최소 테스트 케이스:

Negative regression:

- recent fights 질문인데 future event 제외 조건이 없음
- KO/TKO wins 질문인데 `result = 'win'` 조건이 없음
- submission wins 질문인데 submission method bucket이 없음
- decision fights/participation 질문인데 `result = 'win'`을 강제함
- win rate가 `wins / total_fights`로 계산됨
- rate 결과가 120처럼 0~100 범위를 벗어남
- count 결과가 -1처럼 음수임
- 명확하고 유효한 0행 결과를 무조건 실패시키지 않음

Positive regression:

- canonical `v_fighter_record_summary.win_rate`를 사용한 win rate SQL은 통과함
- raw table SQL이라도 `wins / (wins + losses + draws + no_contests)` denominator를 명확히 따르면 통과함
- 명시적으로 clean win/loss rate를 요청한 경우 `wins / (wins + losses)` denominator를 통과시킴
- canonical `v_completed_fighter_fights`를 사용한 recent fights SQL은 completed-fight 조건을 재구현하지 않아도 통과함
- KO/TKO wins 질문에서 `result = 'win'`과 KO/TKO method bucket이 모두 있으면 통과함
- decision participation/fights 질문에서 decision method bucket은 있고 `result = 'win'`이 없으면 통과함
- 명확하고 유효한 0행 결과는 `validation_status="valid_empty"`로 통과함
- schema coverage 밖 요청은 `validation_status="unsupported"`와 `critic_passed=False`를 반환하지만 retry하지 않고 `text_response`로 라우팅됨

이 테스트들은 critic의 deterministic Phase A가 실제로 위험한 SQL을 잡는지 확인하는 regression suite 역할을 한다.

## Suggested Implementation Order

1. critic의 canonical metric policy를 코드 상수 또는 작은 helper로 정의한다. 이때 win rate는 SQL agent prompt/schema/view와 동일하게 `wins / (wins + losses + draws + no_contests)`를 기본값으로 둔다.
2. `_run_phase_a(agent_results)` 계약을 `_run_phase_a(agent_results, resolved_query)`로 변경한다.
3. `resolved_query`에서 temporal intent, method metric intent, win-rate intent, ambiguous free-text filter 여부를 추출하는 작은 intent classifier/helper를 추가한다.
4. 현재 Phase A에 intent/metric 기반 deterministic guardrail을 추가하되, alias/grain/OR precedence처럼 정규식으로 확신할 수 없는 SQL은 실패가 아니라 Phase B semantic escalation 대상으로 둔다.
5. empty result handling을 `validation_status: Literal["passed", "retry_needed", "valid_empty", "unsupported"]`로 분리한다.
6. `unsupported`는 `critic_passed=False`로 기록하지만 retry하지 않고 `text_response`로 라우팅하도록 `critic_route`를 보강한다.
7. LLM Phase B prompt에서 SQL 효율성 평가를 명시적으로 제외하고 semantic correctness만 보게 한다.
8. seeded bad-SQL 테스트와 positive regression 테스트를 추가한다.
9. 기존 `src/tests/llm` critic/node 테스트를 보강해 retry feedback 문구, `validation_status`, pass/fail 결과, unsupported 라우팅을 검증한다.

## Out of Scope for This Work

- SQL agent가 더 좋은 SQL을 생성하도록 prompt를 개선하는 작업
- SQL 실행 성능, index 사용, join order, query cost 검증
- SQL AST/parser 기반 alias/scope/grain 정밀 분석
- 최종 사용자 응답 생성 책임 변경
- DB view 생성 또는 schema prompt metadata 변경
- collector metadata를 prompt에 동적으로 주입하는 작업

## Open Follow-Up

향후 eval에서 다음 유형의 오류가 반복되면 SQL AST/parser 도입을 검토한다.

- 조건은 존재하지만 잘못된 table alias에 적용된 경우
- opponent self-join에서 본인/상대 조건이 뒤집힌 경우
- denominator가 fighter_match grain이 아니라 detail row grain으로 계산된 경우
- recent N이 fighter별 N이 아니라 전체 합산 N으로 적용된 경우
- OR/AND precedence가 metric 의미를 바꾸는 경우

즉 1차에서는 AST를 도입하지 않고, deterministic guardrail과 seeded bad-SQL 테스트로 critic의 정답성 검증력을 먼저 끌어올린다.
