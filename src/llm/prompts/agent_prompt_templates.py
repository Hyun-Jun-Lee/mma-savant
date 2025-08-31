"""
Agent prompt template generators for Two-Phase Reasoning System
"""

import json
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
    phase1_data: Dict[str, Any], 
    supported_charts: Dict[str, Any]
) -> ChatPromptTemplate:
    """Create Phase 2 prompt template with chart info"""
    context = {
        "phase1_results": phase1_data,
        "supported_charts": supported_charts
    }
    
    phase2_prompt_text = create_phase_prompt(2, context)
    
    # Add chart options
    charts_description = "\n\n## Available Charts:\n"
    for chart_id, info in supported_charts.items():
        charts_description += f"**{chart_id}**: {info['description']}\n"
        charts_description += f"   - Use: {info['use_cases']}\n"
        charts_description += f"   - Needs: {info['data_needs']}\n\n"
    
    enhanced_prompt = phase2_prompt_text + charts_description
    enhanced_prompt += "\n\nSelect appropriate visualization and provide structured JSON output."
    
    return ChatPromptTemplate.from_messages([
        ("system", enhanced_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


def prepare_phase2_input(
    user_query: str,
    phase1_data: Dict[str, Any],
    data_analysis: Dict[str, Any],
    supported_charts: Dict[str, Any]
) -> str:
    """Prepare Phase 2 input data"""
    return f"""
## User Query: {user_query}

## Phase 1 Summary
- Tools: {len(phase1_data.get('tools_executed', []))}
- Data types: {', '.join(data_analysis.get('data_types', ['unknown']))}
- Quality: {data_analysis.get('quality', 'unknown')}

## Collected Data
{json.dumps(phase1_data.get('collected_data', {}), ensure_ascii=False, indent=2)}

## Task
1. Analyze data structure
2. Select best visualization
3. Format data for chart
4. Generate insights
5. Return structured JSON

Output required JSON with: selected_visualization, visualization_data, insights, metadata.
"""


def create_charts_description(supported_charts: Dict[str, Any]) -> str:
    """Convert charts info to prompt text"""
    description = "## Available Charts:\n\n"
    
    for chart_id, info in supported_charts.items():
        description += f"**{chart_id}**: {info.get('description', 'No description')}\n"
        description += f"- Use: {info.get('use_cases', 'General')}\n"
        description += f"- Needs: {info.get('data_needs', 'Any data')}\n\n"
    
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