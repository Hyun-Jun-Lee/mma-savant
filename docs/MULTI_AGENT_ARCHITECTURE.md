# MMA Savant 멀티 에이전트 아키텍처 계획

## 현재 구조

```
사용자 질문 → intent 분류 → sql_agent → text_response → 응답
```

단일 그래프에서 모든 로직이 순차 처리되는 구조.

---

## 목표 아키텍처

```
사용자 질문
     ↓
[Conversation Manager] ── 대명사 해소, 맥락 보완, 히스토리 관리 (SUB_MODEL)
     ↓
[Supervisor] ── LLM 기반 라우팅, 질문 분해 (SUB_MODEL)
     │
     ├─ general ──→ [direct_response] → END  (fast path, Supervisor 직접 처리)
     │
     ├─ 분석 ────→ [MMA 분석 에이전트] ──────────────────┐
     ├─ 비교 ────→ [Fighter 비교 에이전트] ───────────────┤
     ├─ 복합 ────→ [MMA 분석] + [Fighter 비교] (병렬) ───┤
     └─ 전망 ────→ [MMA 분석] + [Enrichment] (병렬) ─────┤
                                                         ↓
                                              [Critic Agent] (SUB_MODEL)
                                                   ↓ (실패 시 최대 3회 재시도)
                                              ┌────┴────────────────────────┐
                                              ↓                            ↓
                                        [텍스트 응답]            [시각화 에이전트]
                                        (항상 실행)    (needs_visualization=true일 때만)
                                        (MAIN_MODEL)            (SUB_MODEL)
                                              ↓         ↓
                                              └────┬────┘
                                                   ↓
                                               최종 응답
```

---

## 확정된 설계 결정

| 항목 | 결정 | 근거 |
|------|------|------|
| Critic 전략 | 하이브리드 (규칙 → LLM), 최대 3회 재시도 | 규칙으로 처리 가능한 4/5 항목은 LLM 없이 즉시 검증, 의미적 정합성만 SUB_MODEL |
| Supervisor 라우팅 | LLM 기반 + `Send()` API 동적 fan-out | 유연한 질문 분류, 복합 질문의 병렬 에이전트 활성화 |
| 에이전트 결과 통합 | `AgentResult` 통합 스키마 + `operator.add` reducer | 병렬 에이전트 결과 자동 합산, 에이전트 추가 시 state 변경 불필요 |
| general 질문 | fast path (Supervisor → direct_response) | 불필요한 에이전트 호출 방지 |
| Enrichment Agent | 인터페이스만 설계, 구현은 Phase 5 | 외부 소스(웹 검색 유력) 구체화 후 |
| 시각화 전략 | 텍스트 항상 생성 + 시각화 조건부 병렬 (`Send()` 기반) | 텍스트 응답 보장, 시각화 실패 내성 |
| 시각화 판단 주체 | SQL 에이전트가 `AgentResult.needs_visualization` 출력 | result_analyzer 제거, SQL 결과를 가장 잘 아는 에이전트가 의미적 판단 |
| reasoning 재사용 | 단일 에이전트 시 reasoning → final_response 직접 사용 | MAIN_MODEL 호출 1회 절약 (비용 + 속도) |
| 모델 구분 | `{provider}/{model_name}` 형식 환경변수 | MAIN/SUB가 서로 다른 프로바이더 사용 가능, 기존 `LLM_PROVIDER`와 공존 |
| 프론트엔드 | 인터페이스 변경 없음 | 중간 상태 스트리밍 불필요, 백엔드 내부만 변경 |

---

## 에이전트 상세 설계

### 1. Conversation Manager (대화 관리 에이전트)

**역할**: 멀티턴 대화의 맥락을 전문적으로 관리
**모델**: SUB_MODEL

**담당 기능**:
- 대화 히스토리 요약 및 압축 (토큰 절약)
- 대명사 해소 ("그 선수" → "코너 맥그리거")
- 맥락 기반 질문 보완 ("승률은?" → "코너 맥그리거의 UFC 승률은?")
- 주제 전환 감지 및 히스토리 리셋 판단
- 불필요한 히스토리 정리로 하위 에이전트에 깔끔한 입력 전달

**입력**: 사용자 원본 메시지 + 대화 히스토리
**출력**: `resolved_query` + 압축된 `messages` (resolved_query를 HumanMessage로 추가)

**`resolved_query`의 하위 에이전트 전파**:
Conversation Manager는 `resolved_query`를 별도 필드로 설정하는 동시에, `messages`에 HumanMessage로 추가한다.
이렇게 하면 `create_react_agent` 기반 에이전트(MMA 분석, Fighter 비교)는 코드 변경 없이
`messages`의 최신 HumanMessage에서 맥락이 해소된 질문을 읽는다.

```python
async def conversation_manager_node(state, llm) -> dict:
    resolved_text = ...  # LLM으로 맥락 해소

    return {
        "resolved_query": resolved_text,                    # Supervisor, Critic용
        "messages": [HumanMessage(content=resolved_text)],  # SQL 에이전트용 (add_messages로 추가)
    }
```

| 소비자 | 읽는 필드 | 이유 |
|--------|----------|------|
| Supervisor | `resolved_query` | 라우팅 판단에 완전한 단일 문장 필요 |
| MMA 분석 / Fighter 비교 | `messages` (최신 HumanMessage) | `create_react_agent`가 messages를 입력으로 사용 |
| Critic | `resolved_query` | 질문-결과 정합성 검증에 완전한 질문 필요 |
| 텍스트 응답 | `resolved_query` | 사용자 질문에 맞는 답변 구조화 |

**히스토리 압축 전략**:
단순 개수 슬라이싱이 아닌, 지능적 압축을 적용한다.
- **최근 3턴 (6 메시지)**: 원본 그대로 유지 — 직전 맥락의 정확성 보장
- **그 이전 대화**: LLM이 요약문으로 압축 — 토큰 절약하면서 맥락 유지
- **주제 전환 감지 시**: 이전 주제 히스토리를 요약 1문장으로 축소

```
예: 20턴 대화 중 현재 질문이 "그러면 승률은?"
  → 1~17턴: "사용자가 맥그리거의 체급, KO 기록, 최근 경기에 대해 질문함" (요약)
  → 18~20턴: 원본 메시지 유지
  → resolved_query: "코너 맥그리거의 UFC 승률은?"
```

**`service.py` 히스토리 상한**:
현재 `service.py`의 10개 슬라이딩 윈도우는 제거한다.
Conversation Manager가 히스토리 압축의 주체이므로, `service.py`에는
극단적 상황 방지를 위한 **최대 100턴 상한만 유지**한다.

```python
# service.py — 변경 후
if len(messages) > 100:
    messages = messages[-100:]  # 안전 상한만 유지
```

**기대 효과**:
- 하위 에이전트들이 항상 완전한 질문을 받으므로 정확도 향상
- 히스토리 관리 중앙화로 토큰 사용 최적화
- 긴 대화에서도 맥락 유실 방지

---

### 2. Supervisor (라우팅 에이전트)

**역할**: LLM 기반으로 질문을 분석하고 적절한 에이전트로 라우팅
**모델**: SUB_MODEL

**담당 기능**:
- Conversation Manager가 보완한 질문을 LLM으로 분석
- 필요한 에이전트 조합 결정 (structured output)
- 병렬 실행 가능한 에이전트 식별
- general 질문은 fast path로 direct_response 직접 처리

**라우팅 분류**:
```python
class SupervisorRouting(BaseModel):
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    agents: list[str]       # 활성화할 에이전트 목록
```

**라우팅 규칙**:

| 질문 유형 | route | 활성화 에이전트 |
|----------|-------|--------------|
| 일반 대화, MMA 상식 | general | (없음, 직접 응답) |
| 단일 선수 스탯 | mma_analysis | MMA 분석 |
| 선수 비교 | fighter_comparison | Fighter 비교 |
| 복합 질문 | complex | MMA 분석 + Fighter 비교 |
| 전망/예측형 | complex | MMA 분석 + Enrichment |

**동적 라우팅 구현 — LangGraph `Send()` API**:

`add_conditional_edges`는 컴파일 타임에 라우팅 맵이 고정되므로, `agents: list[str]`의 동적 조합을 처리할 수 없다.
LangGraph 0.5.x의 `Send()` API로 런타임 동적 fan-out을 구현한다.

```python
from langgraph.constants import Send

def supervisor_dispatch(state: MainState) -> list[Send]:
    """Supervisor 라우팅 결과에 따라 에이전트를 동적으로 활성화"""
    route = state["route"]

    if route == "general":
        return [Send("direct_response", state)]

    # 단일 또는 복수 에이전트를 동적으로 활성화
    return [Send(agent, state) for agent in state["active_agents"]]

main_graph.add_conditional_edges("supervisor", supervisor_dispatch)
```

**Fan-in (병렬 결과 합류)**:
`Send()`로 병렬 활성화된 에이전트들은 `agent_results: Annotated[list[AgentResult], operator.add]` reducer를 통해
결과가 자동 합산된다. 모든 병렬 에이전트가 완료되면 다음 노드(critic)로 진행한다.

```
supervisor ──Send("mma_analysis")──→ mma_analysis ──┐
           └─Send("fighter_comparison")─→ fighter_comparison ─┤→ (reducer 합산) → critic
```

---

### 3. MMA 분석 에이전트 (통합)

**역할**: Striking, Grappling, 일반 스탯을 포함한 종합 MMA 데이터 분석
**모델**: MAIN_MODEL

**담당 기능**:
- 단일 선수 스탯 조회 및 분석
- Striking 지표 분석 (유효타격률, KO/TKO 패턴, 부위별 타격 등)
- Grappling 지표 분석 (테이크다운 성공률, 서브미션 시도/성공, 컨트롤 타임 등)
- 체급별/시대별 트렌드 분석
- 전적 조회 및 경기 히스토리

**입력**: Conversation Manager가 보완한 질문
**출력**: `AgentResult` (통합 스키마, MainState의 `agent_results`에 reducer로 합산)

**시각화 판단 책임**:
SQL 결과를 생성하는 시점에 데이터의 시각화 적합성을 함께 판단.
기존 `result_analyzer` 노드(규칙 기반)를 제거하고, SQL 결과의 맥락을 가장 잘 이해하는 이 에이전트가 의미적으로 판단.

**노드 반환 형태**:
```python
# mma_analysis_node가 반환하는 dict (reducer가 자동 합산)
return {
    "agent_results": [{
        "agent_name": "mma_analysis",
        "query": "SELECT ...",
        "data": [...],
        "columns": [...],
        "row_count": 10,
        "needs_visualization": True,   # 시각화 필요 여부 판단
        "reasoning": "...",            # 자연어 분석 (텍스트 응답 재사용 가능)
    }],
}
```

---

### 4. Fighter 비교 에이전트

**역할**: 2명 이상의 선수를 다각도로 비교 분석
**모델**: MAIN_MODEL

**담당 기능**:
- 선수 간 스탯 비교 (Striking, Grappling, 전적 등)
- 스타일 매치업 분석 (스트라이커 vs 그래플러 등)
- 공통 상대 전적 비교
- 체급/연령/경력 등 메타 데이터 비교
- 상대 전적 (직접 대결 기록)

**입력**: 비교 대상 선수 목록 + 비교 관점
**출력**: `AgentResult` (통합 스키마, `agent_name="fighter_comparison"`)

**시각화 판단**: MMA 분석 에이전트와 동일하게 `AgentResult.needs_visualization`으로 판단.

**활용 시나리오**:
- "존 존스 vs 알렉스 페레이라 비교해줘"
- "라이트급 상위 5명의 테이크다운 방어율 비교"
- "맥그리거와 올리베이라 중 누가 스트라이킹이 더 나아?"

---

### 5. Critic Agent (검증 에이전트)

**역할**: SQL과 분석 결과의 품질을 독립적으로 검증
**모델**: 하이브리드 (규칙 기반 + SUB_MODEL)

**하이브리드 검증 전략**:
검증 체크리스트 중 대부분은 규칙 기반으로 처리 가능하며, LLM은 의미적 판단에만 사용한다.
매번 LLM을 호출하면 응답 속도에 1~3초가 추가되므로, 규칙 기반 검증을 먼저 수행하고
통과한 경우에만 LLM으로 질문-결과 정합성을 검증한다.

```
Phase A (규칙 기반, LLM 불필요):
  [ ] SQL 문법 유효성 — sqlparse 등으로 구문 검사
  [ ] 참조 테이블/컬럼 존재 확인 — DB 스키마 메타데이터 대조
  [ ] 결과 값 범위 타당성 — 승률 0~100%, 음수 체크 등
  [ ] NULL/빈 결과 처리 적절성 — row_count == 0 감지

Phase B (LLM 기반, Phase A 통과 시에만 실행):
  [ ] 질문-결과 정합성 — 질문한 선수/체급/기간과 결과 일치 여부
```

**입력**: `agent_results` (통합 스키마 리스트) + `resolved_query`
**출력**: 검증 통과 여부 + 피드백 (실패 시) + `retry_count` 증가

**재시도 정책**:
- 최대 재시도 횟수: **3회**
- Critic이 실패를 반환할 때 `retry_count += 1`을 state에 기록
- Critic 실패 → 피드백을 포함하여 SQL Agent에 재생성 요청
- 3회 모두 실패 시 → `final_response`에 에러 메시지를 설정하고 END로 직행
- 재시도 루프: `sql_agent → critic → (실패) → sql_agent → critic → ...`

**재시도 흐름 (LangGraph 구현)**:
```
sql_agent → critic ─(통과)─→ response_fanout (텍스트 + 시각화)
                   └─(실패, retry < 3)─→ sql_agent (피드백 포함)
                   └─(실패, retry >= 3)─→ END (에러 응답)
```

```python
def critic_route(state: MainState) -> str:
    if state["critic_passed"]:
        return "response"
    if state["retry_count"] >= 3:
        return "error"
    return "retry"

main_graph.add_conditional_edges("critic", critic_route, {
    "response": "response_fanout",
    "retry": "sql_agent",
    "error": END,
})
```

**에러 시 state 설정** (Critic 3회 실패):
```python
# critic_node에서 retry >= 3일 때
return {
    "critic_passed": False,
    "final_response": "분석 결과의 품질 검증에 실패했습니다. 질문을 더 구체적으로 바꿔주세요.",
    "visualization_type": None,
    "visualization_data": None,
}
```
`service.py`는 `final_response`가 존재하고 `visualization_type`이 None이면
텍스트 전용 응답으로 처리하므로 기존 프론트엔드 인터페이스와 호환된다.

---

### 6. 텍스트 응답 에이전트

**역할**: 자연스러운 한국어 분석 텍스트 생성
**모델**: MAIN_MODEL

**실행 조건**: Critic 통과 후 **항상 실행**

**담당 기능**:
- SQL 결과를 기반으로 분석 텍스트 작성
- 데이터 해석 및 인사이트 도출
- 사용자 질문에 맞는 답변 구조화

**입력**: `agent_results` + `resolved_query`
**출력**: `final_response` (최종 텍스트 응답)

**reasoning 재사용 최적화**:
단일 에이전트 실행 시 (`agent_results` 길이가 1), 해당 에이전트의 `reasoning` 필드가 충분한 품질이면
MAIN_MODEL 호출을 생략하고 그대로 `final_response`로 사용한다.
복수 에이전트 병렬 실행 시에는 각 reasoning을 합산하여 MAIN_MODEL에 전달, 통합 텍스트를 생성한다.

```python
async def text_response_node(state: MainState, llm) -> dict:
    results = state["agent_results"]

    if len(results) == 1 and results[0]["reasoning"]:
        # 단일 에이전트 → reasoning 재사용 (LLM 호출 생략)
        return {"final_response": results[0]["reasoning"]}

    # 복수 에이전트 → 통합 텍스트 생성 (LLM 호출)
    combined_input = _merge_agent_results(results, state["resolved_query"])
    response = await llm.ainvoke(combined_input)
    return {"final_response": response.content}
```

---

### 7. 시각화 에이전트

**역할**: 데이터 특성에 맞는 최적의 시각화 생성
**모델**: SUB_MODEL

**실행 조건**: Critic 통과 후, **SQL 에이전트의 `needs_visualization=true`인 경우에만 실행** (텍스트 응답과 병렬)

**담당 기능**:
- 데이터 특성 분석 (시계열, 비교, 분포, 순위 등)
- 최적 차트 타입 자동 선택
  - 비교 → Bar Chart
  - 시계열 → Line Chart
  - 분포 → Pie/Radar Chart
  - 순위 → Horizontal Bar
  - 다차원 비교 → Radar Chart
- 프론트엔드 차트 라이브러리(Recharts) 스펙 생성
- 인터랙티브 요소 결정 (툴팁, 필터, 드릴다운 등)
- 반응형 레이아웃 고려

**입력**: 분석 결과 데이터 + 질문 맥락
**출력**: 차트 타입 + 데이터 스펙 + 설정 옵션

**병렬 실행 전략 (Send() 기반)**:

Critic 통과 후, `response_fanout` 노드에서 `Send()`로 텍스트와 시각화를 동시에 활성화한다.

```python
def response_fanout(state: MainState) -> list[Send]:
    """텍스트 응답은 항상, 시각화는 조건부로 활성화"""
    sends = [Send("text_response", state)]  # 항상 실행

    needs_viz = any(r["needs_visualization"] for r in state["agent_results"])
    if needs_viz:
        sends.append(Send("visualization", state))

    return sends

main_graph.add_conditional_edges("critic", critic_route, {
    "response": "response_fanout",
    ...
})
main_graph.add_conditional_edges("response_fanout", response_fanout)
```

```
response_fanout ──Send("text_response")────→ text_response ──┐
                └─Send("visualization") (조건부)→ visualization ─┤→ END
```

- 텍스트 응답은 항상 보장되므로 "빈 응답" 상황 없음
- 시각화 에이전트가 실패해도 텍스트 응답은 이미 완성
- 시각화가 필요한 경우 텍스트와 동시 생성으로 응답 속도 향상

---

### 8. Enrichment Agent (데이터 보강 에이전트) — 인터페이스 설계만

**역할**: DB에 없는 외부 정보로 분석을 보강
**모델**: SUB_MODEL
**상태**: Phase 5에서 구현 예정, 현재는 인터페이스만 설계

**인터페이스 정의**:
```python
class EnrichmentRequest(BaseModel):
    """Enrichment Agent 입력"""
    query: str                    # 보강이 필요한 질문
    entities: list[str]           # 관련 선수명/이벤트명
    enrichment_type: Literal["news", "schedule", "odds", "general"]

class EnrichmentResult(BaseModel):
    """Enrichment Agent 출력"""
    source: str                   # 데이터 출처
    data: dict                    # 보강 데이터
    confidence: float             # 신뢰도 (0.0~1.0)
    retrieved_at: datetime        # 수집 시점
```

**예정 외부 소스** (우선순위):
1. 웹 검색 API (가장 유력)
2. MMA 뉴스 사이트
3. 베팅 오즈 API

**활용 시나리오**:
- "이 선수 다음 경기 전망은?" → DB 스탯 + 최근 뉴스/부상 정보 결합
- "UFC 300 분석해줘" → DB 전적 + 이벤트 정보 + 베팅 오즈

**주의사항**:
- 외부 API 의존성 관리 필요
- 캐싱 전략으로 비용/속도 최적화
- 외부 데이터의 신뢰성 표시 필요

---

## 현재 → 목표 구조 전환: followup 흐름 변화

### 현재 구조의 흐름

```
intent_classifier
  ├─ general    → direct_response → END
  ├─ sql_needed → sql_agent → result_analyzer → visualize/text_response → END
  └─ followup   → context_enricher → sql_agent → result_analyzer → visualize/text_response → END
```

- `intent_classifier`가 히스토리 존재 여부로 intent를 보정
  - 히스토리 있음 + sql_needed → **강제로 followup으로 보정**
  - 히스토리 없음 + followup → **강제로 sql_needed로 보정**
- `context_enricher`가 대화 히스토리를 참조해 후속 질문을 독립 질문으로 재작성
- 재작성된 질문이 sql_agent로 전달

### 현재 구조의 한계

1. **히스토리 있으면 무조건 followup**: 독립적인 새 질문도 context_enricher를 불필요하게 거침
2. **intent 3분기 구조**: followup이라는 별도 경로가 존재하여 그래프 복잡도 증가
3. **맥락 해소가 선택적**: followup일 때만 동작하므로, 첫 질문에서의 모호한 표현은 처리 불가

### 목표 구조에서의 변화

```
[Conversation Manager] → [Supervisor] → 에이전트들
```

**핵심 변경점**:

| 항목 | 현재 | 목표 |
|------|------|------|
| 맥락 해소 시점 | followup일 때만 | **모든 질문에 대해 항상** |
| intent_classifier | 별도 노드 (3분기) | Supervisor에 흡수 |
| context_enricher | followup 전용 노드 | Conversation Manager에 흡수 |
| followup intent | 별도 경로로 존재 | **제거됨** (경로 자체가 불필요) |

**Conversation Manager가 모든 질문을 처리**:
- "그러면 승률은?" → 맥락 필요 → "맥그리거 UFC 승률은?"으로 재작성
- "존 존스 체급이 뭐야?" → 맥락 불필요 → 그대로 통과
- "아까 그 선수랑 비교해줘" → 부분 맥락 → 대명사만 해소

Conversation Manager를 거친 후 **모든 질문이 완전한 형태**이므로, Supervisor는 followup 여부를 고려할 필요 없이 질문 내용 자체로 라우팅만 수행.

### 제거되는 노드/코드

- `intent_classifier.py` → Supervisor 노드로 대체
- `context_enricher.py` → Conversation Manager 노드로 대체
- `result_analyzer.py` → SQL 에이전트가 `needs_visualization` 출력으로 대체
- `IntentClassification.intent`의 `"followup"` 값 → 제거
- `graph_builder.py`의 `route_by_intent`에서 followup 분기 → 제거
- `graph_builder.py`의 `route_by_response_mode` → 제거 (`needs_visualization` 플래그로 대체)

---

## 기술 구현 계획

### 그래프 구조: 함수 노드 기반 (서브그래프 미사용)

모든 에이전트를 **함수 노드**로 등록한다. 서브그래프(`StateGraph.compile()`)로 래핑하지 않는다.

**서브그래프를 사용하지 않는 이유**:
- MMA 분석, Fighter 비교 에이전트는 내부에서 `create_react_agent`를 사용하며, 이것 자체가 이미 LangGraph StateGraph다.
  별도의 `StateGraph(AnalysisState)`로 감싸면 **3계층 state 중첩**(MainState → AnalysisState → ReactAgent 내부 State)이 발생하여
  디버깅이 어려워지고 state 매핑에서 예상치 못한 누락이 생길 수 있다.
- Conversation Manager, Supervisor, Critic, 텍스트 응답, 시각화는 모두 **단일 LLM 호출 또는 규칙 기반 처리**이므로
  함수 노드로 충분하며, 서브그래프의 이점(내부 흐름 제어)이 없다.
- 향후 에이전트 내부 로직이 복잡해지는 경우(예: Enrichment가 웹 검색 → 파싱 → 검증 → 요약의 멀티스텝 파이프라인이 되는 경우)
  **해당 에이전트만 서브그래프로 전환**하면 된다.

```python
main_graph = StateGraph(MainState)

# 모든 에이전트를 함수 노드로 등록 (partial로 LLM 바인딩)
main_graph.add_node("conversation_manager", partial(conversation_manager_node, llm=sub_llm))
main_graph.add_node("supervisor", partial(supervisor_node, llm=sub_llm))
main_graph.add_node("direct_response", partial(direct_response_node, llm=sub_llm))
main_graph.add_node("mma_analysis", partial(mma_analysis_node, llm=main_llm))
main_graph.add_node("fighter_comparison", partial(fighter_comparison_node, llm=main_llm))
main_graph.add_node("critic", partial(critic_node, llm=sub_llm))
main_graph.add_node("text_response", partial(text_response_node, llm=main_llm))
main_graph.add_node("visualization", partial(visualize_node, llm=sub_llm))
```

### 공유 State 설계

#### 에이전트 결과 통합 스키마

병렬 실행되는 에이전트들(MMA 분석, Fighter 비교, Enrichment)은 모두 동일한 `AgentResult` 형태로 결과를 반환한다.
커스텀 reducer로 병렬 결과를 자동 합산하며, Critic 재시도 시에는 이전 실패 결과를 초기화한다.

```python
class AgentResult(TypedDict):
    """각 에이전트의 통합 출력 스키마"""
    agent_name: str                  # "mma_analysis" | "fighter_comparison" | "enrichment"
    query: str                       # 실행한 SQL 쿼리
    data: list[dict]                 # SQL 결과 데이터
    columns: list[str]               # 결과 컬럼명
    row_count: int                   # 결과 행 수
    needs_visualization: bool        # 이 에이전트 결과의 시각화 필요 여부
    reasoning: str                   # 에이전트의 자연어 분석 (텍스트 응답 재사용 가능)


def reduce_agent_results(
    existing: list[AgentResult],
    new: list[AgentResult],
) -> list[AgentResult]:
    """agent_results 커스텀 reducer

    - 빈 리스트 할당(=[]) → 초기화 (Critic 재시도 전 리셋용)
    - 그 외 → 기존 결과에 추가 (병렬 에이전트 합산)
    """
    if not new:          # sql_agent 재시도 전: {"agent_results": []}
        return []
    return existing + new  # 병렬 에이전트 결과 합산


class MainState(TypedDict):
    # 대화 관리
    messages: Annotated[list[BaseMessage], add_messages]
    resolved_query: str              # Conversation Manager 출력

    # 라우팅
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    active_agents: list[str]         # Supervisor가 결정한 활성 에이전트

    # 분석 결과 (커스텀 reducer: 병렬 합산 + 재시도 시 초기화)
    agent_results: Annotated[list[AgentResult], reduce_agent_results]

    # 검증
    critic_passed: bool
    critic_feedback: Optional[str]
    retry_count: int                 # Critic이 실패 반환 시 +1, 최대 3

    # 출력
    final_response: str              # 텍스트 응답 (항상 존재)
    visualization_type: Optional[str]   # 시각화 타입 (조건부)
    visualization_data: Optional[dict]  # 시각화 데이터 (조건부)
    insights: Optional[list[str]]       # 차트 인사이트 (시각화 시에만)

    # 메타데이터
    user_id: int
    conversation_id: int
```

**재시도 시 초기화 흐름**:
```
1차: mma_analysis → agent_results = [result_v1]
     critic 실패 → retry로 라우팅
     sql_agent 재진입 시 {"agent_results": []} 반환 → reducer가 초기화
2차: mma_analysis → agent_results = [result_v2]  ← v1 없이 깨끗한 상태
     critic 통과 → response
```

**시각화 판단 집계**: 후속 노드에서 `any(r["needs_visualization"] for r in state["agent_results"])`로 판단.
하나의 에이전트라도 시각화가 필요하다고 판단하면 시각화 에이전트가 실행된다.

**reasoning 재사용**: 단일 에이전트 실행 시 (mma_analysis 단독 등), 해당 에이전트의 `reasoning`을
텍스트 응답 노드에서 재사용하여 MAIN_MODEL 호출 1회를 절약할 수 있다. 복수 에이전트 병렬 실행 시에는
각 reasoning을 합산하여 텍스트 응답 노드의 입력으로 제공한다.

### 모델 설정

**환경변수 구조**:

현재 프로바이더는 `LLM_PROVIDER` 단일 값으로 결정되지만, MAIN/SUB 모델이 서로 다른 프로바이더를 사용할 수 있다.
`{provider}/{model_name}` 형식의 환경변수로 프로바이더와 모델을 동시에 지정한다.

```bash
# .env
# 형식: {provider}/{model_name}
# provider: openrouter | anthropic | openai
MAIN_MODEL=openrouter/google/gemini-3-flash-preview
SUB_MODEL=openrouter/google/gemini-2.5-flash-lite

# 같은 프로바이더 내에서 모델만 다르게 사용하는 경우 (가장 일반적):
MAIN_MODEL=openrouter/google/gemini-3-flash-preview
SUB_MODEL=openrouter/google/gemini-2.5-flash-lite

# 서로 다른 프로바이더를 사용하는 경우:
MAIN_MODEL=anthropic/claude-sonnet-4-5-20250929
SUB_MODEL=openrouter/google/gemini-2.5-flash-lite
```

```python
# model_factory.py 확장
def _parse_model_spec(spec: str) -> tuple[str, str]:
    """환경변수에서 프로바이더와 모델명을 분리

    'openrouter/google/gemini-3-flash-preview'
      → ('openrouter', 'google/gemini-3-flash-preview')
    'anthropic/claude-sonnet-4-5-20250929'
      → ('anthropic', 'claude-sonnet-4-5-20250929')
    """
    parts = spec.split("/", 1)  # 첫 번째 / 기준으로만 분리
    if len(parts) != 2:
        raise ValueError(f"Invalid model spec: {spec}. Expected 'provider/model_name'")
    return parts[0], parts[1]

def get_main_model() -> BaseChatModel:
    """MAIN_MODEL 환경변수로 모델 생성"""
    provider, model_name = _parse_model_spec(Config.MAIN_MODEL)
    return _create_model(provider, model_name)

def get_sub_model() -> BaseChatModel:
    """SUB_MODEL 환경변수로 모델 생성"""
    provider, model_name = _parse_model_spec(Config.SUB_MODEL)
    return _create_model(provider, model_name)
```

**service.py 변경**:
```python
# 현재: 단일 LLM
llm, _ = create_llm_with_callbacks(...)
self._compiled_graph = build_mma_graph(llm)

# 목표: 이중 LLM
main_llm = get_main_model()
sub_llm = get_sub_model()
self._compiled_graph = build_mma_graph(main_llm, sub_llm)
```

**기존 `LLM_PROVIDER` 환경변수와의 공존**:
Phase 1에서는 `LLM_PROVIDER` + `MAIN_MODEL`/`SUB_MODEL` 모두 지원.
`MAIN_MODEL`이 설정되어 있으면 우선 사용, 없으면 기존 `LLM_PROVIDER` 방식으로 폴백.

**에이전트별 모델 배정**:

| 에이전트 | 모델 | 근거 |
|---------|------|------|
| Conversation Manager | SUB_MODEL | 대명사 해소, 요약 등 비교적 단순한 NLP 태스크 |
| Supervisor | SUB_MODEL | 라우팅 분류는 structured output으로 충분 |
| MMA 분석 | MAIN_MODEL | SQL 생성에 충분한 코딩 능력 필요 |
| Fighter 비교 | MAIN_MODEL | 복수 쿼리 생성 및 비교 로직 |
| Critic | SUB_MODEL | 규칙 기반 검증 위주, 판단 범위가 좁음 |
| 텍스트 응답 | MAIN_MODEL | 자연스러운 한국어 분석 텍스트 생성 |
| 시각화 | SUB_MODEL | 차트 타입 선택 + JSON 스펙 생성 |
| Enrichment | SUB_MODEL | 검색 결과 요약 및 정리 |

---

## 프론트엔드 영향

**변경 없음**. 백엔드 내부 아키텍처만 변경.

- WebSocket `final_result` 이벤트 형식 유지
- 에이전트별 중간 상태 스트리밍 없음
- 에러 응답 형식 기존과 동일 (Critic 3회 실패 시에도 동일 에러 형식)
- 시각화 데이터 구조 기존과 동일 (`visualization_type`, `visualization_data`)

---

## 구현 순서

현재 구조에서 최종 아키텍처로 **한 번에 전환**한다.
단계적 도입이 아니므로 중간 State 호환성 문제는 없으며, `MainState` 기반으로 바로 구현한다.
Enrichment Agent는 인터페이스만 설계된 상태이므로 제외하고, 나머지 모든 에이전트를 구현한다.

### Step 1: 인프라 — State, 모델, 스키마

기존 코드를 수정하지 않고 새 파일만 생성하는 단계. 이후 모든 노드가 의존하는 기반.

- `MainState` 정의 (`AgentResult`, `reduce_agent_results` reducer 포함)
- `MAIN_MODEL` / `SUB_MODEL` 환경변수 파싱 (`_parse_model_spec`)
- `get_main_model()` / `get_sub_model()` 팩토리 함수
- `SupervisorRouting` 등 신규 Pydantic 스키마

**산출물**: `state.py` (신규), `model_factory.py` (확장), `schemas.py` (확장)

### Step 2: 개별 노드 구현

각 노드를 독립적으로 구현. 그래프 연결 없이 단위 테스트 가능한 상태로 만든다.

- **Conversation Manager 노드**: 히스토리 압축 + 대명사 해소 + `resolved_query` 반환
- **Supervisor 노드**: `resolved_query` 기반 라우팅 + `SupervisorRouting` structured output
- **MMA 분석 노드**: 기존 `sql_agent_node` 리팩토링 → `AgentResult` 반환 형태로 변환
- **Fighter 비교 노드**: MMA 분석과 동일 구조, 비교 전용 프롬프트 + SQL 패턴
- **Critic 노드**: 규칙 기반 검증(Phase A) + LLM 정합성 검증(Phase B) + `retry_count` 관리
- **텍스트 응답 노드**: reasoning 재사용 로직 + 복수 에이전트 결과 통합
- **시각화 노드**: 기존 `visualize_node` → `agent_results` 입력으로 변환
- **direct_response 노드**: 기존 로직 유지

**산출물**: `nodes/` 디렉토리 내 각 노드 파일

### Step 3: 그래프 조립

Step 2의 노드들을 `MainState` 기반 그래프로 연결.

- `build_mma_graph(main_llm, sub_llm)` 재구현
- `Send()` 기반 Supervisor 동적 라우팅 + fan-in 에지
- Critic 재시도 루프 (conditional edges)
- `response_fanout` → 텍스트 + 시각화 병렬 `Send()`
- general fast path (Supervisor → direct_response → END)

**산출물**: `graph_builder.py` (재작성)

### Step 4: 서비스 레이어 연결

그래프를 실제 서비스에 연결하고 기존 코드를 교체.

- `service.py` 수정: `get_main_model()` + `get_sub_model()` → `build_mma_graph(main_llm, sub_llm)`
- `service.py` 히스토리: 10개 슬라이딩 윈도우 제거, 100턴 상한만 유지
- `MainState` → `final_result` WebSocket 이벤트 변환 로직 확인
- 기존 프론트엔드 인터페이스 호환성 검증

**산출물**: `service.py` (수정), `.env` (MAIN_MODEL/SUB_MODEL 추가)

### Step 5: 기존 코드 제거

새 그래프가 동작 확인된 후 제거.

- `intent_classifier.py` → Supervisor로 대체됨
- `context_enricher.py` → Conversation Manager로 대체됨
- `result_analyzer.py` → `AgentResult.needs_visualization`으로 대체됨
- `IntentClassification` 스키마의 `"followup"` 값
- `MMAGraphState` (기존 state) → `MainState`로 교체 완료

**산출물**: 삭제 대상 파일 제거, import 정리

### Step 6: 프롬프트 작성 및 테스트

각 에이전트의 프롬프트를 작성하고 E2E 테스트.

- Conversation Manager 프롬프트 (맥락 해소 지침)
- Supervisor 프롬프트 (라우팅 분류 기준)
- Fighter 비교 에이전트 프롬프트 (비교 SQL 패턴)
- Critic 프롬프트 (Phase B 정합성 검증 기준)
- E2E 시나리오 테스트:
  - 일반 대화 → general fast path
  - 단일 스탯 질문 → MMA 분석 단독
  - 선수 비교 → Fighter 비교 단독
  - 복합 질문 → 병렬 실행 + fan-in
  - 후속 질문 → Conversation Manager 맥락 해소
  - 잘못된 SQL → Critic 재시도 루프

### Enrichment Agent (보류)

인터페이스만 설계된 상태. 외부 데이터 소스(웹 검색 등)가 구체화된 후 구현한다.
`MainState`의 `active_agents`에 `"enrichment"`를 추가하고 `Send()`로 활성화하면 되므로,
기존 그래프 구조 변경 없이 노드 추가만으로 도입 가능하다.
