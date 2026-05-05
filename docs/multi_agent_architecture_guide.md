
# Multi-Agent Guide

## 0. 기초 개념 정리

---

### Agent

- LLM을 기반으로 **스스로 판단하고 행동**하는 실행 단위
  - 단순히 질문에 답하는 것을 넘어, 주어진 목표를 달성하기 위해 어떤 Tool을 쓸지, 다음에 무엇을 할지를 스스로 결정

```text
입력(State)
  ↓
Agent (LLM 기반 판단)
  ↓
Tool 호출 또는 결과 반환
```

---

### Node

Graph 안에서 **하나의 실행 단계**를 나타내는 단위
Agent가 될 수도 있고, 단순한 데이터 가공 로직이 될 수도 있음.

```text
Node의 역할:
  - State를 읽는다
  - 로직을 실행한다 (Agent 호출, rule 처리 등)
  - State delta를 반환한다
```

---

### Edge

Node와 Node를 **연결하는 흐름**이다.
다음에 어떤 Node를 실행할지를 결정한다.

```text
1) 고정 Edge (Normal Edge)
   항상 동일한 다음 Node로 이동
   Classifier → Aggregator

2) 조건부 Edge (Conditional Edge)
   조건에 따라 다음 Node가 달라짐
   Router → SQL Agent      (issue_type == "sql")
          → Lock Agent     (issue_type == "lock")
          → CPU Agent      (issue_type == "cpu")
```

### 간단 정리

```text
- Graph: 전체 실행 흐름
- Node:  실행 단계 (Agent 또는 로직)
- Edge:  Node 간 연결 및 분기 조건
- Agent: LLM 기반 판단 주체 (Node 안에 존재)
- Tool:  Agent가 호출하는 기능 단위
```

---


## 1. LLM 기반 시스템의 특성

- LLM은 deterministic rule engine이 아니라 **probabilistic reasoning engine**
- 입력 context와 prompt 구성에 따라 결과가 달라질 수 있음
- context 길이가 길어질수록 핵심 정보가 희석되는 문제 (lost-in-the-middle)
- 하나의 Agent에 많은 역할이 집중될수록:
  - 추론 경로가 불안정해짐
  - 결과 품질 변동성 증가
  - 디버깅 및 테스트 어려움 증가

---

### 기본 아키텍처

```text
User Request
  ↓
Supervisor / Router
  ↓
Domain Agents
  - SQL Agent
  - Lock Agent
  - CPU/OS Agent
  - Space Agent
  ↓
Aggregator
  ↓
HITL (optional)
  ↓
Final Output
```

#### 구성 요소 설명

**1) Supervisor / Router**
- 사용자 요청을 해석하여 적절한 Agent로 분기
- rule 기반 또는 LLM 기반으로 구현 가능

**2) Domain Agents**
- 각 도메인에 특화된 Agent
- 독립적으로 개발 및 테스트 가능

**3) Aggregator**
- 여러 Agent의 결과를 통합
- 충돌 해결
- 결과 품질 평가
- partial failure 처리

**4) HITL (Human-in-the-loop)**
- 자동 판단이 어려운 경우 인간 개입
- 고위험 의사결정 또는 불확실성 높은 결과에서 사용

---


## 2. Agent 설계

- 책임 범위 및 판단 기준 명확히 설정
- 명확한 조건 분기는 rule로 처리하고, LLM 호출은 해석이 필요한 지점에만 사용
- LLM은 모호한 해석과 판단에 집중
- 많은 일을 처리하게 하는 것 보다 예측 가능하게 동작하도록 개발

---

### 2.1 대표적인 개발 패턴

#### 1) Router Pattern

요청을 해석하여 적절한 Agent 또는 Node로 분기

```text
User Request
  ↓
Router (요청 해석 + Agent 선택)
  ↓
SQL Agent / Lock Agent / CPU Agent
```

적합한 상황:
- 요청 유형이 명확히 구분될 때
- 각 Agent가 독립적으로 처리 가능할 때

주의:
- 오분류 가능성이 항상 존재하므로 fallback 전략이 필수
  - confidence threshold 기반 분기 (low confidence 시 fallback)
  - fallback route 정의 (default agent 또는 rule 기반 처리)

---

#### 2) Planner–Executor Pattern

실행 계획 수립과 실행을 분리, Planner가 어떤 Agent/Tool을 어떤 순서로 쓸지 결정하고, Executor가 이를 수행하는 구조

```text
User Request
  ↓
Planner (계획 수립 + Agent/Tool 선택)
  ↓
Executor (계획 실행)
  ↓
Result
```

적합한 상황:
- 실행 단계가 요청 시점에 동적으로 결정되어야 할 때
  - ex) "이 에러를 분석하려면 어떤 Agent를 어떤 순서로 써야 할지 사전에 알 수 없는 경우"

주의:
- Planner LLM 호출이 추가되므로 latency 및 비용 증가
- Planner의 계획이 잘못되면 Executor 전체가 잘못된 방향으로 실행됨
- Planner 출력은 반드시 Structured Output으로 고정할 것

---

#### 3) Evaluator–Refiner Pattern

생성된 결과를 평가하고, 기준 미달 시 재생성

```text
Generate
  ↓
Evaluate (기준 충족 여부 판단)
  ↓ 미달
Refine (재생성)
  ↓ 통과
Result
```

적합한 상황:
- 출력 품질 기준이 명확히 존재할 때
- 재생성 비용이 허용 가능한 수준일 때

주의:
- 최대 retry 횟수 설정 필수 (권장: 2~3회) — 미설정 시 무한 루프 위험
- Evaluator의 평가 기준(rubric)이 불명확하면 refinement가 오히려 품질을 저하시킬 수 있음
- Evaluator 자체도 LLM 호출이므로 비용/latency 고려 필요

---

### 2.2 Node vs Tool

**Node**
- workflow의 실행 단계
- State를 읽고, 다음 흐름을 결정하고, State delta를 반환
- Agent 간 실행 순서와 조건 분기를 담당

**Tool**
- 단일 기능을 수행하고 결과를 반환
- DB 조회, API 호출, 파일 읽기 등 외부 I/O 담당

| | Node | Tool |
|---|---|---|
| **역할** | 흐름 결정 | 기능 수행 |
| **State 접근** | O (읽기/쓰기) | X |
| **외부 I/O** | X | O |
| **예시** | Router, Classifier, Aggregator | execute_sql_query, get_process_list |

```text
# 판단 기준 한 줄 요약
"다음에 무엇을 실행할지 결정하는가?" → Node
"외부 시스템에 요청하고 결과를 반환하는가?" → Tool
```

#### Node 설계 가이드

- 하나의 Node는 하나의 흐름 결정만 담당한다
- State를 직접 수정하지 않고 delta만 반환한다 (순수 함수 지향)
- 외부 I/O는 Node 내부에서 직접 수행하지 않는다 → Tool로 분리

```python
# 좋은 예: 순수 함수에 가까운 Node
def classify_node(state: State, config: Config) -> dict:
    issue_type = classify(state["query"])  # Tool 호출
    return {"issue_type": issue_type}      # delta만 반환

# 나쁜 예: Node 내부에서 외부 I/O 직접 수행
def classify_node(state: State, config: Config) -> dict:
    result = requests.post("http://db/query", ...)  # ❌ Tool로 분리해야 함
    return {"issue_type": result}
```


#### Tool 설계 가이드 (네이밍 & Docstring)

LLM은 tool의 **이름**과 **description**만 보고 어떤 tool을 호출할지 결정한다.
따라서 tool 설계는 코드 품질이 아니라 **LLM의 tool selection 정확도**를 직접 좌우한다.

**네이밍 원칙:**

```text
- 동사 + 목적어 형태: execute_sql_query, get_process_list, check_lock_status
- 모호한 이름 금지: run(), do_task(), handle(), process()
- Agent 간 tool 이름 중복 금지 (같은 이름이 다른 동작을 하면 혼란 유발)
- 보편적으로 통용되지 않는 축약어 지양
```

**Docstring 원칙:**

```python
@tool
def execute_sql_query(query: str) -> str:
    """Execute a SQL query against the PostgreSQL database and return results.

    Use this tool when you need to retrieve data from the database.
    Input must be a valid SQL SELECT statement.
    Returns: JSON string of query results (max 100 rows).

    Do NOT use for INSERT/UPDATE/DELETE operations.
    """
```

핵심 요소:
- **첫 줄**: tool이 무엇을 하는지 한 문장으로
- **언제 사용하는지**: LLM이 선택 판단을 할 수 있도록
- **파라미터 설명**: 어떤 형태의 입력을 기대하는지
- **출력 형태**: 무엇이 반환되는지
- **금지 사항**: 이 tool로 하면 안 되는 것

주의 사항:
- 여러 기능을 하나의 tool에 합친 경우 → 의도와 다른 호출 발생
- 실패 시 반환값 미정의 → LLM이 에러를 데이터로 오인

---

### 2.3 Agent 분리 기준

Agent는 하나의 책임만 가져야 한다.

**① 도메인 기반**
- 서로 다른 전문 지식이 필요한 영역으로 분리
- 예) SQL Agent (쿼리 분석) / Lock Agent (잠금 탐지) / CPU Agent (리소스 분석)

**② 데이터 소스 기반**
- 접근하는 시스템이 다를 때 분리
- 예) PostgreSQL 조회 Agent vs OS 메트릭 수집 Agent

**③ 판단 목적 기반**
- 내리는 판단의 성격이 다를 때 분리
- 예) 원인 분석 Agent vs 해결책 추천 Agent

실행 순서 기준, 담당자 기준 분리 X

#### Agent 분리 판단

- system prompt에 서로 다른 도메인의 지시사항이 혼재하기 시작할 때

- 서로 다른 tool set이 필요할 때
  예) SQL Agent는 DB tool, Lock Agent는 OS tool

- 실패 격리가 필요할 때 (한쪽 실패가 다른 쪽 결과에 영향을 줌)

- 독립적으로 테스트/배포하고 싶을 때

---

### 2.4 상태와 데이터 흐름 관리

---

#### 2.4.1 State 관리

State는 Agent와 Node 사이에서 공유되는 데이터

State가 커질수록 Agent 간 결합도가 높아지고 디버깅이 어려워지니 필요한 만큼만, 명시적으로 관리

- 필요한 데이터만 포함
- 명시적 schema를 사용
- 중간 결과와 최종 결과를 분리
  - 각 Agent 출력 검증 + 디버깅 쉬움
- Agent 간 전달 시 원본 데이터 전체가 아닌 필요한 필드만 추출하여 전달

```python
class DiagnosisState(TypedDict):
    # 입력 (변경 없음)
    query: str

    # 중간 결과 (각 Agent 출력)
    issue_type: str
    agent_results: list[AgentResult]

    # 최종 결과 (Aggregator 출력)
    final_summary: str
```

---

#### 2.4.2 Reducer

Reducer는 병렬 실행된 여러 Agent의 결과를 State에 병합하는 방식으로
fan-out / fan-in 구조에서 각 Agent의 결과를 누적할 때 사용한다.

```python
# LangGraph에서 Reducer 정의 예시
class DiagnosisState(TypedDict):
    # operator.add: 각 Agent 결과가 추가될 때마다 리스트에 누적
    agent_results: Annotated[list, operator.add]
```

```text
# 동작 방식
SQL Agent 결과   ─┐
Lock Agent 결과  ─┼─→ Reducer → agent_results: [sql_result, lock_result, cpu_result]
CPU Agent 결과   ─┘
```

---

#### 2.4.3 Structured Output

LLM 출력을 schema 기반으로 고정


```python
from pydantic import BaseModel
from typing import Literal

class SQLAnalysisResult(BaseModel):
    issue_type: Literal["slow_query", "lock", "index_missing"]
    confidence: float          # 0.0 ~ 1.0
    evidence: list[str]        # 판단 근거
    recommendation: str        # 권장 조치

# LLM에 schema 강제 적용
llm.with_structured_output(SQLAnalysisResult)
```

---

#### 실패 처리


```python
try:
    result = llm.with_structured_output(SQLAnalysisResult).invoke(prompt)
except OutputParserException:
    # 1) 재시도 (최대 N회)
    # 2) fallback schema로 전환 (필드 수를 줄인 간소화 버전)
    # 3) partial response로 처리
```

---

## 3. Context Engineering

Agent의 품질은 모델 선택이나 코드 로직보다 **LLM에게 무엇을 어떻게 보여주는가**에 의해 결정

Context Engineering = LLM에게 주어지는 입력 데이터의 설계 + 해석 규칙의 명시

같은 모델, 같은 Agent 구조라도 context 구성에 따라 성능 크게 다름.

Prompt Engineering이 "LLM에게 무엇을 어떻게 지시할까"라면,
Context Engineering은 "그 지시를 뒷받침할 데이터를 어떻게 구성할까"이다.

---

### 3.1 Context 구성 요소


```text
┌─────────────────────────────────┐
│ 1. System Prompt (역할, 규칙)      │
├─────────────────────────────────┤
│ 2. Reference Data (스키마, 문서)    │
├─────────────────────────────────┤
│ 3. Dynamic Context (이전 결과, 상태) │
├─────────────────────────────────┤
│ 4. User Input (현재 요청)          │
└─────────────────────────────────┘
```


**1) System Prompt**
- Agent의 역할과 책임을 명확히 정의
- 판단 기준(decision criteria)을 명시적으로 제공
- 금지 사항(negative instructions)을 포함

**2) Reference Data**
- DB 스키마, API 문서, 도메인 규칙 등 정적 참조 자료
- 전체를 넣지 말고 필요한 부분만 선별 (context window 절약)
- 관련 없는 정보는 noise → 판단 품질 저하

**3) Dynamic Context**
- 이전 Agent의 실행 결과, Tool 호출 결과, 대화 히스토리
- 양이 많으면 요약 필요

**4) User Input**
- 원본 질문
- 모호한 입력은 Agent 앞단에서 정제

---

### 주의사항

- 필요 최소 정보만 제공

  ```text
  전체 DB 스키마 50개 테이블 → LLM이 관련 테이블을 찾아야 함

  질문과 관련된 5개 테이블 스키마만 → 즉시 올바른 쿼리 작성
  ```


- 구조화된 형태로 전달

  ```text
  "locks 테이블에 id, pid, query_time, status 컬럼이 있고..."

  {
    "table": "locks",
    "columns": [
      { "name": "id",         "type": "int",     "description": "PK" },
      { "name": "pid",        "type": "int",     "description": "잠금 유발 프로세스 ID" },
      { "name": "query_time", "type": "float",   "description": "쿼리 실행 시간 (초)" },
      { "name": "status",     "type": "varchar", "description": "waiting / held" }
    ]
  }
  ```

- 시간/상태 정보를 주입

  LLM은 현재 시간, 시스템 상태를 모르니 판단에 필요한 명시적으로 제공


- Lost-in-the-Middle 대응
  - 가장 중요한 규칙/데이터를 앞과 끝에 배치
  - context가 길면 요약/압축 후 전달
  - 반복 강조: 핵심 규칙을 prompt 앞과 끝에 재언급


---


## 4. Agent Interface 표준화

### 4.1 필요 이유 (의존성 최소화)

멀티 에이전트 시스템에서 가장 흔한 실패 원인은 Agent 간 **강한 결합 (tight coupling)** 이다.

문제 상황:

```text
- Agent마다 입력/출력 형식이 다름
- 특정 Agent 내부 구조를 알아야 다음 Agent 구현 가능
- 하나의 Agent 변경이 전체 시스템에 영향
- 테스트 및 디버깅 어려움
```

이를 해결하기 위해서는 **Agent를 블랙박스로 다룰 수 있어야 한다.**

핵심 개념:

```text
Orchestrator는 Agent 내부 구현을 몰라도 된다.
→ 오직 Input / Output 계약(contract)만 알면 된다.
```

표준화의 효과:

- Agent 교체 용이성 (model 변경, 로직 변경)
- 장애 격리
- 테스트 자동화 가능
- 병렬 실행 및 확장성 확보
- 팀 간 독립 개발 가능

---

### 4.2 Agent 간 통합 방식

#### 방식 1: API 기반 통합 (서비스 간 분리)

각 Agent가 독립 서비스로 배포되고, HTTP/RPC로 통신한다.

```text
Orchestrator → HTTP/RPC → Agent A (별도 서비스)
                        → Agent B (별도 서비스)
```

적합한 경우:
- 팀별로 Agent를 독립 개발/배포해야 할 때
- Agent마다 다른 언어/런타임을 사용할 때
- 외부 파트너가 Agent를 제공하는 경우


#### 방식 2: State 기반 통합 (단일 프로세스 내)

LangGraph 등 프레임워크에서 Agent들이 공유 State를 통해 데이터를 주고받는다.

```text
StateGraph:
  Node A → state 업데이트 → Node B → state 업데이트 → Node C
```

적합한 경우:
- 단일 팀이 전체 Agent를 관리할 때
- Agent 간 데이터 전달이 빈번하고 밀접할 때
- 지연 시간(latency)을 최소화해야 할 때
- 프로토타이핑 및 초기 개발 단계

---

### 4.3 입출력 표준 스키마 예시 

- 공통 Request Schema
  ```json
  {
    "input": {
      "query": "사용자 요청",
      "context": {
        "db_id": "...",
        "additional_info": {}
      }
    }
  }
  ```

- 공통 Response Schema
  ```json
  {
    "result": {
      "summary": "분석 결과",
      "details": {}
    },
    "meta": {
      "confidence": 0.0,
      "latency_ms": 120,
      "token_usage": 300
    },
    "error": null
  }
  ```

- Error Contract
  ```json
  {
    "error": {
      "code": "TIMEOUT",
      "message": "Agent execution exceeded limit"
    }
  }
  ```

---

## 5. 실패 처리

### 5.1 Timeout

일정 시간 내 응답이 없으면 실패로 간주

```text
Orchestrator → Agent 호출 (timeout=20s)
→ 20초 초과 시 실패 처리
```

---

### 5.2 Retry

일시적 오류(transient failure)에 대응하기 위해 재시도

주의:
- 무조건 retry는 비용/지연 증가 유발하니 재시도 횟수 제한
- 비결정적(LLM) 결과에 대한 과도한 retry는 품질 변동만 키울 수 있음

---

### 5.3 Fallback

주요 Agent 실패 시 대체 경로로 전환한다.

```text
SQL Agent 실패 → Rule 기반 간이 분석 → 결과 반환
```
---

## 6. 테스트 전략

LLM/멀티 에이전트 시스템은 비결정성 때문에 **회귀(regression)와 품질 저하를 쉽게 놓친다**.

```text
- 동일 입력에도 출력 변동 가능
- prompt/모델 변경 시 예상치 못한 영향 발생
- 다수 Agent 결합 시 오류 원인 추적 어려움
```

---

### 6.1 테스트를 위한 설계 (함수형/순수성 지향)

테스트 용이성을 높이기 위해 Node/Agent는 가능한 한 **순수 함수에 가깝게** 설계한다.

권장:
- 입력(state, config) → 출력(state delta) 형태
- 외부 I/O는 Tool로 분리
- side-effect 최소화

```python
def classify_node(state, config):
    # pure logic
    return {"issue_type": "sql"}
```

장점:
- 재현성 높은 테스트
- mocking 용이
- 병렬/리플레이 테스트 가능

---

### 6.2 테스트 레벨

```text
1) Unit (Node/Agent 단위)
- 입력 → 출력 검증
- structured output 스키마 검증

2) Integration (Graph 단위)
- Router → Agents → Aggregator 흐름 검증
- fan-out / reducer 동작 검증

3) E2E (시나리오)
- 실제 요청 기반 결과 품질 확인
```

---

### 6.3 데이터 기반 테스트

- 고정된 테스트 케이스 세트 유지 (golden set)
- 실제 장애/운영 케이스를 축적
- 입력/기대 결과(또는 평가 기준) 함께 관리

---

### 6.4 LLM-as-a-Judge

정답이 명확하지 않은 경우, LLM을 평가자로 사용한다.

```text
expected_output + llm_result → Judge Prompt → Score / Pass-Fail
```

#### 평가 프롬프트 예시

```text
You are an evaluator for a database diagnosis system.

[Expected Output]
{expected_output}

[Model Output]
{llm_result}

Evaluate the model output based on the following criteria:
1. Does it correctly identify the root cause?
2. Does it include sufficient supporting evidence?
3. Is the explanation clear and actionable?

Return a JSON object with:
- score (0.0 ~ 1.0)
- pass (true/false, threshold 0.7)
- reason (short explanation)
```

#### 출력 예시

```json
{
  "score": 0.78,
  "pass": true,
  "reason": "Root cause is correct but explanation lacks detail"
}
```

주의:
- Judge 모델/프롬프트도 버전 관리
- 기준(prompt rubric) 명확화
- 비용/지연 고려


---

## 7. 향후 고려사항

### 7.1 CI/CD

멀티 에이전트 시스템에서도 CI/CD는 필수이다.

주요 포인트:

```text
- PR 시 자동 테스트 실행 (Unit / Integration / Judge 기반 평가)
- 성능 회귀 감지 (score threshold 기반)
- prompt / model / agent version 관리
- 실험(Experiment)과 배포(Production) 분리
```

권장 전략:

```text
- 테스트 데이터셋(golden set) 기반 자동 검증
- LLM-as-a-Judge를 CI에 포함
- 특정 score 이하 시 배포 차단
```

---

### 7.2 Message Queue / 비동기 처리

초기에는 Sync API 기반으로 시작하되, 서비스 확장 시 비동기 구조로 전환을 고려해야 한다.

도입 필요 상황:

```text
- 요청 처리 시간이 긴 경우
- 동시 요청이 많은 경우
- Agent fan-out으로 부하가 큰 경우
- retry / 재처리가 필요한 경우
```

구조:

```text
Client
  ↓
API Server
  ↓
Queue
  ↓
Worker Agents
  ↓
Result Store
```

장점:

```text
- 트래픽 흡수 (buffer 역할)
- 시스템 안정성 증가
- worker 기반 확장 가능
- 장애 격리
```

주의:

```text
- 응답 모델 변경 (즉시 응답 → job 기반 처리)
- 디버깅 복잡도 증가
- 상태 관리 필요
```

---


### TODO 라이브러리 버전 관리

```text
- 팀원 A는 0.1, 팀원 B는 0.2 사용 → 코드가 합쳐지면 런타임 에러
- 프로덕션과 개발 환경의 버전 불일치 → "내 환경에서는 됩니다" 문제
```
