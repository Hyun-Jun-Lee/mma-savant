# MMA Savant 멀티 에이전트 구현 가이드

> 이 문서는 `docs/MULTI_AGENT_ARCHITECTURE.md`의 설계를 기반으로 한 구체적인 구현 가이드입니다.
> 구현 완료 후 실제 코드와 대조하여 검증 용도로 사용합니다.

---

## Step 1: 인프라 — State, 모델, 스키마

**목적**: 이후 모든 노드가 의존하는 기반을 먼저 만든다. 기존 코드는 건드리지 않는다.

### 1-1. `MainState` + `AgentResult` 정의

현재 `src/llm/graph/state.py`에 `MMAGraphState`가 있다. 이 파일에 `MainState`와 `AgentResult`를 **추가**한다 (기존 `MMAGraphState`는 아직 삭제하지 않음).

```
수정 파일: src/llm/graph/state.py
추가 내용:
  - AgentResult (TypedDict)
  - reduce_agent_results (커스텀 reducer)
  - MainState (TypedDict) — 문서에 정의된 전체 필드
```

### 1-2. 모델 팩토리 확장

현재 `src/config.py`에는 `MAIN_MODEL`, `SUB_MODEL` 환경변수가 없다. 추가해야 한다.

```
수정 파일: src/config.py
추가 내용:
  - MAIN_MODEL: str (환경변수, 형식: "openrouter/google/gemini-3-flash-preview")
  - SUB_MODEL: str (환경변수, 형식: "openrouter/google/gemini-2.5-flash-lite")
```

```
수정 파일: src/llm/model_factory.py
추가 내용:
  - _parse_model_spec(spec) → (provider, model_name)
  - _create_model(provider, model_name) → BaseChatModel
  - get_main_model() → BaseChatModel
  - get_sub_model() → BaseChatModel
기존 유지:
  - create_llm_with_callbacks() — Step 5에서 제거 판단
```

`_create_model`은 기존 `get_openrouter_llm`, `get_anthropic_llm` 등을 내부에서 호출한다. 새 함수가 기존 provider 함수들을 재활용하는 구조.

### 1-3. 신규 Pydantic 스키마

현재 `src/llm/graph/schemas.py`에 `ChartVisualizationOutput`, `TextSummaryOutput`, `IntentClassification`이 있다.

```
수정 파일: src/llm/graph/schemas.py
추가 내용:
  - SupervisorRouting (route + agents 필드)
  - CriticValidation (passed, feedback, retry_count 등)
  - ConversationManagerOutput (resolved_query 등) — 필요시
기존 유지:
  - ChartVisualizationOutput — 시각화 노드에서 계속 사용
  - TextSummaryOutput — 텍스트 응답 노드에서 계속 사용
```

---

## Step 2: 개별 노드 구현

**목적**: 각 노드를 함수로 구현한다. 그래프에 연결하지 않으므로, 각 노드를 독립적으로 테스트할 수 있다.

### 2-1. Conversation Manager 노드

```
신규 파일: src/llm/graph/nodes/conversation_manager.py
```

이 노드의 입출력:
- **읽는 필드**: `messages` (대화 히스토리)
- **쓰는 필드**: `resolved_query`, `messages` (압축된 히스토리 + resolved HumanMessage 추가)

내부 동작:
1. `messages`에서 히스토리 길이 확인
2. 히스토리가 3턴 이하 → 압축 불필요, 현재 질문만 `resolved_query`로 설정
3. 히스토리가 3턴 초과 → SUB_MODEL에 최근 3턴 원본 + 이전 대화 요약 요청
4. 대명사/생략이 있으면 맥락 해소된 질문을 `resolved_query`로 반환
5. `messages`에 `HumanMessage(content=resolved_query)` 추가

```
신규 프롬프트: src/llm/graph/prompts.py에 CONVERSATION_MANAGER_PROMPT 추가
```

현재 `CONTEXT_ENRICHER_PROMPT`의 로직을 흡수하되, 히스토리 압축 + 주제 전환 감지가 추가된다.

### 2-2. Supervisor 노드

```
신규 파일: src/llm/graph/nodes/supervisor.py
```

입출력:
- **읽는 필드**: `resolved_query`
- **쓰는 필드**: `route`, `active_agents`

내부 동작:
1. `resolved_query`를 SUB_MODEL에 전달 (with_structured_output → `SupervisorRouting`)
2. `route`와 `agents` 반환
3. general일 때 `active_agents`는 빈 리스트

현재 `INTENT_CLASSIFIER_PROMPT`의 분류 로직을 흡수하되, followup이 제거되고 `fighter_comparison`, `complex`가 추가된다.

```
신규 프롬프트: src/llm/graph/prompts.py에 SUPERVISOR_PROMPT 추가
```

### 2-3. MMA 분석 노드

```
수정 파일: src/llm/graph/nodes/sql_agent.py (리팩토링)
또는
신규 파일: src/llm/graph/nodes/mma_analysis.py
```

현재 `sql_agent_node`는 `create_react_agent`로 SQL을 실행하고 `sql_result` + `agent_reasoning`을 반환한다. 이것을 `AgentResult` 형태로 변환한다.

변경 사항:
- 반환값: `{"agent_results": [AgentResult]}` (reducer가 합산)
- `AgentResult.needs_visualization`: react agent의 최종 AI 응답에서 판단하도록 프롬프트에 지시
- `AgentResult.reasoning`: 기존 `agent_reasoning` 추출 로직 유지
- `AgentResult.agent_name`: `"mma_analysis"` 고정

SQL 실행 도구(`src/llm/tools/sql_tool.py`)와 SQL 프롬프트(`src/llm/prompts.py`의 `SQL_AGENT_PROMPT`)는 그대로 사용한다. `needs_visualization` 판단 지시만 프롬프트에 추가한다.

### 2-4. Fighter 비교 노드

```
신규 파일: src/llm/graph/nodes/fighter_comparison.py
```

MMA 분석 노드와 동일한 구조(`create_react_agent` + `sql_tool`)이지만, **비교 전용 프롬프트**를 사용한다.

```
신규 프롬프트: src/llm/prompts.py에 FIGHTER_COMPARISON_PROMPT 추가
```

비교 프롬프트에는:
- 2명 이상 선수의 데이터를 각각 조회하는 SQL 패턴
- 공통 상대 비교 SQL 패턴
- 비교 결과를 구조화하는 지침
- `needs_visualization`: 비교 데이터는 대부분 True (radar, bar chart 등)

반환값은 MMA 분석과 동일하게 `{"agent_results": [AgentResult(agent_name="fighter_comparison", ...)]}`

### 2-5. Critic 노드

```
신규 파일: src/llm/graph/nodes/critic.py
```

입출력:
- **읽는 필드**: `agent_results`, `resolved_query`, `retry_count`
- **쓰는 필드**: `critic_passed`, `critic_feedback`, `retry_count`, (실패 3회 시 `final_response`)

내부 동작:
1. **Phase A (규칙 기반)**: `agent_results`의 각 결과에 대해
   - SQL 문법 검사 (sqlparse)
   - 컬럼명이 DB 스키마에 존재하는지 (`load_schema_prompt`의 정보 활용)
   - 결과 값 범위 타당성 (승률 0~100%, 음수 체크)
   - NULL/빈 결과 처리 적절성 (row_count == 0 감지)
2. **Phase B (LLM)**: Phase A 통과 시에만 SUB_MODEL 호출
   - `resolved_query`와 `agent_results`의 데이터가 일치하는지 정합성 검증
3. 실패 시: `retry_count += 1`, `critic_feedback` 설정
4. 3회 실패 시: `final_response`에 에러 메시지 설정

```
신규 프롬프트: src/llm/graph/prompts.py에 CRITIC_PROMPT 추가 (Phase B용)
```

DB 스키마 메타데이터는 `src/common/utils.py`의 `load_schema_prompt()`가 이미 텍스트로 반환하고 있다. Critic Phase A에서 이것을 파싱하여 테이블/컬럼 목록을 추출한다.

### 2-6. 텍스트 응답 노드

```
수정 파일: src/llm/graph/nodes/text_response.py
```

현재 `agent_reasoning` 재사용 로직이 이미 있다. 변경 사항:
- 입력: `state["sql_result"]` → `state["agent_results"]`
- 단일 에이전트 (`len(agent_results) == 1`): `reasoning` 재사용 (기존 로직 유지)
- 복수 에이전트: 각 `reasoning`을 합산하여 MAIN_MODEL에 전달, 통합 텍스트 생성
- 출력: `final_response` + `messages`에 AIMessage 추가

### 2-7. 시각화 노드

```
수정 파일: src/llm/graph/nodes/visualize.py
```

현재 `sql_result`에서 데이터를 읽는다. 변경 사항:
- 입력: `state["sql_result"]` → `state["agent_results"]`에서 데이터 추출
- 복수 에이전트 결과가 있으면 합산 데이터를 시각화 입력으로 구성
- `ChartVisualizationOutput` structured output은 그대로 유지
- 출력: `visualization_type`, `visualization_data`, `insights`

### 2-8. direct_response 노드

```
파일: src/llm/graph/nodes/direct_response.py
변경 거의 없음
```

현재 로직 그대로 유지. `resolved_query`를 읽어서 응답하도록 입력만 조정.

---

## Step 3: 그래프 조립

**목적**: Step 2의 노드들을 `MainState` 기반의 단일 그래프로 연결한다.

```
재작성 파일: src/llm/graph/graph_builder.py
```

현재 `graph_builder.py`의 `build_mma_graph(llm)` → `build_mma_graph(main_llm, sub_llm)`로 변경.

그래프 구조 전체:

```python
def build_mma_graph(main_llm, sub_llm):
    graph = StateGraph(MainState)

    # 노드 등록
    graph.add_node("conversation_manager", partial(conversation_manager_node, llm=sub_llm))
    graph.add_node("supervisor", partial(supervisor_node, llm=sub_llm))
    graph.add_node("direct_response", partial(direct_response_node, llm=sub_llm))
    graph.add_node("mma_analysis", partial(mma_analysis_node, llm=main_llm))
    graph.add_node("fighter_comparison", partial(fighter_comparison_node, llm=main_llm))
    graph.add_node("critic", partial(critic_node, llm=sub_llm))
    graph.add_node("text_response", partial(text_response_node, llm=main_llm))
    graph.add_node("visualization", partial(visualize_node, llm=sub_llm))

    # 에지 1: START → conversation_manager → supervisor
    graph.add_edge(START, "conversation_manager")
    graph.add_edge("conversation_manager", "supervisor")

    # 에지 2: supervisor → Send()로 동적 라우팅
    graph.add_conditional_edges(
        "supervisor",
        supervisor_dispatch,
        ["direct_response", "mma_analysis", "fighter_comparison"],
    )

    # 에지 3: direct_response → END
    graph.add_edge("direct_response", END)

    # 에지 4: 분석 에이전트들 → critic (fan-in)
    graph.add_edge("mma_analysis", "critic")
    graph.add_edge("fighter_comparison", "critic")

    # 에지 5: critic → 조건부 라우팅
    graph.add_conditional_edges("critic", critic_route, {
        "response": "response_fanout",
        "retry": "mma_analysis",  # 또는 원래 에이전트로 재라우팅
        "error": END,
    })

    # 에지 6: response_fanout → Send()로 텍스트 + 시각화 병렬
    graph.add_conditional_edges(
        "response_fanout",
        response_fanout_dispatch,
        ["text_response", "visualization"],
    )

    # 에지 7: 텍스트/시각화 → END
    graph.add_edge("text_response", END)
    graph.add_edge("visualization", END)

    return graph.compile()
```

**Critic 재시도의 라우팅 대상**: `complex` 라우팅에서 2개 에이전트가 병렬 실행된 후 Critic이 실패하면, 어느 에이전트를 재실행할지 결정해야 한다. 가장 단순한 방식은 `active_agents`를 다시 읽어서 `Send()`로 재실행하는 것이다:

```python
def critic_route(state: MainState) -> Union[str, list[Send]]:
    if state["critic_passed"]:
        return "response_fanout"
    if state["retry_count"] >= 3:
        return END
    # 실패한 에이전트 재실행 (agent_results는 reducer가 초기화됨)
    return [Send(agent, state) for agent in state["active_agents"]]
```

---

## Step 4: 서비스 레이어 연결

**목적**: 새 그래프를 실제 WebSocket 서비스에 연결한다.

```
수정 파일: src/llm/service.py
```

변경 사항:

```python
# 현재
async def initialize(self):
    llm, _ = create_llm_with_callbacks(...)
    self._compiled_graph = build_mma_graph(llm)

# 변경 후
async def initialize(self):
    main_llm = get_main_model()
    sub_llm = get_sub_model()
    self._compiled_graph = build_mma_graph(main_llm, sub_llm)
```

```python
# 현재: 히스토리 10개 슬라이싱
if len(messages) > 10:
    messages = messages[-10:]

# 변경 후: 100턴 상한만 유지
if len(messages) > 100:
    messages = messages[-100:]
```

결과 추출 로직:

```python
# 현재: MMAGraphState 필드명
visualization_type = result.get("visualization_type")
visualization_data = result.get("visualization_data")
insights = result.get("insights", [])

# 변경 후: MainState 필드명 (동일하므로 변경 없을 수 있음)
# final_response, visualization_type, visualization_data, insights 모두 MainState에 존재
```

`MainState`의 출력 필드(`final_response`, `visualization_type`, `visualization_data`, `insights`)가 현재 `MMAGraphState`와 동일한 이름이므로, `service.py`의 결과 추출 로직은 대부분 그대로 유지된다.

```
수정 파일: src/.env
추가:
  MAIN_MODEL=openrouter/google/gemini-3-flash-preview
  SUB_MODEL=openrouter/google/gemini-2.5-flash-lite
```

---

## Step 5: 기존 코드 제거

**목적**: 새 그래프가 정상 동작하는 것을 확인한 후, 더 이상 사용되지 않는 코드를 삭제한다.

```
삭제 대상:
  src/llm/graph/nodes/intent_classifier.py    → Supervisor로 대체
  src/llm/graph/nodes/context_enricher.py     → Conversation Manager로 대체
  src/llm/graph/nodes/result_analyzer.py      → AgentResult.needs_visualization으로 대체

수정 대상:
  src/llm/graph/nodes/__init__.py             → 삭제된 노드 import 제거, 신규 노드 import 추가
  src/llm/graph/schemas.py                    → IntentClassification의 "followup" 값 제거 (또는 스키마 자체 제거)
  src/llm/graph/prompts.py                    → INTENT_CLASSIFIER_PROMPT, CONTEXT_ENRICHER_PROMPT,
                                                 RESULT_ANALYZER_PROMPT 제거
  src/llm/graph/state.py                      → MMAGraphState 제거 (MainState로 완전 교체)
```

---

## Step 6: 프롬프트 작성 및 테스트

**목적**: 각 에이전트의 프롬프트 품질이 전체 시스템 품질을 결정하므로, 마지막에 집중적으로 다듬는다.

### 신규 프롬프트 목록

| 프롬프트 | 파일 | 핵심 내용 |
|---------|------|----------|
| `CONVERSATION_MANAGER_PROMPT` | `graph/prompts.py` | 히스토리 압축 규칙, 대명사 해소 지침, 주제 전환 감지 |
| `SUPERVISOR_PROMPT` | `graph/prompts.py` | 4가지 route 분류 기준, 에이전트 조합 결정 규칙 |
| `FIGHTER_COMPARISON_PROMPT` | `prompts.py` | 비교 SQL 패턴, 공통 상대 조회, 다차원 비교 구조화 |
| `CRITIC_PROMPT` | `graph/prompts.py` | Phase B 정합성 검증 기준, 피드백 형식 |
| `SQL_AGENT_PROMPT` 수정 | `prompts.py` | `needs_visualization` 판단 지시 추가 |

### E2E 테스트 시나리오

```
1. "안녕"
   → CM(패스스루) → SV(general) → direct_response → END

2. "현재 페더급 챔피언은?"
   → CM(패스스루) → SV(mma_analysis) → MMA 분석 → Critic → 텍스트 응답 → END

3. "존 존스 vs 페레이라 비교해줘"
   → CM(패스스루) → SV(fighter_comparison) → Fighter 비교 → Critic → 텍스트+시각화 → END

4. "체급별 KO 승률 Top 5"
   → CM(패스스루) → SV(mma_analysis) → MMA 분석(viz=true) → Critic → 텍스트+시각화 병렬 → END

5. "그러면 승률은?" (히스토리 있음)
   → CM("맥그리거의 UFC 승률은?") → SV(mma_analysis) → MMA 분석 → Critic → 텍스트 → END

6. 잘못된 SQL 결과
   → Critic 실패 → 재시도 → 최대 3회 후 에러 → END
```

---

## 파일 변경 요약

### 신규 생성

| 파일 | 내용 |
|------|------|
| `src/llm/graph/nodes/conversation_manager.py` | 히스토리 압축 + 대명사 해소 |
| `src/llm/graph/nodes/supervisor.py` | LLM 기반 라우팅 + Send() 디스패치 |
| `src/llm/graph/nodes/fighter_comparison.py` | 비교 전용 SQL 에이전트 |
| `src/llm/graph/nodes/critic.py` | 하이브리드 검증 (규칙 + LLM) |

### 수정

| 파일 | 변경 내용 |
|------|----------|
| `src/llm/graph/state.py` | `MainState`, `AgentResult`, `reduce_agent_results` 추가 |
| `src/llm/graph/schemas.py` | `SupervisorRouting`, `CriticValidation` 추가 |
| `src/llm/graph/graph_builder.py` | 전면 재작성 (MainState + Send() 기반) |
| `src/llm/graph/prompts.py` | 4개 프롬프트 추가, 3개 제거 |
| `src/llm/prompts.py` | `FIGHTER_COMPARISON_PROMPT` 추가, `SQL_AGENT_PROMPT` 수정 |
| `src/llm/model_factory.py` | `_parse_model_spec`, `get_main_model`, `get_sub_model` 추가 |
| `src/llm/service.py` | 이중 LLM 초기화, 100턴 상한 |
| `src/config.py` | `MAIN_MODEL`, `SUB_MODEL` 환경변수 |
| `src/llm/graph/nodes/text_response.py` | `agent_results` 입력 + 복수 결과 통합 |
| `src/llm/graph/nodes/visualize.py` | `agent_results` 입력으로 변환 |
| `src/llm/graph/nodes/direct_response.py` | `resolved_query` 입력 조정 |

### 삭제

| 파일 | 대체 |
|------|------|
| `src/llm/graph/nodes/intent_classifier.py` | Supervisor |
| `src/llm/graph/nodes/context_enricher.py` | Conversation Manager |
| `src/llm/graph/nodes/result_analyzer.py` | `AgentResult.needs_visualization` |

### 환경변수

```bash
# src/.env에 추가
MAIN_MODEL=openrouter/google/gemini-3-flash-preview
SUB_MODEL=openrouter/google/gemini-2.5-flash-lite
```
