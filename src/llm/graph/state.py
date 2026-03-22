"""MMA Graph State 정의"""
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class MMAGraphState(TypedDict):
    """LangGraph StateGraph의 상태 스키마"""

    # 대화 메시지 (멀티턴 히스토리) - add_messages reducer로 자동 관리
    messages: Annotated[list[BaseMessage], add_messages]

    # 의도 분류 결과
    intent: Literal["general", "sql_needed", "followup"]

    # SQL 실행 결과 (sql_agent 노드 출력)
    sql_result: Optional[dict]  # {query, data, columns, row_count, success}
    agent_reasoning: Optional[str]  # sql_agent의 최종 텍스트 답변 (text 라우팅 시 재사용)

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
