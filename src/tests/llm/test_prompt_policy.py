from llm import prompts as sql_prompts
from llm.graph import prompts as graph_prompts


def test_sql_agent_prompt_uses_verification_decision_tree():
    prompt = sql_prompts.SQL_AGENT_PROMPT

    assert "Verify data characteristics before main query (MANDATORY)" not in prompt
    assert "Before the main query, decide whether a verification query is required" in prompt
    assert "Run a verification query only if" in prompt
    assert "Do not run a verification query if" in prompt
    assert "Skipping verification step" not in prompt


def test_sql_prompts_include_canonical_metric_definitions():
    for prompt in (sql_prompts.SQL_AGENT_PROMPT, sql_prompts.FIGHTER_COMPARISON_PROMPT):
        assert "## Canonical Metric Definitions" in prompt
        assert "win_rate = wins / (wins + losses + draws + no_contests)" in prompt
        assert "finish_rate = finish_wins / total_completed_fights" in prompt
        assert "COALESCE(bout_status, 'completed') NOT IN" in prompt


def test_response_style_fragments_are_node_specific():
    assert "GENERAL_MMA_STYLE" in dir(graph_prompts)
    assert "SQL_GROUNDED_RESPONSE_STYLE" in dir(graph_prompts)
    assert "VISUALIZATION_DECISION_STYLE" in dir(graph_prompts)

    assert "제공된 SQL 결과 데이터만 사용" not in graph_prompts.DIRECT_RESPONSE_PROMPT
    assert "제공된 SQL 결과 데이터만 사용" in graph_prompts.TEXT_RESPONSE_PROMPT
    assert "실제 반환된 컬럼" in graph_prompts.VISUALIZE_PROMPT


def test_supervisor_prompt_distinguishes_group_comparison_from_named_fighters():
    prompt = graph_prompts.SUPERVISOR_PROMPT

    assert "Use only when the question names two or more specific fighters" in prompt
    assert "group comparisons" in prompt
    assert "라이트급 상위 5명 테이크다운 비교" in prompt


def test_sql_grounded_response_refuses_unsupported_data():
    assert "current database cannot answer" in graph_prompts.SQL_GROUNDED_RESPONSE_STYLE
    assert "Do not infer it from model knowledge" in graph_prompts.SQL_GROUNDED_RESPONSE_STYLE
