# LangGraph StateGraph 마이그레이션 계획

> 멀티턴 대화 + 조건부 시각화 아키텍처로의 전환

## 0. 기획 결정사항

| 항목 | 결정 |
|------|------|
| 프론트엔드 전환 순서 | 백엔드 먼저 수정 → 프론트엔드는 백엔드 방향에 맞춰 후속 수정 |
| MMA 외 질문 처리 | 시스템 프롬프트에서 MMA 전용으로 제한 (별도 `out_of_scope` 분류 없음, `direct_response` 노드가 MMA 외 질문 거절) |
| 시각화 데이터 저장 | `MessageModel.tool_results`에 `visualization_data`를 저장 (원시 SQL 결과가 아닌 가공된 차트 데이터) |
| 스트리밍 UX | 현재와 동일 유지 (`typing` → `response_chunk` → `final_result`), 중간 단계 노출 없음 |
| 에러 메시지 저장 | 에러 발생 시에도 assistant 메시지로 DB에 저장 (후속 질문에서 맥락 유지) |
| 기존 세션 호환 | 기존 1질문-1응답 세션도 열어서 이어서 대화 가능 (멀티턴 소급 적용) |

## 1. 현재 상태 (AS-IS)

### 아키텍처

```
사용자 질문 (WebSocket)
→ ConnectionManager.handle_user_message()
  → LangChainLLMService.generate_streaming_chat_response()
    → AgentManager.process_two_step()
      → Phase 1: _understand_and_collect()  [Legacy ReAct + AgentExecutor]
        → SQL Tool (동기, 이벤트 루프 블로킹)
      → Phase 2: _process_and_visualize()   [직접 LLM 호출, 문자열 결합 프롬프트]
    → 결과 반환
  → WebSocket으로 전송
→ DB에 대화 저장
```

### 핵심 문제

| 문제 | 영향 |
|------|------|
| 1질문-1응답, 히스토리 미활용 | 후속 질문 불가, 매번 독립 쿼리 |
| 모든 질문이 SQL 파이프라인 강제 통과 | 일반 질문도 불필요한 SQL 시도 |
| Legacy `AgentExecutor` (deprecated) | 문자열 파싱 기반, 스트리밍 미지원 |
| 동기 SQL Tool | AsyncIO 이벤트 루프 블로킹 |
| `ainvoke()` 사용 → 가짜 스트리밍 | 전체 완료 후 한 번에 전달 |
| Phase 2 비구조적 프롬프트 | System/Human 구분 없음 |
| `stream_processor.py` 대부분 Dead Code | 이전 버전 잔재 |
| LangGraph 4개 패키지 설치 but 미사용 | 불필요한 의존성 |

### 현재 파일 구조

```
src/llm/
├── langchain_service.py     # 서비스 진입점 (오케스트레이션)
├── agent_manager.py         # Two-Phase 로직 (Phase 1 + Phase 2)
├── model_factory.py         # LLM + Callback 생성 팩토리
├── prompts.py               # Phase 1/2 프롬프트 템플릿
├── stream_processor.py      # 스트리밍 청크 처리 (대부분 Dead Code)
├── chart_loader.py          # 차트 JSON 로딩
├── exceptions.py            # Custom Exception 계층
├── supported_charts.json    # 지원 차트 정의
├── providers/
│   ├── anthropic_provider.py
│   ├── huggingface_provider.py
│   └── openrouter_provider.py
├── callbacks/
│   ├── anthropic_callback.py
│   ├── huggingface_callback.py
│   └── openrouter_callback.py
└── tools/
    ├── __init__.py
    └── sql_tool.py          # 동기 SQL 실행 도구
```

---

## 2. 목표 상태 (TO-BE)

### 아키텍처

```
사용자 질문 + conversation_id (WebSocket)
→ ConnectionManager.handle_user_message()
  → DB에서 대화 히스토리 로드
  → MMAGraph.astream_events(question, history, thread_id)
    → [intent_classifier] 의도 분류
      ├── "general"  → [direct_response] LLM 텍스트 응답 → END
      ├── "sql_needed" → [sql_agent] SQL 실행
      │   → [result_analyzer] 시각화 적합성 판단
      │   ├── visualizable → [visualize] 차트 데이터 생성 → END
      │   └── text_only    → [text_response] 텍스트 분석 → END
      └── "followup" → [context_enricher] 이전 맥락 보강 → sql_agent로 이동
  → 실시간 토큰 스트리밍 (astream_events)
  → DB에 대화 저장
```

### StateGraph 설계

```
                    ┌─────────────────────┐
                    │    intent_classifier │
                    └──────┬──────┬───────┘
                           │      │       │
                  "general"│      │       │"followup"
                           │      │       │
                           ▼      │       ▼
                    ┌──────┐  │  ┌─────────────────┐
                    │direct│  │  │context_enricher  │
                    │resp  │  │  └────────┬─────────┘
                    └──┬───┘  │           │
                       │      │"sql"      │
                       │      ▼           │
                       │  ┌──────────┐    │
                       │  │sql_agent │◄───┘
                       │  └────┬─────┘
                       │       │
                       │  ┌────▼──────────┐
                       │  │result_analyzer │
                       │  └──┬─────────┬──┘
                       │     │         │
                       │ "viz"│    "text"│
                       │     ▼         ▼
                       │ ┌────────┐ ┌─────────┐
                       │ │visualize│ │text_resp│
                       │ └───┬────┘ └────┬────┘
                       │     │           │
                       ▼     ▼           ▼
                    ┌─────────────────────┐
                    │        END          │
                    └─────────────────────┘
```

### State 스키마

```python
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class MMAGraphState(TypedDict):
    # 대화 메시지 (멀티턴 히스토리)
    messages: Annotated[list[BaseMessage], add_messages]

    # 의도 분류 결과
    intent: Literal["general", "sql_needed", "followup"]

    # SQL 실행 결과 (Phase 1)
    sql_result: Optional[dict]  # {query, data, columns, row_count, success}

    # 시각화 판단 결과
    response_mode: Literal["visualization", "text"]

    # 최종 응답
    final_response: Optional[str]
    visualization_type: Optional[str]
    visualization_data: Optional[dict]
    insights: Optional[list[str]]

    # 메타데이터
    user_id: int
    conversation_id: int
```

### 목표 파일 구조

```
src/llm/
├── graph/
│   ├── __init__.py
│   ├── state.py                # MMAGraphState 정의
│   ├── graph_builder.py        # StateGraph 조립 및 컴파일
│   └── nodes/
│       ├── __init__.py
│       ├── intent_classifier.py    # 의도 분류 노드
│       ├── direct_response.py      # 일반 질문 응답 노드
│       ├── sql_agent.py            # SQL 에이전트 노드 (prebuilt ReAct)
│       ├── context_enricher.py     # 후속 질문 맥락 보강 노드
│       ├── result_analyzer.py      # 시각화 적합성 판단 노드
│       ├── visualize.py            # 시각화 데이터 생성 노드
│       └── text_response.py        # 텍스트 분석 응답 노드
├── service.py               # LLM 서비스 (graph 호출 + 스트리밍)
├── model_factory.py         # LLM + Callback 생성 (유지, 정리)
├── prompts.py               # 노드별 프롬프트 (재구성)
├── chart_loader.py          # 차트 JSON 로딩 (유지)
├── exceptions.py            # Custom Exception (유지)
├── supported_charts.json    # (유지)
├── providers/               # (유지)
├── callbacks/               # (유지, 정리)
└── tools/
    ├── __init__.py
    └── sql_tool.py          # async로 전환
```

**삭제 대상:**
- `agent_manager.py` → `graph/nodes/`로 분해
- `langchain_service.py` → `service.py`로 교체
- `stream_processor.py` → 삭제 (Dead Code)

---

## 3. 마이그레이션 단계

### Phase A: 기반 정리 (기존 코드 개선, 그래프 미도입)

**목표:** 그래프 도입 전에 블로킹 이슈와 Dead Code를 정리하여 안정적인 기반 확보

#### A-1. SQL Tool async 전환

**현재:**
```python
# sql_tool.py
def execute_sql_query(query: str) -> str:          # 동기
    with get_readonly_db_context() as session:      # 동기 context manager
        result = session.execute(text(cleaned_query))

Tool(name="execute_raw_sql_query", func=execute_sql_query)  # 동기 바인딩
```

**변경:**
```python
async def execute_sql_query_async(query: str) -> str:
    async with get_async_readonly_db_context() as session:
        result = await session.execute(text(cleaned_query))

# langgraph prebuilt agent는 async tool을 직접 지원
```

**영향 범위:** `sql_tool.py`, `database/connection/postgres_conn.py` (async readonly 추가)

#### A-2. Dead Code 삭제

- `stream_processor.py`에서 미사용 함수 제거 (`validate_streaming_chunk`만 유지)
- 또는 파일 전체 삭제 후 `validate_streaming_chunk`를 필요한 곳으로 이동

#### A-3. Callback 이중 등록 정리

**현재:** LLM 생성 시 + AgentExecutor 생성 시 동일 callback 이중 등록
**변경:** LLM 레벨에서만 등록, 또는 AgentExecutor 레벨에서만 등록

---

### Phase B: StateGraph 구축

**목표:** 새 그래프 구조를 구현하되 기존 서비스와 병행 가능하도록

#### B-1. State 정의

`llm/graph/state.py` 생성:
- `MMAGraphState` TypedDict 정의
- `add_messages` reducer로 멀티턴 히스토리 자동 관리

#### B-2. 노드 구현 (기존 로직 분해)

각 노드는 `(state: MMAGraphState) -> dict` 시그니처를 가짐:

| 노드 | 원본 | 핵심 변경 |
|------|------|----------|
| `intent_classifier` | 신규 | LLM 기반 의도 분류 (핵심 설계 과제 1) |
| `direct_response` | 신규 | 일반 질문에 대한 LLM 직접 응답 |
| `sql_agent` | `agent_manager._understand_and_collect` | `langgraph.prebuilt.create_react_agent` 사용 |
| `context_enricher` | 신규 | 대화 히스토리에서 맥락 추출 (핵심 설계 과제 2) |
| `result_analyzer` | `agent_manager._validate_and_enhance_phase2_result` 일부 | 시각화 적합성 판단 (핵심 설계 과제 3) |
| `visualize` | `agent_manager._process_and_visualize` | 시각화 데이터 생성 (System/Human 메시지 구조화) |
| `text_response` | 신규 | SQL 결과를 텍스트로 분석 |

#### B-3. 조건부 에지 정의

```python
def route_by_intent(state: MMAGraphState) -> str:
    return state["intent"]  # "general" | "sql_needed" | "followup"

def route_by_response_mode(state: MMAGraphState) -> str:
    return state["response_mode"]  # "visualization" | "text"
```

#### B-4. 그래프 조립 및 컴파일

`llm/graph/graph_builder.py`:
```python
from langgraph.graph import StateGraph, START, END

def build_mma_graph(llm) -> CompiledGraph:
    graph = StateGraph(MMAGraphState)

    # 노드 등록
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("direct_response", direct_response_node)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("context_enricher", context_enricher_node)
    graph.add_node("result_analyzer", result_analyzer_node)
    graph.add_node("visualize", visualize_node)
    graph.add_node("text_response", text_response_node)

    # 에지 정의
    graph.add_edge(START, "intent_classifier")
    graph.add_conditional_edges("intent_classifier", route_by_intent, {
        "general": "direct_response",
        "sql_needed": "sql_agent",
        "followup": "context_enricher",
    })
    graph.add_edge("context_enricher", "sql_agent")
    graph.add_edge("sql_agent", "result_analyzer")
    graph.add_conditional_edges("result_analyzer", route_by_response_mode, {
        "visualization": "visualize",
        "text": "text_response",
    })
    graph.add_edge("direct_response", END)
    graph.add_edge("visualize", END)
    graph.add_edge("text_response", END)

    return graph.compile()
```

---

### Phase C: 서비스 계층 교체

**목표:** 새 그래프를 WebSocket 서비스에 연결하고 실시간 스트리밍 구현

#### C-1. 새 서비스 작성

`llm/service.py`:
- `build_mma_graph()`로 컴파일된 그래프를 보유
- `astream_events()`로 실시간 토큰 스트리밍
- 이벤트 타입별 처리: `on_chat_model_stream`, `on_tool_start`, `on_tool_end`

```python
class MMAGraphService:
    def __init__(self):
        self.graph = None
        self.llm = None

    async def initialize(self, provider: str = None):
        llm, callback = create_llm_with_callbacks(...)
        self.graph = build_mma_graph(llm)

    async def stream_response(
        self,
        user_message: str,
        conversation_id: int,
        user_id: int,
        chat_history: list[dict]
    ) -> AsyncGenerator[dict, None]:
        # 히스토리를 BaseMessage로 변환
        messages = self._build_messages(chat_history, user_message)

        # 그래프 실행 + 실시간 스트리밍
        async for event in self.graph.astream_events(
            {"messages": messages, "user_id": user_id, "conversation_id": conversation_id},
            version="v2"
        ):
            chunk = self._process_event(event)
            if chunk:
                yield chunk
```

#### C-2. WebSocket Manager 연동 변경

`api/websocket/manager.py`:
- `LangChainLLMService` → `MMAGraphService`로 교체
- `handle_user_message`에서 DB 히스토리 로드 후 그래프에 전달
- 멀티턴: `conversation_id`가 있으면 기존 세션 히스토리 로드

**핵심 변경:**
```python
# 기존: 히스토리 없이 실행
await self._process_llm_streaming_response(connection_id, content, user_id, db)

# 변경: 히스토리 로드 후 실행
history = await self._load_chat_history(db, conversation_id)
await self._process_graph_streaming(connection_id, content, user_id, db, history)
```

#### C-3. 대화 저장 로직 변경

현재: LLM 성공 후 세션 생성 (`_save_successful_conversation`)
변경:
- 신규 대화: 첫 응답 성공 시 세션 생성 (현재와 동일)
- 기존 대화: `conversation_id`로 기존 세션에 메시지 추가

---

### Phase D: 검증 및 정리

#### D-1. 테스트 작성

| 대상 | 테스트 유형 |
|------|------------|
| 각 노드 함수 | 단위 테스트 (입력 State → 출력 State) |
| 조건부 라우팅 | intent별 경로 검증 |
| 전체 그래프 | 통합 테스트 (일반 질문, SQL 질문, 후속 질문) |
| 스트리밍 | WebSocket 이벤트 수신 검증 |

#### D-2. 기존 코드 삭제

- `langchain_service.py` 삭제
- `agent_manager.py` 삭제
- `stream_processor.py` 삭제
- `pyproject.toml`에서 불필요한 의존성 확인

#### D-3. 프론트엔드 대응

WebSocket 메시지 타입 변경 최소화:
- `response_chunk`, `final_result`, `error` 타입은 유지
- `phase_start` 타입 제거 (그래프가 내부적으로 처리)
- 신규: `intent` 이벤트 (선택적, 디버깅/UX용)

---

## 4. 핵심 설계 과제 및 구현 방법

### 과제 1: 의도 분류기 (Intent Classifier)

**역할:** 사용자 질문을 `general` / `sql_needed` / `followup` 중 하나로 분류

#### 추천 방법: Structured Output (tool_choice 강제)

LLM에게 분류 도구를 정의하고 반드시 호출하도록 강제하는 방식입니다. 프롬프트 기반 분류보다 출력 형식이 보장됩니다.

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

class IntentClassification(BaseModel):
    """사용자 질문의 의도 분류 결과"""
    intent: Literal["general", "sql_needed", "followup"] = Field(
        description="general: MMA 지식/규칙 등 DB 조회 불필요, "
                    "sql_needed: 통계/랭킹/전적 등 DB 조회 필요, "
                    "followup: 이전 대화를 참조하는 후속 질문"
    )
    reasoning: str = Field(
        description="분류 근거를 한 문장으로 설명"
    )

async def intent_classifier_node(state: MMAGraphState) -> dict:
    structured_llm = llm.with_structured_output(IntentClassification)

    # 마지막 사용자 메시지 + 최근 히스토리 요약을 함께 전달
    messages = [
        SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
        *state["messages"][-5:]  # 최근 5개 메시지만
    ]

    result = await structured_llm.ainvoke(messages)
    return {"intent": result.intent}
```

**분류 기준 프롬프트:**

```
당신은 MMA/UFC 데이터 분석 시스템의 의도 분류기입니다.

## 분류 기준

### general (일반 질문)
- MMA/UFC 규칙, 체급 설명, 기술 설명
- 인사, 잡담, 시스템 사용법
- 예: "UFC 체급 종류가 뭐야?", "서브미션이 뭐야?"

### sql_needed (데이터 조회)
- 특정 선수의 전적, 통계, 랭킹
- 비교, 집계, 트렌드 분석
- 예: "존 존스 전적", "KO 승률 Top 10", "2024년 타이틀전 결과"

### followup (후속 질문)
- 이전 대화 내용을 참조 ("그중에서", "좀 더 자세히", "다른 선수는?")
- 대명사로 이전 맥락 지칭 ("그 선수", "위의 결과에서")
- 반드시 이전 대화가 있어야 함 — 대화 히스토리가 비어있으면 sql_needed로 분류

## 중요
- 애매할 경우 sql_needed를 선택 (데이터 기반 답변이 더 정확함)
- 히스토리가 비어있으면 followup은 불가 → general 또는 sql_needed
```

**비용 제어:**
- 분류 전용 모델을 저비용 모델(haiku급)로 설정하거나, 메인 모델의 `max_tokens=50`으로 제한
- 간단한 규칙 기반 pre-filter로 명확한 케이스를 LLM 호출 없이 분류:
  ```python
  # LLM 호출 전 규칙 기반 빠른 분류
  if not state["messages"] or len(state["messages"]) <= 1:
      # 히스토리 없으면 followup 불가
      if has_data_keywords(last_message):  # "전적", "승률", "Top", "랭킹" 등
          return {"intent": "sql_needed"}
  ```

---

### 과제 2: 대화 히스토리 → SQL 컨텍스트 변환

**역할:** 후속 질문에서 "그중", "다른 선수는?" 같은 참조를 실제 SQL 쿼리 가능한 조건으로 변환

#### 추천 방법: Query Rewriting (질문 재작성)

후속 질문을 독립적인 완전한 질문으로 재작성하여 SQL 에이전트에 전달합니다. SQL 에이전트는 변경 없이 재작성된 질문만 받으면 됩니다.

```python
CONTEXT_ENRICHER_PROMPT = """
이전 대화와 사용자의 후속 질문을 분석하여, 독립적으로 이해 가능한 완전한 질문으로 재작성하세요.

## 규칙
1. 대명사와 생략된 맥락을 구체적인 이름/조건으로 대체
2. 이전 SQL 결과에서 언급된 선수명, 조건을 명시적으로 포함
3. 재작성된 질문만 출력 (설명 불필요)

## 예시
이전 대화: "존 존스 전적 알려줘" → [SQL 결과: 28승 1패 ...]
후속 질문: "그중에서 KO로 이긴 건?"
→ 재작성: "존 존스의 KO 승리 기록을 알려줘"

이전 대화: "라이트급 Top 5 알려줘" → [SQL 결과: 마카체프, 올리베이라, ...]
후속 질문: "1위랑 2위 비교해줘"
→ 재작성: "이슬람 마카체프와 찰스 올리베이라의 전적을 비교해줘"
"""

async def context_enricher_node(state: MMAGraphState) -> dict:
    messages = [
        SystemMessage(content=CONTEXT_ENRICHER_PROMPT),
        *state["messages"]  # 전체 대화 히스토리
    ]

    rewritten = await llm.ainvoke(messages)

    # 재작성된 질문을 messages에 추가 (원본 대체가 아닌 보강)
    return {
        "messages": [HumanMessage(content=rewritten.content)]
    }
```

**핵심 포인트:**
- SQL 에이전트는 재작성된 질문을 받으므로 **변경 불필요**
- 이전 SQL 결과(`sql_result`)를 히스토리에 포함해야 맥락이 풍부해짐
- DB에서 히스토리 로드 시 assistant 메시지의 `tool_results` 필드 활용

**히스토리 토큰 관리 (과제 4와 연동):**
- 전체 히스토리를 넣지 않고, 최근 N턴만 전달
- SQL 결과가 클 경우 요약본만 포함

---

### 과제 3: 시각화 적합성 판단

**역할:** SQL 결과를 보고 차트로 보여줄지 텍스트로 답할지 결정

#### 추천 방법: 규칙 기반 + LLM 보조 하이브리드

대부분의 케이스는 데이터 형태만으로 판단 가능합니다. 규칙으로 처리하고, 애매한 경우만 LLM에 위임합니다.

```python
async def result_analyzer_node(state: MMAGraphState) -> dict:
    sql_result = state["sql_result"]

    if not sql_result or not sql_result.get("success"):
        return {"response_mode": "text"}

    data = sql_result.get("data", [])
    columns = sql_result.get("columns", [])
    row_count = sql_result.get("row_count", 0)

    # 규칙 기반 판단
    mode = rule_based_analysis(data, columns, row_count)
    if mode:
        return {"response_mode": mode}

    # 애매한 경우 LLM 판단
    mode = await llm_based_analysis(state)
    return {"response_mode": mode}


def rule_based_analysis(data, columns, row_count) -> str | None:
    """규칙 기반 시각화 적합성 판단"""

    # 텍스트로 응답해야 하는 경우
    if row_count == 0:
        return "text"
    if row_count == 1 and len(columns) <= 3:
        return "text"  # 단일 값 응답 ("존 존스의 승률은 93%")

    # 시각화가 적합한 경우
    if row_count >= 3:
        has_numeric = any(
            isinstance(data[0].get(col), (int, float))
            for col in columns
            if col in data[0]
        )
        if has_numeric:
            return "visualization"

    # 2행이거나 수치 데이터가 없는 경우 → LLM에 위임
    return None
```

**판단 기준 정리:**

| 조건 | 판단 | 이유 |
|------|------|------|
| 0행 | text | 데이터 없음 |
| 1행, 3컬럼 이하 | text | 단순 값 응답 |
| 1행, 4컬럼 이상 | visualization (radar) | 다차원 단일 선수 스탯 |
| 2행, 수치 있음 | visualization (비교) | 1:1 비교 |
| 3행 이상, 수치 있음 | visualization | 랭킹/분포/트렌드 |
| 3행 이상, 수치 없음 | text 또는 table | 텍스트 목록 |

---

### 과제 4: 히스토리 관리 (토큰 제한)

**역할:** 멀티턴에서 대화 히스토리의 크기를 LLM 컨텍스트 윈도우 내로 제어

#### 추천 방법: 슬라이딩 윈도우 + SQL 결과 요약

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

MAX_HISTORY_TURNS = 10     # 최근 N턴 유지
MAX_SQL_RESULT_CHARS = 500 # SQL 결과 요약 최대 길이

def prepare_history_for_graph(
    db_messages: list[dict],
    max_turns: int = MAX_HISTORY_TURNS
) -> list[BaseMessage]:
    """DB에서 가져온 메시지를 LangGraph State용으로 변환"""

    # 최근 N턴만 선택 (1턴 = user + assistant)
    recent = db_messages[-(max_turns * 2):]

    messages = []
    for msg in recent:
        content = msg["content"]

        # assistant 메시지의 SQL 결과가 크면 요약
        if msg["role"] == "assistant" and msg.get("tool_results"):
            content = summarize_with_tool_results(content, msg["tool_results"])

        if msg["role"] == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    return messages


def summarize_with_tool_results(content: str, tool_results: list[dict]) -> str:
    """assistant 메시지에 SQL 결과 요약을 포함"""
    summary_parts = [content[:300]]  # 응답 텍스트 앞부분

    for tr in tool_results[:1]:  # 첫 번째 도구 결과만
        result_str = str(tr.get("result", ""))
        if len(result_str) > MAX_SQL_RESULT_CHARS:
            result_str = result_str[:MAX_SQL_RESULT_CHARS] + "..."
        summary_parts.append(f"\n[SQL 결과 요약: {result_str}]")

    return "\n".join(summary_parts)
```

**전략 정리:**

| 레벨 | 방법 | 대상 |
|------|------|------|
| 기본 | 슬라이딩 윈도우 (최근 10턴) | 모든 노드 |
| SQL 결과 | 문자열 제한 + 요약 | context_enricher, sql_agent |
| intent_classifier | 최근 5턴만 전달 (빠른 분류) | intent_classifier |
| direct_response | 최근 10턴 전체 | direct_response |

**향후 고도화 (필요 시):**
- `tiktoken`으로 정확한 토큰 수 계산 후 잘라내기
- 오래된 대화를 LLM으로 요약하여 1개 SystemMessage로 압축
- 모델의 `context_length`에 따라 `max_turns` 자동 조절

---

## 5. 일정 추정

| Phase | 내용 | 범위 |
|-------|------|------|
| **A** | 기반 정리 (async tool, dead code, callback) | 3개 파일 수정, 1개 삭제 |
| **B** | StateGraph 구축 (state, 7개 노드, 그래프 조립) | 10개 파일 신규 |
| **C** | 서비스 계층 교체 (서비스, WebSocket 연동) | 2개 파일 수정 |
| **D** | 검증 및 정리 (테스트, 기존 코드 삭제) | 테스트 신규, 3개 삭제 |

**의존 관계:** A → B → C → D (순차적)

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 의도 분류 정확도 부족 | 잘못된 경로로 라우팅 | 규칙 기반 pre-filter + LLM 조합, "애매하면 sql_needed" 기본값 |
| 스트리밍 이벤트 호환성 | 프론트엔드 렌더링 깨짐 | 기존 WebSocket 메시지 타입 유지, 이벤트 변환 레이어 |
| LLM 비용 증가 | 의도 분류에 추가 LLM 호출 | 규칙 기반 pre-filter, 분류 전용 저비용 모델 |
| 멀티턴 히스토리 토큰 초과 | LLM 에러 | 슬라이딩 윈도우 + SQL 결과 요약으로 제어 |
