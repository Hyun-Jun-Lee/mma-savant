# 데이터 처리 흐름 (Backend Function Reference)

사용자의 질문이 응답으로 변환되는 전체 과정을 백엔드 함수명 기반으로 정리한 문서입니다.

## 전체 흐름도

```
사용자 WebSocket 메시지 수신
│
▼
┌─────────────────────────────────────────────────────────┐
│ ConnectionManager.handle_user_message()                 │  manager.py:203
│  ├── _validate_user_connection()                        │  :232  연결 검증
│  ├── _check_usage_limit()                               │  :245  일일 사용량 확인
│  ├── _validate_message_data()                           │  :277  빈 메시지 검증
│  ├── _send_typing_indicator()                           │  :292  typing=True 전송
│  └── _process_llm_streaming_response()                  │  :321  ▼ 아래로
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ _process_llm_streaming_response()                       │  manager.py:321
│  ├── _ensure_llm_service() → get_graph_service()        │  :334  서비스 싱글턴 초기화
│  ├── _load_chat_history() (conversation_id 있을 때)     │  :342  DB에서 히스토리 로드
│  └── llm_service.generate_streaming_chat_response()     │  :345  ▼ 아래로
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ MMAGraphService.generate_streaming_chat_response()      │  service.py:65
│  ├── initialize()                                       │  :92   LLM + 그래프 최초 1회 빌드
│  │    ├── create_llm_with_callbacks()                   │         LLM 인스턴스 생성
│  │    └── build_mma_graph(llm)                          │         StateGraph 컴파일
│  ├── build_messages_from_history(chat_history)           │  :95   DB 메시지 → LangChain 변환
│  └── _compiled_graph.ainvoke(state)                     │  :99   ▼ 그래프 실행
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ StateGraph 실행 (graph_builder.py)                       │
│                                                         │
│  ① intent_classifier_node(state, llm)                   │  항상 LLM 호출
│     └── llm.with_structured_output(IntentClassification)│  → intent 결정
│                                                         │
│  ② route_by_intent(state)  ── 조건부 분기 ──            │
│     ├── "general"    → direct_response_node(state, llm) │  LLM 직접 답변 → END
│     ├── "followup"   → context_enricher_node(state, llm)│  질문 재작성 → ③으로
│     └── "sql_needed" → ③으로                            │
│                                                         │
│  ③ sql_agent_node(state, llm)                           │
│     ├── _build_sql_agent(llm)                           │  create_react_agent 생성
│     │    └── get_phase1_prompt()                        │  스키마+오늘 날짜 주입
│     ├── agent.ainvoke(messages)                         │  SQL 쿼리 생성 + 실행
│     │    └── execute_sql_query_async()                  │  asyncpg로 DB 조회
│     └── _extract_sql_result_from_messages()             │  ToolMessage에서 결과 추출
│                                                         │
│  ④ result_analyzer_node(state)  ── 규칙 기반 ──         │  LLM 미사용
│     └── 행 수, 숫자 컬럼 수 기반으로 판단               │  → response_mode 결정
│                                                         │
│  ⑤ route_by_response_mode(state)  ── 조건부 분기 ──     │
│     ├── "visualization" → visualize_node(state, llm)    │  차트 JSON 생성 → END
│     └── "text"          → text_response_node(state, llm)│  텍스트 분석 → END
└─────────────────────────────────────────────────────────┘
         │
         ▼  (결과가 service.py로 반환)
         │
         │  yield { type: "final_result", content, visualization_type, ... }
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ _process_llm_streaming_response() 후처리               │  manager.py:366
│  ├── _save_successful_conversation()                    │  :416  DB 저장
│  │    ├── get_or_create_session() (새 대화일 때)        │        세션 생성
│  │    ├── _save_user_message()                          │        사용자 메시지 저장
│  │    └── add_message_to_session(role="assistant")      │        AI 응답 + viz 저장
│  ├── _send_final_result()                               │  :388  final_result 전송
│  ├── send_to_connection(typing=False)                   │  :376  타이핑 종료
│  └── send_to_connection(response_end)                   │  :381  응답 완료 신호
└─────────────────────────────────────────────────────────┘
         │
         ▼
    프론트엔드 수신
```

## 3계층 요약

| 계층 | 파일 | 역할 |
|------|------|------|
| **WebSocket 계층** | `api/websocket/manager.py` | 연결 검증, 사용량 체크, 히스토리 로드, DB 저장, 이벤트 전송 |
| **서비스 계층** | `llm/service.py` | LangChain 메시지 변환, 그래프 `ainvoke` 실행, 결과 yield |
| **그래프 계층** | `llm/graph/graph_builder.py` + 7개 노드 | 의도 분류 → 조건부 라우팅 → SQL 실행/분석 → 응답 생성 |

## StateGraph 노드 상세

### ① intent_classifier_node
- **파일**: `llm/graph/nodes/intent_classifier.py`
- **방식**: 항상 LLM (`with_structured_output`)
- **출력**: `intent` = `general` | `sql_needed` | `followup`
- **안전장치**: LLM 실패 시 `sql_needed` fallback, 히스토리 없는 followup → `sql_needed` 보정

### ② direct_response_node
- **파일**: `llm/graph/nodes/direct_response.py`
- **트리거**: `intent == "general"`
- **역할**: MMA 일반 지식 답변, MMA 외 질문 거절

### ③ context_enricher_node
- **파일**: `llm/graph/nodes/context_enricher.py`
- **트리거**: `intent == "followup"`
- **역할**: 후속 질문을 독립적 질문으로 재작성 (예: "그중에서 KO는?" → "존 존스의 KO 승리 기록을 알려줘")
- **이후**: `sql_agent_node`로 진행

### ④ sql_agent_node
- **파일**: `llm/graph/nodes/sql_agent.py`
- **트리거**: `intent == "sql_needed"` 또는 `context_enricher` 이후
- **방식**: `langgraph.prebuilt.create_react_agent` (ReAct 루프)
- **프롬프트**: `get_phase1_prompt()` — DB 스키마 + 오늘 날짜 동적 주입
- **도구**: `execute_sql_query_async()` (asyncpg 기반 읽기 전용)

### ⑤ result_analyzer_node
- **파일**: `llm/graph/nodes/result_analyzer.py`
- **방식**: 규칙 기반 (LLM 미사용)
- **판단 기준**: 행 수, 컬럼 수, 숫자 컬럼 비율
- **출력**: `response_mode` = `visualization` | `text`

### ⑥ visualize_node
- **파일**: `llm/graph/nodes/visualize.py`
- **트리거**: `response_mode == "visualization"`
- **역할**: SQL 결과를 차트 JSON으로 변환 (bar_chart, pie_chart, radar_chart 등)

### ⑦ text_response_node
- **파일**: `llm/graph/nodes/text_response.py`
- **트리거**: `response_mode == "text"`
- **역할**: SQL 결과를 한국어 텍스트 분석으로 변환

## WebSocket 이벤트 흐름

```
[Server → Client]

1. { type: "typing", is_typing: true }       ← 처리 시작
2. { type: "final_result", content, ... }     ← 최종 결과
3. { type: "typing", is_typing: false }       ← 타이핑 종료
4. { type: "response_end", conversation_id }  ← 응답 완료
```

## 멀티턴 대화 처리

```
새 대화 (conversation_id 없음):
  사용자 메시지 → LLM 처리 → 성공 시 get_or_create_session() → DB 저장

기존 대화 (conversation_id 있음):
  _load_chat_history() → build_messages_from_history() (최근 20개)
  → 히스토리 + 현재 메시지로 그래프 실행 → 기존 세션에 메시지 추가
```
