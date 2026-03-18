"""StateGraph 노드 단위 테스트"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# =============================================================================
# result_analyzer 노드 테스트 (순수 규칙 기반)
# =============================================================================

class TestResultAnalyzer:
    """result_analyzer_node 테스트 - 규칙 기반 시각화 판단"""

    @pytest.fixture
    def state_factory(self):
        def _make(data, columns, row_count, success=True):
            return {
                "messages": [HumanMessage(content="test")],
                "sql_result": {
                    "success": success,
                    "data": data,
                    "columns": columns,
                    "row_count": row_count,
                },
            }
        return _make

    @pytest.mark.asyncio
    async def test_no_sql_result_returns_text(self):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = {"messages": [], "sql_result": None}
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"

    @pytest.mark.asyncio
    async def test_failed_sql_returns_text(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory([], [], 0, success=False)
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"

    @pytest.mark.asyncio
    async def test_zero_rows_returns_text(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory([], [], 0)
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"

    @pytest.mark.asyncio
    async def test_single_row_few_columns_returns_text(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory(
            [{"name": "Jones", "wins": 28}],
            ["name", "wins"],
            1,
        )
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"

    @pytest.mark.asyncio
    async def test_single_row_many_numeric_columns_returns_visualization(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory(
            [{"name": "Jones", "wins": 28, "losses": 1, "ko": 10, "sub": 7}],
            ["name", "wins", "losses", "ko", "sub"],
            1,
        )
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "visualization"

    @pytest.mark.asyncio
    async def test_single_row_many_text_columns_returns_text(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory(
            [{"a": "x", "b": "y", "c": "z", "d": "w"}],
            ["a", "b", "c", "d"],
            1,
        )
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"

    @pytest.mark.asyncio
    async def test_multiple_rows_with_numeric_returns_visualization(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory(
            [{"name": "A", "wins": 10}, {"name": "B", "wins": 8}],
            ["name", "wins"],
            2,
        )
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "visualization"

    @pytest.mark.asyncio
    async def test_multiple_rows_no_numeric_returns_text(self, state_factory):
        from llm.graph.nodes.result_analyzer import result_analyzer_node
        state = state_factory(
            [{"name": "A", "team": "X"}, {"name": "B", "team": "Y"}],
            ["name", "team"],
            2,
        )
        result = await result_analyzer_node(state)
        assert result["response_mode"] == "text"


# =============================================================================
# intent_classifier 노드 테스트
# =============================================================================

class TestIntentClassifier:
    """intent_classifier_node LLM 기반 분류 테스트"""

    @pytest.mark.asyncio
    async def test_empty_messages_returns_general(self):
        from llm.graph.nodes.intent_classifier import intent_classifier_node
        state = {"messages": []}
        result = await intent_classifier_node(state, llm=None)
        assert result["intent"] == "general"

    @pytest.mark.asyncio
    async def test_llm_failure_returns_sql_needed(self):
        """LLM 호출 실패 시 안전하게 sql_needed로 fallback"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node
        mock_llm = MagicMock()
        mock_llm.with_structured_output.side_effect = Exception("LLM error")
        state = {"messages": [HumanMessage(content="존 존스 전적")]}
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "sql_needed"

    @pytest.mark.asyncio
    async def test_followup_corrected_without_history(self):
        """히스토리 없는데 followup으로 분류되면 sql_needed로 보정"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node, IntentClassification
        mock_result = IntentClassification(intent="followup")
        mock_structured = AsyncMock(ainvoke=AsyncMock(return_value=mock_result))
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        # 메시지 1개만 → has_history=False
        state = {"messages": [HumanMessage(content="그중에서 KO는?")]}
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "sql_needed"

    @pytest.mark.asyncio
    async def test_followup_allowed_with_history(self):
        """히스토리 있으면 followup 분류 허용"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node, IntentClassification
        mock_result = IntentClassification(intent="followup")
        mock_structured = AsyncMock(ainvoke=AsyncMock(return_value=mock_result))
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        state = {
            "messages": [
                HumanMessage(content="존 존스 전적"),
                AIMessage(content="존 존스는 28승 1패입니다."),
                HumanMessage(content="그중에서 KO는?"),
            ]
        }
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "followup"

    @pytest.mark.asyncio
    async def test_sql_needed_classification(self):
        """LLM이 sql_needed로 분류한 경우"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node, IntentClassification
        mock_result = IntentClassification(intent="sql_needed")
        mock_structured = AsyncMock(ainvoke=AsyncMock(return_value=mock_result))
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        state = {"messages": [HumanMessage(content="최근 경기가 언제야?")]}
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "sql_needed"

    @pytest.mark.asyncio
    async def test_sql_needed_corrected_with_history(self):
        """히스토리 있는데 sql_needed로 분류되면 followup으로 보정"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node, IntentClassification
        mock_result = IntentClassification(intent="sql_needed")
        mock_structured = AsyncMock(ainvoke=AsyncMock(return_value=mock_result))
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        state = {
            "messages": [
                HumanMessage(content="존 존스 전적"),
                AIMessage(content="존 존스는 28승 1패입니다."),
                HumanMessage(content="서브미션 승리 Top 5 알려줘"),
            ]
        }
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "followup"

    @pytest.mark.asyncio
    async def test_general_classification(self):
        """LLM이 general로 분류한 경우"""
        from llm.graph.nodes.intent_classifier import intent_classifier_node, IntentClassification
        mock_result = IntentClassification(intent="general")
        mock_structured = AsyncMock(ainvoke=AsyncMock(return_value=mock_result))
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        state = {"messages": [HumanMessage(content="안녕하세요")]}
        result = await intent_classifier_node(state, llm=mock_llm)
        assert result["intent"] == "general"


# =============================================================================
# graph_builder 테스트
# =============================================================================

class TestGraphBuilder:
    """build_mma_graph 조립 및 컴파일 테스트"""

    def test_graph_compiles_with_mock_llm(self):
        from llm.graph.graph_builder import build_mma_graph
        mock_llm = MagicMock()
        compiled = build_mma_graph(mock_llm)
        assert compiled is not None

    def test_route_by_intent_general(self):
        from llm.graph.graph_builder import route_by_intent
        assert route_by_intent({"intent": "general"}) == "general"

    def test_route_by_intent_sql(self):
        from llm.graph.graph_builder import route_by_intent
        assert route_by_intent({"intent": "sql_needed"}) == "sql_needed"

    def test_route_by_intent_followup(self):
        from llm.graph.graph_builder import route_by_intent
        assert route_by_intent({"intent": "followup"}) == "followup"

    def test_route_by_intent_invalid_raises(self):
        from llm.graph.graph_builder import route_by_intent
        with pytest.raises(ValueError, match="Invalid intent"):
            route_by_intent({})

    def test_route_by_intent_unknown_value_raises(self):
        from llm.graph.graph_builder import route_by_intent
        with pytest.raises(ValueError, match="Invalid intent"):
            route_by_intent({"intent": "unknown"})

    def test_route_by_response_mode_visualization(self):
        from llm.graph.graph_builder import route_by_response_mode
        assert route_by_response_mode({"response_mode": "visualization"}) == "visualization"

    def test_route_by_response_mode_text(self):
        from llm.graph.graph_builder import route_by_response_mode
        assert route_by_response_mode({"response_mode": "text"}) == "text"

    def test_route_by_response_mode_invalid_raises(self):
        from llm.graph.graph_builder import route_by_response_mode
        with pytest.raises(ValueError, match="Invalid response_mode"):
            route_by_response_mode({})

    def test_route_by_response_mode_unknown_value_raises(self):
        from llm.graph.graph_builder import route_by_response_mode
        with pytest.raises(ValueError, match="Invalid response_mode"):
            route_by_response_mode({"response_mode": "unknown"})


# =============================================================================
# visualize 노드 JSON 파싱 테스트
# =============================================================================

class TestVisualizeJsonParsing:
    """visualize 노드의 JSON 파싱 로직 테스트"""

    def test_direct_json(self):
        from llm.graph.nodes.visualize import _parse_visualization_json
        data = '{"selected_visualization": "bar_chart", "visualization_data": {"title": "t"}, "insights": []}'
        result = _parse_visualization_json(data)
        assert result["selected_visualization"] == "bar_chart"

    def test_json_in_code_block(self):
        from llm.graph.nodes.visualize import _parse_visualization_json
        data = '```json\n{"selected_visualization": "pie_chart", "visualization_data": {}, "insights": []}\n```'
        result = _parse_visualization_json(data)
        assert result["selected_visualization"] == "pie_chart"

    def test_invalid_json_returns_none(self):
        from llm.graph.nodes.visualize import _parse_visualization_json
        result = _parse_visualization_json("this is not json at all")
        assert result is None

    def test_json_with_extra_text(self):
        from llm.graph.nodes.visualize import _parse_visualization_json
        data = 'Here is the data: {"selected_visualization": "table", "visualization_data": {"title": "x"}} end'
        result = _parse_visualization_json(data)
        assert result is not None
        assert result["selected_visualization"] == "table"


# =============================================================================
# text_response 노드 JSON 파싱 테스트
# =============================================================================

class TestTextResponseJsonParsing:
    """text_response 노드의 JSON 파싱 로직 테스트"""

    def test_direct_json(self):
        from llm.graph.nodes.text_response import _parse_text_response_json
        data = '{"visualization_data": {"content": "hello"}, "insights": ["a"]}'
        result = _parse_text_response_json(data)
        assert result["visualization_data"]["content"] == "hello"

    def test_json_in_code_block(self):
        from llm.graph.nodes.text_response import _parse_text_response_json
        data = '```json\n{"visualization_data": {"content": "hi"}, "insights": []}\n```'
        result = _parse_text_response_json(data)
        assert result is not None

    def test_invalid_json_returns_none(self):
        from llm.graph.nodes.text_response import _parse_text_response_json
        result = _parse_text_response_json("not json")
        assert result is None


# =============================================================================
# sql_agent 노드 결과 추출 테스트
# =============================================================================

class TestSqlAgentExtraction:
    """sql_agent 노드의 SQL 결과 추출 테스트"""

    def test_extract_from_tool_message(self):
        from llm.graph.nodes.sql_agent import _extract_sql_result_from_messages
        tool_content = json.dumps({
            "success": True, "data": [{"name": "test"}],
            "columns": ["name"], "row_count": 1, "query": "SELECT 1",
        })
        messages = [
            HumanMessage(content="test"),
            AIMessage(content="running query"),
            ToolMessage(content=tool_content, tool_call_id="1"),
        ]
        result = _extract_sql_result_from_messages(messages)
        assert result["success"] is True
        assert result["row_count"] == 1

    def test_no_tool_message_returns_failure(self):
        from llm.graph.nodes.sql_agent import _extract_sql_result_from_messages
        messages = [HumanMessage(content="test"), AIMessage(content="ok")]
        result = _extract_sql_result_from_messages(messages)
        assert result["success"] is False

    def test_invalid_json_tool_message(self):
        from llm.graph.nodes.sql_agent import _extract_sql_result_from_messages
        messages = [ToolMessage(content="not json", tool_call_id="1")]
        result = _extract_sql_result_from_messages(messages)
        assert result["success"] is False


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

    def test_build_messages_sliding_window(self):
        from llm.service import MMAGraphService
        history = [{"role": "user", "content": f"msg{i}"} for i in range(30)]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 20
        assert result[0].content == "msg10"

    def test_build_messages_ignores_unknown_roles(self):
        from llm.service import MMAGraphService
        history = [
            {"role": "user", "content": "q"},
            {"role": "system", "content": "ignored"},
            {"role": "assistant", "content": "a"},
        ]
        result = MMAGraphService.build_messages_from_history(history)
        assert len(result) == 2
