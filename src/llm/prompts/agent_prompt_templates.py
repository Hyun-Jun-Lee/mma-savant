"""
Agent prompt template generators for Two-Phase Reasoning System
"""

from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate

from .two_phase_prompts import get_phase1_prompt, create_phase_prompt


def create_phase1_prompt_template() -> ChatPromptTemplate:
    """Create Phase 1 prompt template"""
    phase1_prompt_text = get_phase1_prompt()
    
    return ChatPromptTemplate.from_messages([
        ("system", phase1_prompt_text),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


def create_phase2_prompt_template(
) -> ChatPromptTemplate:
    """Create Phase 2 prompt template with chart info"""
    # Use the dynamic chart-aware prompt directly
    from .two_phase_prompts import get_phase2_prompt_with_charts
    
    phase2_prompt_text = get_phase2_prompt_with_charts()
    
    return ChatPromptTemplate.from_messages([
        ("system", phase2_prompt_text),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


def prepare_phase2_input(
    user_query: str,
    phase1_data: Dict[str, Any],
) -> str:
    """Prepare Phase 2 input data - pass raw phase1 data for LLM to analyze"""
    # collected_data만 추출 (success 등 메타데이터 제외)
    collected_data = phase1_data.get('collected_data', {})
    tools_executed = phase1_data.get('tools_executed', [])
    
    # 사용된 도구 정보
    tools_info = ""
    for tool in tools_executed:
        tools_info += f"- {tool.get('tool', 'unknown')}\n"
    
    return f"""
## User Query: {user_query}

## Phase 1 Results
### Tools Used ({len(tools_executed)}):
{tools_info if tools_info else "No tools executed"}

### Raw Data:
{str(collected_data)}

## Your Task (Phase 2):
1. Analyze the structure and content of the collected data
2. Determine what type of information we have (fighter stats, match results, rankings, etc.)
3. Select the most appropriate visualization from available charts
4. Format the data for the selected visualization
5. Generate key insights from the data

Required output: Provide a structured response with your selected visualization type, formatted data, and insights.
"""


def create_charts_description(supported_charts: Dict[str, Any]) -> str:
    """Convert charts info to prompt text"""
    description = ""
    
    for chart_id, info in supported_charts.items():
        description += f"**{chart_id}**: {info.get('description', 'No description')}\n"
        description += f"- Best for: {info.get('best_for', 'General use')}\n"
        description += f"- Data requirements: {info.get('data_requirements', 'Any data')}\n\n"
    
    return description


def enhance_prompt_with_context(
    base_prompt: str,
    context: Dict[str, Any]
) -> str:
    """Enhance prompt with context info"""
    enhanced = base_prompt
    
    if 'supported_charts' in context:
        charts_info = create_charts_description(context['supported_charts'])
        enhanced += f"\n\n{charts_info}"
    
    if 'phase1_results' in context:
        phase1_summary = context['phase1_results']
        tools_count = len(phase1_summary.get('tools_executed', []))
        enhanced += f"\n\n## Phase 1 Results:\n"
        enhanced += f"- Tools: {tools_count}\n"
        enhanced += f"- Data: {'Yes' if phase1_summary.get('collected_data') else 'No'}\n"
    
    return enhanced


def create_execution_prompt_for_phase(
    phase: int,
    user_query: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Create execution prompt for specific phase"""
    if phase == 1:
        return f"""
User Query: {user_query}

Phase 1 Goals:
1. Analyze user intent
2. Select and execute appropriate tools
3. Collect complete data for Phase 2

Execute tools systematically.
"""
    
    elif phase == 2:
        phase1_data = context.get('phase1_data', {}) if context else {}
        return f"""
User Query: {user_query}

Phase 2 Goals:
1. Analyze collected data
2. Select best visualization
3. Format data for chart
4. Generate insights

Phase 1 Results:
- Tools used: {len(phase1_data.get('tools_executed', []))}
- Data collected: {bool(phase1_data.get('collected_data'))}

Provide structured JSON response with optimal visualization.
"""
    
    else:
        raise ValueError("Phase must be 1 or 2")