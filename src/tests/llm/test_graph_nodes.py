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
                     "columns": [], "row_count": 0, "needs_visualization": False,
                     "reasoning": "r"}]
        assert reduce_agent_results(existing, []) == []

    def test_reduce_agent_results_merges(self):
        from llm.graph.state import reduce_agent_results
        a = {"agent_name": "mma_analysis", "query": "", "data": [],
             "columns": [], "row_count": 0, "needs_visualization": False, "reasoning": ""}
        b = {"agent_name": "fighter_comparison", "query": "", "data": [],
             "columns": [], "row_count": 0, "needs_visualization": False, "reasoning": ""}
        result = reduce_agent_results([a], [b])
        assert len(result) == 2

    def test_error_agent_result(self):
        from llm.graph.state import _error_agent_result
        r = _error_agent_result("test_agent", "something failed")
        assert r["agent_name"] == "test_agent"
        assert r["reasoning"] == "something failed"
        assert r["row_count"] == 0
        assert r["needs_visualization"] is False
