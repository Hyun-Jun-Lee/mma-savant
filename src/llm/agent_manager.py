"""
Two-Phase Reasoning System을 구현한 에이전트 매니저
MCP 도구 없이 기본 LangChain 도구를 사용하여 ReAct + OpenRouter 지원
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from traceback import format_exc

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from llm.chart_loader import (
    get_supported_charts,
    validate_chart_id
)
from llm.prompts.agent_prompt_templates import (
    create_phase1_prompt_template,
    prepare_phase2_input
)
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


def get_supported_charts_info() -> Dict[str, Any]:
    """지원되는 차트 정보를 Phase 2 프롬프트용으로 반환"""
    charts_info = {}
    supported_charts = get_supported_charts()
    for chart_id, chart_config in supported_charts.items():
        charts_info[chart_id] = {
            "description": chart_config["description"],
            "use_cases": chart_config["best_for"],
            "data_needs": chart_config["data_requirements"]
        }
    return charts_info


class AgentManager:
    """
    Two-Phase Reasoning을 지원하는 에이전트 매니저 (ReAct + OpenRouter)
    Phase 1: ReAct 에이전트로 의도 분석 + 도구 선택/실행 (understand_and_collect)
    Phase 2: 데이터 처리 + 시각화 준비 (process_and_visualize)

    주요 개선사항:
    - ReAct 에이전트 사용으로 OpenRouter 모델과 호환성 향상
    - MCP 도구 제거, 기본 LangChain 도구 사용
    - 파싱 오류 처리 및 최적화된 반복 설정
    """

    def __init__(self):
        """AgentManager 초기화"""
        LOGGER.info("🎯 AgentManager initialized with Two-Phase Reasoning capability")

    def _create_react_compatible_tools(self):
        """
        ReAct 에이전트와 호환되는 일반 LangChain 도구 생성
        MCP 도구 없이 직접 구현한 도구들 사용
        """
        import json
        from langchain.tools import Tool
        from database.connection.postgres_conn import get_readonly_db_context
        from sqlalchemy import text

        def sync_execute_sql_query(query: str) -> str:
            """
            읽기 전용 DB 연결을 사용하는 ReAct 호환 SQL 실행
            """
            LOGGER.debug(f"🔧 [ReAct SQL] Called with query: {query}")

            try:
                # JSON 형식으로 잘못 전달된 경우 처리
                if query.startswith("{") and query.endswith("}"):
                    try:
                        query_data = json.loads(query)
                        if "query" in query_data:
                            query = query_data["query"]
                    except:
                        pass

                # 마크다운 래퍼 제거
                query = query.strip()
                if query.startswith("```") and query.endswith("```"):
                    import re
                    query = re.sub(r'^```\w*\n?', '', query)
                    query = re.sub(r'\n?```$', '', query)
                    query = query.strip()

                # 읽기 전용 DB 연결로 실행
                with get_readonly_db_context() as session:
                    result = session.execute(text(query))
                    rows = result.fetchall()
                    columns = result.keys()

                    # 결과를 JSON 형식으로 반환
                    data = [dict(zip(columns, row)) for row in rows]

                    response = {
                        "query": query,
                        "success": True,
                        "data": data,
                        "columns": list(columns),
                        "row_count": len(data)
                    }

                    LOGGER.info(f"✅ [ReAct SQL] Query executed successfully: {len(data)} rows")
                    return json.dumps(response, ensure_ascii=False, default=str)

            except Exception as e:
                error_response = {
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "data": [],
                    "columns": [],
                    "row_count": 0
                }
                LOGGER.error(f"❌ [ReAct SQL] Query failed: {e}")
                return json.dumps(error_response, ensure_ascii=False)

        # ReAct 호환 도구 생성
        tools = [
            Tool(
                name="execute_raw_sql_query",
                func=sync_execute_sql_query,
                description="""UFC 데이터베이스에서 읽기 전용 SQL 쿼리를 실행합니다.

                중요한 테이블명 규칙 (단수형 사용):
                - 'fighter' (파이터 정보)
                - 'match' (매치 정보)
                - 'fighter_match' (파이터-매치 관계)
                - 'event' (이벤트 정보)
                - 'ranking' (랭킹 정보)
                - 'weight_class' (체급 정보)

                읽기 전용 계정이므로 SELECT만 가능합니다.

                올바른 쿼리 예시:
                SELECT f.name, COUNT(*) as ko_wins FROM fighter f JOIN fighter_match fm ON f.id = fm.fighter_id JOIN match m ON fm.match_id = m.id WHERE m.method ILIKE '%ko%' GROUP BY f.name ORDER BY ko_wins DESC LIMIT 3;

                Args:
                    query (str): 실행할 SQL 쿼리 (읽기 전용)
                """
            )
        ]

        return tools

    def validate_chat_history(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        채팅 히스토리 유효성 검사 및 정리

        Args:
            messages: 원본 메시지 리스트

        Returns:
            List[BaseMessage]: 유효한 메시지들만 포함된 리스트
        """
        valid_messages = []

        for message in messages:
            if isinstance(message, (HumanMessage, AIMessage, SystemMessage)):
                # 빈 content는 제외
                if message.content and message.content.strip():
                    valid_messages.append(message)

        LOGGER.debug(f"📚 Chat history validation: {len(messages)} → {len(valid_messages)} messages")
        return valid_messages

    def create_execution_config(self, user_message: str, chat_history: List[BaseMessage]) -> Dict[str, Any]:
        """
        에이전트 실행을 위한 설정 생성

        Args:
            user_message: 사용자 메시지
            chat_history: 채팅 히스토리

        Returns:
            Dict: 에이전트 실행 설정
        """
        return {
            "input": user_message,
            "chat_history": chat_history
        }

    async def process_two_step(
        self,
        user_query: str,
        llm: Any,
        callback_handler: Any,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """
        Two-Step 쿼리 처리 메인 메서드

        Args:
            user_query: 사용자 질문
            llm: LangChain LLM 인스턴스
            callback_handler: 콜백 핸들러
            chat_history: 채팅 히스토리

        Returns:
            Dict: 전체 처리 결과 및 최종 응답
        """
        processing_id = f"query_{hash(user_query)}_{int(asyncio.get_event_loop().time())}"

        try:
            LOGGER.info(f"🚀 Starting Two-Step processing for query: {user_query[:50]}...")

            # Phase 1: 의도 분석 및 데이터 수집
            phase1_result = await self._understand_and_collect(
                user_query=user_query,
                llm=llm,
                callback_handler=callback_handler,
                chat_history=chat_history or [],
                processing_id=processing_id
            )

            if phase1_result.get("error"):
                return self._create_error_response("Phase 1 failed", phase1_result)

            # Phase 2: 데이터 처리 및 시각화
            phase2_result = await self._process_and_visualize(
                user_query=user_query,
                phase1_data=phase1_result,
                llm=llm,
                callback_handler=callback_handler,
                processing_id=processing_id
            )

            if phase2_result.get("error"):
                return self._create_error_response("Phase 2 failed", phase2_result)

            # 최종 결과 구성 (시각화 데이터 + content 필드 포함)
            simplified_result = {
                "processing_id": processing_id,
                "content": phase2_result.get("final_response", ""),  # content 필드 추가
                "visualization_type": phase2_result.get("visualization_type", ""),
                "visualization_data": phase2_result.get("visualization_data", {}),
                "insights": phase2_result.get("insights", []),
                "sql_query": phase1_result.get("sql_query", ""),
                "row_count": phase1_result.get("row_count", 0)
            }
            return simplified_result

        except Exception as e:
            LOGGER.error(f"❌ Error in Two-Step processing: {e}")
            LOGGER.error(format_exc())
            return self._create_error_response(f"Processing failed: {str(e)}")

    async def _understand_and_collect(
        self,
        user_query: str,
        llm: Any,
        callback_handler: Any,
        chat_history: List[BaseMessage],
        processing_id: str
    ) -> Dict[str, Any]:
        """
        Phase 1: 사용자 의도 분석 및 필요한 데이터 수집
        LLM이 질문을 분석하고 적절한 도구들을 선택/실행하여 원시 데이터 수집

        Args:
            user_query: 사용자 질문
            llm: LLM 인스턴스
            callback_handler: 콜백 핸들러
            chat_history: 채팅 히스토리
            processing_id: 처리 식별자

        Returns:
            Dict: Phase 1 처리 결과 (원시 데이터 + 실행된 도구 정보)
        """
        try:
            LOGGER.info(f"🔍 Phase 1: Understanding and collecting data for query: {user_query[:50]}...")

            # Phase 1용 ReAct 프롬프트 생성
            from llm.prompts.two_phase_prompts import get_phase1_prompt
            from llm.providers.openrouter_provider import create_react_prompt_template

            base_phase1_prompt = get_phase1_prompt()
            react_prompt = create_react_prompt_template(base_phase1_prompt)

            # ReAct 에이전트용 일반 LangChain 도구 생성
            tools = self._create_react_compatible_tools()
            LOGGER.info(f"🔧 Phase 1 loaded {len(tools)} ReAct-compatible tools")

            # Phase 1 ReAct 에이전트 생성 (OpenRouter 최적화)
            agent = create_react_agent(llm, tools, react_prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                return_intermediate_steps=True,
                callbacks=[callback_handler],
                max_iterations=5,  # ReAct는 더 적은 반복으로 충분
                handle_parsing_errors=True  # ReAct 파싱 오류 처리
            )

            # 실행 설정 (LLM이 도구 선택 및 실행)
            execution_config = self.create_execution_config(
                user_message=user_query,
                chat_history=chat_history
            )

            LOGGER.info("🚀 Phase 1: Starting ReAct agent with OpenRouter LLM...")

            # Phase 1 실행 - LLM이 질문 분석 후 도구들 선택/실행
            result = await agent_executor.ainvoke(execution_config)

            # SQL 실행 결과 추출 (하나의 SQL 쿼리만 실행됨)
            sql_result = self._extract_sql_result(result.get("intermediate_steps", []))

            # Phase 1 완료 결과 구성 (SQL 결과만 포함)
            phase1_result = {
                "phase": 1,
                "processing_id": processing_id,
                "user_query": result.get("input", user_query),  # 사용자 원본 쿼리
                "sql_query": sql_result.get("query", ""),  # 실행된 SQL 쿼리
                "sql_success": sql_result.get("success", False),  # 성공 여부
                "sql_data": sql_result.get("data", []),  # 실제 데이터
                "sql_columns": sql_result.get("columns", []),  # 컬럼 정보
                "row_count": sql_result.get("row_count", 0)  # 행 개수
            }

            LOGGER.info(f"✅ Phase 1 completed: SQL query executed")
            if not phase1_result['sql_success']:
                LOGGER.warning(f"⚠️ SQL execution failed: {sql_result.get('error', 'Unknown error')}")

            return phase1_result

        except Exception as e:
            LOGGER.error(f"❌ Phase 1 error: {e}")
            LOGGER.error(format_exc())
            return {
                "error": str(e),
                "phase": 1,
                "processing_id": processing_id,
                "sql_success": False,
                "sql_data": [],
                "sql_columns": [],
                "row_count": 0
            }

    async def _process_and_visualize(
        self,
        user_query: str,
        phase1_data: Dict[str, Any],
        llm: Any,
        callback_handler: Any,
        processing_id: str
    ) -> Dict[str, Any]:
        """
        Phase 2: 수집된 데이터를 분석하고 최적 시각화 선택/생성
        직접 LLM 호출로 간소화된 구조

        Args:
            user_query: 원래 사용자 질문
            phase1_data: Phase 1 결과 데이터
            llm: LLM 인스턴스
            callback_handler: 콜백 핸들러
            processing_id: 처리 식별자

        Returns:
            Dict: Phase 2 처리 결과 (시각화 데이터 + 인사이트)
        """
        try:
            LOGGER.info(f"🎨 Phase 2: Processing and visualizing data for query")

            # Phase 2 프롬프트 생성
            from llm.prompts.two_phase_prompts import get_phase2_prompt_with_charts
            phase2_prompt = get_phase2_prompt_with_charts()

            # Phase 2 입력 데이터 준비
            phase2_input = prepare_phase2_input(user_query, phase1_data)

            # 전체 프롬프트 구성
            full_prompt = phase2_prompt + "\n\n" + phase2_input

            # 직접 LLM 호출 (Agent 없이)
            response = await llm.ainvoke(full_prompt)

            # 응답 텍스트 추출
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 결과 파싱 및 시각화 데이터 구조화 (직접 응답 텍스트 전달)
            parsed_result = self._parse_phase2_result(response_text, processing_id, phase1_data)

            # 응답 품질 검증 및 보완
            validated_result = self._validate_and_enhance_phase2_result(parsed_result)

            LOGGER.info(f"✅ Phase 2 completed: {validated_result.get('visualization_type', 'unknown')} visualization prepared")
            return validated_result

        except Exception as e:
            LOGGER.error(f"❌ Phase 2 error: {e}")
            LOGGER.error(format_exc())
            return {
                "error": str(e),
                "phase": 2,
                "processing_id": processing_id,
                "fallback_visualization": self._create_fallback_visualization(phase1_data)
            }

    def _parse_phase2_result(self, response_text: str, processing_id: str, phase1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2 결과 파싱 및 시각화 데이터 구조화"""
        try:
            # 응답 텍스트 유효성 검사
            if not isinstance(response_text, str):
                response_text = str(response_text)

            output_text = response_text.strip()

            # 직접 JSON 파싱 시도
            extracted_json = None
            try:
                # 먼저 직접 JSON 파싱 시도
                extracted_json = json.loads(output_text)
            except json.JSONDecodeError:
                # 실패 시 JSON 추출 함수 사용
                extracted_json = self._extract_json_from_response(output_text)

            if extracted_json:
                # 구조화된 응답인 경우
                visualization_type = extracted_json.get('selected_visualization', 'text_summary')
                visualization_data = extracted_json.get('visualization_data', {})
                insights = extracted_json.get('insights', [])

            else:
                # 텍스트 기반 응답인 경우 기본 처리
                visualization_type = 'text_summary'
                visualization_data = {"content": output_text}
                insights = self._extract_key_insights_from_text(output_text)

            return {
                "phase": 2,
                "processing_id": processing_id,
                "visualization_type": visualization_type,
                "visualization_data": visualization_data,
                "insights": insights,
                "final_response": output_text,
                "metadata": {
                    "data_source": "phase1_tools",
                    "processing_method": "llm_analysis",
                    "chart_config": get_supported_charts().get(visualization_type, {})
                }
            }

        except Exception as e:
            LOGGER.error(f"Error parsing Phase 2 result: {e}")
            LOGGER.error(format_exc())
            return {
                "error": f"Failed to parse Phase 2 result: {str(e)}",
                "phase": 2,
                "processing_id": processing_id,
                "fallback_response": response_text
            }

    def _validate_and_enhance_phase2_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2 결과 검증 및 품질 향상"""
        try:
            if result.get("error"):
                return result

            visualization_type = result.get("visualization_type")

            # 선택된 시각화 타입이 지원되는지 확인
            if not validate_chart_id(visualization_type):
                LOGGER.warning(f"Unsupported visualization type: {visualization_type}, falling back to text_summary")
                result["visualization_type"] = "text_summary"
                result["visualization_data"] = {"content": result.get("final_response", "")}
                result["fallback_applied"] = True

            # 메타데이터 보강
            result["metadata"] = result.get("metadata", {})
            result["metadata"]["visualization_validated"] = True

            return result

        except Exception as e:
            LOGGER.error(f"Error validating Phase 2 result: {e}")
            LOGGER.error(format_exc())
            result["validation_error"] = str(e)
            return result

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """LLM 응답에서 JSON 구조 추출"""
        try:
            # 입력 유효성 검사
            if not isinstance(response_text, str):
                LOGGER.warning(f"Expected string input, got {type(response_text)}")
                return None

            if not response_text.strip():
                return None

            # JSON 블록 찾기 (```json ... ``` 또는 { ... } 패턴)
            import re

            # JSON 코드 블록 패턴
            json_block_pattern = r'```json\s*(\{.*?\})\s*```'
            json_match = re.search(json_block_pattern, response_text, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # 직접 JSON 객체 패턴
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, response_text)

            for json_str in json_matches:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict) and any(key in parsed for key in ['selected_visualization', 'visualization_data']):
                        return parsed
                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            LOGGER.debug(f"Could not extract JSON from response: {e}")
            LOGGER.debug(format_exc())
            return None

    def _extract_key_insights_from_text(self, text: str) -> List[str]:
        """텍스트에서 핵심 인사이트 추출"""
        insights = []

        # 입력 유효성 검사
        if not isinstance(text, str) or not text.strip():
            return insights

        try:
            # 간단한 패턴 매칭으로 인사이트 추출
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('**') and line.endswith('**'):
                    insights.append(line.replace('**', ''))
                elif line.startswith('- ') or line.startswith('• '):
                    insights.append(line[2:])
                elif '승률' in line or '랭킹' in line or '분석' in line:
                    insights.append(line)

            return insights[:5]  # 최대 5개까지

        except Exception as e:
            LOGGER.warning(f"Error extracting insights from text: {e}")
            LOGGER.debug(format_exc())  # debug 레벨로 상세 정보 로깅
            return insights

    def _create_fallback_visualization(self, phase1_data: Dict[str, Any]) -> Dict[str, Any]:
        """오류 발생 시 사용할 기본 시각화"""
        return {
            "type": "text_summary",
            "data": {
                "content": f"데이터 수집이 완료되었습니다. {phase1_data.get('row_count', 0)}개의 데이터를 조회했습니다.",
                "row_count": phase1_data.get('row_count', 0)
            }
        }

    def _extract_sql_result(self, intermediate_steps: List) -> Dict[str, Any]:
        """
        AgentExecutor intermediate_steps에서 SQL 실행 결과 추출
        LangChain이 문자열로 직렬화한 결과를 JSON 파싱 후 마지막 성공한 결과 반환

        Args:
            intermediate_steps: AgentExecutor에서 생성된 중간 단계들

        Returns:
            Dict: SQL 쿼리 실행 결과 (query, success, data, columns, row_count)
        """
        import json

        try:
            LOGGER.debug(f"🔍 Extracting SQL result from {len(intermediate_steps)} intermediate steps")

            sql_results = []

            # 모든 SQL 실행 결과 수집 및 JSON 파싱
            for i, step in enumerate(intermediate_steps):
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    tool_name = getattr(action, 'tool', 'unknown')

                    # execute_raw_sql_query 도구의 결과만 처리
                    if tool_name == "execute_raw_sql_query":
                        try:
                            # LangChain이 문자열로 직렬화한 결과를 JSON 파싱
                            if isinstance(observation, str):
                                parsed_result = json.loads(observation)
                            elif isinstance(observation, dict):
                                parsed_result = observation
                            else:
                                LOGGER.warning(f"   Step {i+1}: Unexpected observation type: {type(observation)}")
                                continue

                            # SQL 결과 저장
                            sql_results.append({
                                "step": i + 1,
                                "query": parsed_result.get("query", ""),
                                "success": parsed_result.get("success", False),
                                "data": parsed_result.get("data", []),
                                "columns": parsed_result.get("columns", []),
                                "row_count": parsed_result.get("row_count", 0),
                                "error": parsed_result.get("error", None)
                            })

                            LOGGER.debug(f"   Step {i+1}: SQL execution - success: {parsed_result.get('success', False)}")

                        except json.JSONDecodeError as e:
                            LOGGER.warning(f"   Step {i+1}: Failed to parse JSON: {e}")
                            continue

            # 성공한 SQL 결과 찾기 (마지막 성공한 것 우선)
            for result in reversed(sql_results):
                if result["success"]:
                    del result["step"]  # step 정보는 제거
                    return result

            # 성공한 결과가 없으면 마지막 시도 결과 반환 (에러 정보 포함)
            if sql_results:
                last_result = sql_results[-1]
                LOGGER.warning(f"⚠️ All {len(sql_results)} SQL attempts failed, returning last attempt from step {last_result['step']}")
                del last_result["step"]
                return last_result

            # SQL 결과를 찾지 못한 경우
            LOGGER.warning("⚠️ No SQL execution result found in intermediate steps")
            return {
                "query": "",
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": "No SQL query was executed"
            }

        except Exception as e:
            LOGGER.error(f"❌ Error extracting SQL results: {e}")
            LOGGER.error(format_exc())
            return {
                "query": "",
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": f"Error extracting results: {str(e)}"
            }

    def _create_error_response(self, error_message: str, error_details: Dict = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "error": error_message,
            "error_details": error_details or {},
            "user_response": f"죄송합니다. 처리 중 오류가 발생했습니다: {error_message}",
            "fallback_available": True
        }

    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            health_status = {
                "agent_manager": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "version": "unified",
                "mcp_dependency": False,
                "react_agent": True,
                "openrouter_compatible": True
            }

            return health_status

        except Exception as e:
            LOGGER.error(f"❌ Health check error: {e}")
            LOGGER.error(format_exc())
            return {
                "agent_manager": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }