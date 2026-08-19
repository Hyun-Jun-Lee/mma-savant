"""StateGraph 노드 단위 테스트 — 멀티 에이전트 아키텍처"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# =============================================================================
# mma_analysis 헬퍼 함수 테스트
# =============================================================================

class TestMmaAnalysisHelpers:
    """mma_analysis 노드의 SQL 추출 테스트"""

    def test_extract_sql_result_from_tool_message(self):
        from llm.graph.nodes.mma_analysis import _extract_sql_result
        tool_content = json.dumps({
            "success": True, "data": [{"name": "test"}],
            "columns": ["name"], "row_count": 1, "query": "SELECT 1",
        })
        messages = [
            HumanMessage(content="test"),
            AIMessage(content="running query"),
            ToolMessage(content=tool_content, tool_call_id="1"),
        ]
        result = _extract_sql_result(messages)
        assert result["success"] is True
        assert result["row_count"] == 1

    def test_extract_sql_results_preserves_multiple_successful_tool_messages(self):
        from llm.graph.nodes.mma_analysis import _extract_sql_results
        first_result = json.dumps({
            "success": True,
            "data": [{"fighter_name": "islam makhachev", "wins": 27}],
            "columns": ["fighter_name", "wins"],
            "row_count": 1,
            "query": "SELECT fighter_name, wins FROM v_fighter_record_summary",
        })
        second_result = json.dumps({
            "success": True,
            "data": [{"fighter_name": "islam makhachev", "opponent_name": "charles oliveira"}],
            "columns": ["fighter_name", "opponent_name"],
            "row_count": 1,
            "query": "SELECT fighter_name, opponent_name FROM v_fighter_opponents",
        })
        messages = [
            HumanMessage(content="test"),
            ToolMessage(content=first_result, tool_call_id="1"),
            ToolMessage(content=second_result, tool_call_id="2"),
        ]

        results = _extract_sql_results(messages)

        assert [result["query"] for result in results] == [
            "SELECT fighter_name, wins FROM v_fighter_record_summary",
            "SELECT fighter_name, opponent_name FROM v_fighter_opponents",
        ]

    def test_extract_sql_results_keeps_successes_when_later_tool_call_failed(self):
        from llm.graph.nodes.mma_analysis import _extract_sql_results
        success_result = json.dumps({
            "success": True,
            "data": [{"fighter_name": "charles oliveira", "wins": 35}],
            "columns": ["fighter_name", "wins"],
            "row_count": 1,
            "query": "SELECT fighter_name, wins FROM v_fighter_record_summary",
        })
        failed_result = json.dumps({
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "query": "(SELECT * FROM bad_view)",
            "error": "relation does not exist",
        })
        messages = [
            HumanMessage(content="test"),
            ToolMessage(content=success_result, tool_call_id="1"),
            ToolMessage(content=failed_result, tool_call_id="2"),
        ]

        results = _extract_sql_results(messages)

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["query"] == "SELECT fighter_name, wins FROM v_fighter_record_summary"

    def test_build_agent_results_creates_one_agent_result_per_sql_result(self):
        from llm.graph.nodes.mma_analysis import _build_agent_results
        sql_results = [
            {
                "success": True,
                "query": "SELECT record",
                "data": [{"wins": 1}],
                "columns": ["wins"],
                "row_count": 1,
            },
            {
                "success": True,
                "query": "SELECT recent",
                "data": [{"opponent": "test"}],
                "columns": ["opponent"],
                "row_count": 1,
            },
        ]

        agent_results = _build_agent_results("fighter_comparison", sql_results, "done")

        assert [result["agent_name"] for result in agent_results] == [
            "fighter_comparison[1]",
            "fighter_comparison[2]",
        ]
        assert [result["query"] for result in agent_results] == ["SELECT record", "SELECT recent"]

    def test_no_tool_message_returns_failure(self):
        from llm.graph.nodes.mma_analysis import _extract_sql_result
        messages = [HumanMessage(content="test"), AIMessage(content="ok")]
        result = _extract_sql_result(messages)
        assert result["success"] is False

    def test_extract_reasoning_from_ai_message(self):
        from llm.graph.nodes.mma_analysis import _extract_reasoning
        messages = [
            HumanMessage(content="test"),
            AIMessage(content=""),
            AIMessage(content="Jones has 28 wins"),
        ]
        result = _extract_reasoning(messages)
        assert result == "Jones has 28 wins"


# =============================================================================
# graph_builder 라우팅 테스트
# =============================================================================

class TestGraphBuilder:
    """build_mma_graph 조립 및 라우팅 테스트"""

    def test_graph_compiles_with_mock_llm(self):
        from llm.graph.graph_builder import build_mma_graph
        mock_llm = MagicMock()
        compiled = build_mma_graph(mock_llm)
        assert compiled is not None

    def test_graph_compiles_with_dual_llm(self):
        from llm.graph.graph_builder import build_mma_graph
        compiled = build_mma_graph(MagicMock(), MagicMock())
        assert compiled is not None

    def test_supervisor_dispatch_general(self):
        from llm.graph.graph_builder import supervisor_dispatch
        sends = supervisor_dispatch({"route": "general"})
        assert len(sends) == 1
        assert sends[0].node == "direct_response"

    def test_supervisor_dispatch_mma_analysis(self):
        from llm.graph.graph_builder import supervisor_dispatch
        sends = supervisor_dispatch({
            "route": "mma_analysis",
            "active_agents": ["mma_analysis"],
        })
        assert len(sends) == 1
        assert sends[0].node == "mma_analysis"

    def test_supervisor_dispatch_complex(self):
        from llm.graph.graph_builder import supervisor_dispatch
        sends = supervisor_dispatch({
            "route": "complex",
            "active_agents": ["mma_analysis", "fighter_comparison"],
        })
        assert len(sends) == 2
        nodes = {s.node for s in sends}
        assert nodes == {"mma_analysis", "fighter_comparison"}

    def test_critic_route_passed_text_only(self):
        from llm.graph.graph_builder import critic_route
        sends = critic_route({
            "critic_passed": True,
            "needs_visualization": False,
        })
        assert len(sends) == 1
        assert sends[0].node == "text_response"

    def test_critic_route_passed_with_visualization(self):
        from llm.graph.graph_builder import critic_route
        sends = critic_route({
            "critic_passed": True,
            "needs_visualization": True,
        })
        assert len(sends) == 2
        nodes = {s.node for s in sends}
        assert nodes == {"text_response", "visualization"}

    def test_critic_route_retry(self):
        from llm.graph.graph_builder import critic_route
        from langgraph.graph import END
        sends = critic_route({
            "critic_passed": False,
            "validation_status": "retry_needed",
            "retry_count": 1,
            "active_agents": ["mma_analysis"],
        })
        assert sends != END
        assert len(sends) == 1
        assert sends[0].node == "mma_analysis"

    def test_critic_route_unsupported_goes_to_text_response(self):
        from llm.graph.graph_builder import critic_route
        sends = critic_route({
            "critic_passed": False,
            "validation_status": "unsupported",
            "retry_count": 0,
        })
        assert len(sends) == 1
        assert sends[0].node == "text_response"

    def test_critic_route_no_sql_needed_goes_to_text_response(self):
        from llm.graph.graph_builder import critic_route
        sends = critic_route({
            "critic_passed": True,
            "validation_status": "no_sql_needed",
            "needs_visualization": False,
        })
        assert len(sends) == 1
        assert sends[0].node == "text_response"

    def test_critic_route_invalid_result_retries(self):
        from llm.graph.graph_builder import critic_route
        from langgraph.graph import END
        sends = critic_route({
            "critic_passed": False,
            "validation_status": "invalid_result",
            "retry_count": 1,
            "active_agents": ["mma_analysis"],
        })
        assert sends != END
        assert len(sends) == 1
        assert sends[0].node == "mma_analysis"

    def test_critic_route_exhausted(self):
        from llm.graph.graph_builder import critic_route
        from langgraph.graph import END
        result = critic_route({
            "critic_passed": False,
            "retry_count": 3,
        })
        assert result == END


# =============================================================================
# SQL 쿼리 검증 테스트
# =============================================================================

class TestSqlQueryValidation:
    """_validate_query SQL 인젝션 방어 테스트"""

    def test_select_allowed(self):
        from llm.tools.sql_tool import _validate_query
        _validate_query("SELECT name FROM fighter LIMIT 5")

    def test_with_cte_allowed(self):
        from llm.tools.sql_tool import _validate_query
        _validate_query("WITH top AS (SELECT * FROM fighter) SELECT * FROM top")

    def test_clean_query_removes_single_outer_parentheses_wrapper(self):
        from llm.tools.sql_tool import _clean_query
        assert _clean_query("(SELECT * FROM v_fighter_record_summary)") == "SELECT * FROM v_fighter_record_summary"

    def test_clean_query_does_not_remove_partial_parentheses(self):
        from llm.tools.sql_tool import _clean_query
        query = "SELECT COUNT(*) FROM fighter WHERE name IN ('islam makhachev')"
        assert _clean_query(query) == query

    def test_select_case_insensitive(self):
        from llm.tools.sql_tool import _validate_query
        _validate_query("select name from fighter")

    def test_insert_blocked(self):
        from llm.tools.sql_tool import _validate_query
        with pytest.raises(ValueError):
            _validate_query("INSERT INTO fighter (name) VALUES ('test')")

    def test_update_blocked(self):
        from llm.tools.sql_tool import _validate_query
        with pytest.raises(ValueError):
            _validate_query("UPDATE fighter SET name = 'test'")

    def test_delete_blocked(self):
        from llm.tools.sql_tool import _validate_query
        with pytest.raises(ValueError):
            _validate_query("DELETE FROM fighter WHERE id = 1")

    def test_drop_blocked(self):
        from llm.tools.sql_tool import _validate_query
        with pytest.raises(ValueError):
            _validate_query("DROP TABLE fighter")

    def test_semicolon_injection_blocked(self):
        from llm.tools.sql_tool import _validate_query
        with pytest.raises(ValueError):
            _validate_query("SELECT 1; DROP TABLE fighter")

    def test_select_with_trailing_semicolon_allowed(self):
        from llm.tools.sql_tool import _validate_query
        _validate_query("SELECT name FROM fighter;")


# =============================================================================
# Critic Phase A hard gate 테스트
# =============================================================================

class TestCriticPhaseA:
    """critic deterministic Phase A packet hard gate 테스트"""

    def _result(self, query, data=None, row_count=1, columns=None, reasoning="ok", success=None, error=None):
        if data is None:
            data = [{"value": 1}] if row_count else []
        if columns is None:
            columns = list(data[0].keys()) if data else []
        result = {
            "agent_name": "mma_analysis",
            "query": query,
            "data": data,
            "columns": columns,
            "row_count": row_count,
            "reasoning": reasoning,
        }
        if success is not None:
            result["success"] = success
        if error is not None:
            result["error"] = error
        return result

    def test_query_absence_with_no_sql_needed_reasoning_does_not_retry(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "",
                row_count=0,
                reasoning="no_sql_needed: this request can be answered without a database query",
            )
        ], "너는 어떤 데이터를 조회할 수 있어?")

        assert outcome.validation_status == "no_sql_needed"

    def test_query_absence_from_no_tool_result_does_not_retry_by_itself(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "",
                row_count=0,
                reasoning="이 질문은 데이터베이스 조회가 필요하지 않습니다.",
                success=False,
                error="No SQL result found in agent output",
            )
        ], "너는 어떤 일을 할 수 있어?")

        assert outcome.validation_status == "no_sql_needed"

    def test_query_absence_with_execution_error_retries(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "",
                row_count=0,
                reasoning="SQL execution failed: database timeout",
                success=False,
                error="database timeout",
            )
        ], "존 존스 최근 경기 알려줘")

        assert outcome.validation_status == "retry_needed"
        assert "database timeout" in outcome.feedback

    def test_unsupported_result_routes_without_retry(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "",
                row_count=0,
                reasoning="unsupported: requested data is not represented in the schema",
            )
        ], "선수의 PPV 구매 수 알려줘")

        assert outcome.validation_status == "unsupported"

    def test_sql_tool_error_with_query_retries(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "SELECT * FROM missing_view",
                data=[],
                row_count=0,
                columns=[],
                reasoning="attempted query",
                success=False,
                error='relation "missing_view" does not exist',
            )
        ], "최근 경기 알려줘")

        assert outcome.validation_status == "retry_needed"
        assert "missing_view" in outcome.feedback

    def test_malformed_data_payload_is_invalid_result(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT 1", data={"value": 1}, columns=["value"], row_count=1)
        ], "테스트")

        assert outcome.validation_status == "invalid_result"
        assert "data must be a list" in outcome.feedback

    def test_non_object_data_row_is_invalid_result(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT 1", data=[["value", 1]], columns=["value"], row_count=1)
        ], "테스트")

        assert outcome.validation_status == "invalid_result"
        assert "data row 0" in outcome.feedback

    def test_row_count_zero_with_data_is_invalid_result(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT 1", data=[{"value": 1}], columns=["value"], row_count=0)
        ], "테스트")

        assert outcome.validation_status == "invalid_result"
        assert "row_count is 0" in outcome.feedback

    def test_dangerous_sql_retries(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("UPDATE fighter SET name = 'bad'")
        ], "테스트")

        assert outcome.validation_status == "retry_needed"
        assert "Only SELECT queries are allowed" in outcome.feedback

    def test_valid_empty_result_passes_without_retry(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "SELECT fighter_name FROM v_current_rankings WHERE weight_class_name = 'women heavyweight'",
                row_count=0,
            )
        ], "여성 헤비급 챔피언 알려줘")

        assert outcome.validation_status == "valid_empty"

    def test_ambiguous_empty_result_is_valid_empty_not_retry(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "SELECT fighter_name FROM fighter WHERE name ILIKE '%jon jons%'",
                row_count=0,
            )
        ], "존 존스 알려줘")

        assert outcome.validation_status == "valid_empty"

    def test_semantic_recent_scope_mismatch_passes_phase_a(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT fighter_name, event_date FROM v_fighter_fight_results ORDER BY event_date DESC")
        ], "존 존스 최근 경기 알려줘")

        assert outcome.validation_status == "passed"

    def test_semantic_win_rate_denominator_mismatch_passes_phase_a(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT wins * 100.0 / total_fights AS win_rate FROM fighter_record")
        ], "존 존스 승률 알려줘")

        assert outcome.validation_status == "passed"

    def test_semantic_ko_tko_missing_win_condition_passes_phase_a(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result("SELECT COUNT(*) AS ko_tko_wins FROM match WHERE method ILIKE 'KO/TKO%'")
        ], "KO/TKO 승리 수 알려줘")

        assert outcome.validation_status == "passed"

    def test_semantic_decision_participation_win_filter_passes_phase_a(self):
        from llm.graph.nodes.critic import _run_phase_a

        outcome = _run_phase_a([
            self._result(
                "SELECT COUNT(*) AS decision_fights FROM v_completed_fighter_fights WHERE result = 'win' AND method ILIKE '%DEC%'"
            )
        ], "판정으로 간 경기 수 알려줘")

        assert outcome.validation_status == "passed"


# =============================================================================
# MMAGraphService 테스트
# =============================================================================

class TestMMAGraphService:
    """MMAGraphService 유틸리티 메서드 테스트"""

    def test_build_messages_from_empty_history(self):
        from llm.service import MMAGraphService
        result = MMAGraphService.build_messages_from_history([])
        assert result == []

    def test_build_messages_from_none(self):
        from llm.service import MMAGraphService
        result = MMAGraphService.build_messages_from_history(None)
        assert result == []

    def test_build_messages_from_dict_history(self):
        from llm.service import MMAGraphService
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert result[0].content == "hello"
        assert result[1].content == "hi there"

    def test_build_messages_from_object_history(self):
        from llm.service import MMAGraphService

        class MockMsg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        history = [MockMsg("user", "q1"), MockMsg("assistant", "a1")]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 2
        assert result[0].content == "q1"

    def test_build_messages_sliding_window_100(self):
        from llm.service import MMAGraphService
        history = [{"role": "user", "content": f"msg{i}"} for i in range(150)]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 100
        assert result[0].content == "msg50"

    def test_build_messages_no_sql_context_in_content(self):
        """build_messages_from_history는 content에 SQL Context를 포함하지 않음"""
        from llm.service import MMAGraphService

        history = [
            {"role": "user", "content": "웰터급 챔피언은?"},
            {
                "role": "assistant",
                "content": "웰터급 챔피언은 Leon Edwards입니다.",
                "tool_results": [{"query": "SELECT id FROM fighter", "data": [{"id": 2386}]}],
            },
        ]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 2
        assert isinstance(result[1], AIMessage)
        assert "[SQL Context:" not in result[1].content
        assert result[1].content == "웰터급 챔피언은 Leon Edwards입니다."

    def test_extract_sql_context_from_dict_history(self):
        """dict 형태 히스토리에서 SQL 컨텍스트 추출"""
        from llm.service import MMAGraphService

        history = [
            {"role": "user", "content": "웰터급 챔피언은?"},
            {
                "role": "assistant",
                "content": "웰터급 챔피언은 Leon Edwards입니다.",
                "tool_results": [{"query": "SELECT id FROM fighter", "data": [{"id": 2386}]}],
            },
        ]
        ctx = MMAGraphService.extract_sql_context(history)
        assert len(ctx) == 1
        assert ctx[0]["data"] == [{"id": 2386}]

    def test_extract_sql_context_empty_when_no_tool_results(self):
        """tool_results가 없으면 빈 리스트 반환"""
        from llm.service import MMAGraphService

        history = [
            {"role": "assistant", "content": "일반 응답", "tool_results": None},
        ]
        ctx = MMAGraphService.extract_sql_context(history)
        assert ctx == []

    def test_extract_sql_context_from_object_history(self):
        """객체 형태 히스토리에서도 SQL 컨텍스트 추출"""
        from llm.service import MMAGraphService

        class MockMsgWithTools:
            def __init__(self, role, content, tool_results=None):
                self.role = role
                self.content = content
                self.tool_results = tool_results

        history = [
            MockMsgWithTools("assistant", "결과", [{"query": "SELECT 1", "data": [{"id": 1}]}]),
        ]
        ctx = MMAGraphService.extract_sql_context(history)
        assert len(ctx) == 1
        assert ctx[0]["query"] == "SELECT 1"

    def test_build_messages_ignores_unknown_roles(self):
        from llm.service import MMAGraphService
        history = [
            {"role": "user", "content": "q"},
            {"role": "system", "content": "ignored"},
            {"role": "assistant", "content": "a"},
        ]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 2


# =============================================================================
# state 모듈 테스트
# =============================================================================

class TestState:
    """MainState, AgentResult, reduce_agent_results 테스트"""

    def test_reduce_agent_results_empty_resets(self):
        from llm.graph.state import reduce_agent_results
        existing = [{"agent_name": "mma_analysis", "query": "q", "data": [],
                     "columns": [], "row_count": 0, "reasoning": "r"}]
        assert reduce_agent_results(existing, []) == []

    def test_reduce_agent_results_merges(self):
        from llm.graph.state import reduce_agent_results
        a = {"agent_name": "mma_analysis", "query": "", "data": [],
             "columns": [], "row_count": 0, "reasoning": ""}
        b = {"agent_name": "fighter_comparison", "query": "", "data": [],
             "columns": [], "row_count": 0, "reasoning": ""}
        result = reduce_agent_results([a], [b])
        assert len(result) == 2

    def test_error_agent_result(self):
        from llm.graph.state import _error_agent_result
        r = _error_agent_result("test_agent", "something failed")
        assert r["agent_name"] == "test_agent"
        assert r["reasoning"] == "something failed"
        assert r["row_count"] == 0


# =============================================================================
# text_response 노드 테스트
# =============================================================================

class TestTextResponseNode:
    """text_response_node는 SQL agent reasoning을 사용자 응답으로 재사용하지 않음"""

    @pytest.mark.asyncio
    async def test_single_agent_result_still_uses_response_llm(self):
        from llm.graph.nodes.text_response import text_response_node

        llm = AsyncMock()
        llm.ainvoke.return_value = AIMessage(content="사용자에게 보여줄 응답")

        result = await text_response_node({
            "resolved_query": "존 존스 전적 알려줘",
            "agent_results": [{
                "agent_name": "mma_analysis",
                "query": "SELECT id, name FROM fighter",
                "data": [{"id": 1, "name": "jon jones"}],
                "columns": ["id", "name"],
                "row_count": 1,
                "reasoning": "private reasoning with id 1",
            }],
        }, llm)

        assert llm.ainvoke.await_count == 1
        assert result["final_response"] == "사용자에게 보여줄 응답"
        assert "private reasoning" not in result["final_response"]

    @pytest.mark.asyncio
    async def test_response_failure_does_not_fallback_to_reasoning(self):
        from llm.graph.nodes.text_response import text_response_node

        llm = AsyncMock()
        llm.ainvoke.side_effect = TimeoutError("timeout")

        result = await text_response_node({
            "resolved_query": "존 존스 전적 알려줘",
            "agent_results": [{
                "agent_name": "mma_analysis",
                "query": "SELECT id, name FROM fighter",
                "data": [{"id": 1, "name": "jon jones"}],
                "columns": ["id", "name"],
                "row_count": 1,
                "reasoning": "private reasoning with id 1",
            }],
        }, llm)

        assert result["final_response"] == "응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        assert "private reasoning" not in result["final_response"]
