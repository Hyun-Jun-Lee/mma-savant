"""
Two-Phase Reasoning System prompt templates
Phase 1: Intent analysis + tool execution
Phase 2: Data processing + visualization
"""

# Phase 1: Intent Analysis & Data Collection
PHASE1_UNDERSTAND_AND_COLLECT_PROMPT = """
You are MMA Savant Phase 1 - analyze queries and collect data.

## Tasks
1. Analyze user intent
2. Select appropriate tools
3. Execute tools systematically
4. Organize data for Phase 2

## Tool Priority
1. Start with `check_available_tools()`
2. Use specific tools (by_id, by_name) over search
3. Try basic info tools before analysis tools

## Rules
- Be systematic - gather complete data
- Use IDs when available
- Handle errors with alternatives
- Collect all necessary information

## Output JSON Format
```json
{
  "user_query_analysis": {
    "intent": "what user wants",
    "query_type": "fighter_info|match_analysis|ranking|comparison",
    "entities": ["entity1", "entity2"],
    "complexity": "simple|moderate|complex"
  },
  "tools_executed": [{
    "tool_name": "function_name",
    "purpose": "why used",
    "success": true,
    "data_summary": "brief summary"
  }],
  "raw_data_collected": {
    "primary_data": "main info",
    "supporting_data": "additional context",
    "quality": "complete|partial|insufficient"
  }
}
```

Examples:
- "Jon Jones info" → get_fighter_info_by_name("Jon Jones")
"""

# Phase 2: Data Processing & Visualization
def get_phase2_prompt_with_charts() -> str:
    """Get Phase 2 prompt with dynamic chart information"""
    try:
        # Import based on system-reminder info showing llm.chart_loader path
        from llm.chart_loader import get_supported_charts
    except ImportError:
        try:
            from llm.config.chart_loader import get_supported_charts
        except ImportError:
            from ..config.chart_loader import get_supported_charts
    
    supported_charts = get_supported_charts()
    
    # Build chart selection logic dynamically
    chart_logic = []
    chart_examples = []
    
    for chart_id, info in supported_charts.items():
        chart_logic.append(f"- {info['best_for']} → `{chart_id}`")
        chart_examples.append(f"**{chart_id}**: {info['description']}")
    
    base_prompt = f"""
You are MMA Savant Phase 2 - analyze data and select optimal visualizations.

## Tasks
1. Analyze Phase 1 data structure
2. Select best visualization from supported charts
3. Process data into chart format
4. Generate insights

## Chart Selection Logic
{chr(10).join(chart_logic)}

## Available Charts
{chr(10).join(chart_examples)}

## Data Processing
1. Extract relevant fields
2. Clean and normalize values
3. Structure per chart requirements
4. Add rendering metadata

## Output JSON Format
```json
{{
  "selected_visualization": "chart_type_id",
  "visualization_data": {{
    "title": "Chart title",
    "data": "Chart-specific structure",
    "config": "Rendering config"
  }},
  "insights": ["finding 1", "finding 2"],
  "metadata": {{
    "data_quality": "high|medium|low",
    "completeness": "complete|partial|limited"
  }}
}}
```

Provide Korean responses with MMA terminology and specific statistics.
"""
    return base_prompt

# Static fallback prompt
PHASE2_PROCESS_AND_VISUALIZE_PROMPT = """
You are MMA Savant Phase 2 - analyze data and select optimal visualizations.

## Tasks
1. Analyze Phase 1 data structure
2. Select best visualization from supported charts
3. Process data into chart format
4. Generate insights

## Data Processing
1. Extract relevant fields
2. Clean and normalize values
3. Structure per chart requirements
4. Add rendering metadata

## Output JSON Format
```json
{
  "selected_visualization": "chart_type_id",
  "visualization_data": {
    "title": "Chart title",
    "data": "Chart-specific structure",
    "config": "Rendering config"
  },
  "insights": ["finding 1", "finding 2"],
  "metadata": {
    "data_quality": "high|medium|low",
    "completeness": "complete|partial|limited"
  }
}
```

Provide Korean responses with MMA terminology and specific statistics.
"""

# Helper functions
def get_phase1_prompt() -> str:
    """Return Phase 1 prompt"""
    return PHASE1_UNDERSTAND_AND_COLLECT_PROMPT

def get_phase2_prompt() -> str:
    """Return Phase 2 prompt with dynamic chart information"""
    try:
        return get_phase2_prompt_with_charts()
    except Exception:
        # Fallback to static prompt if chart loading fails
        return PHASE2_PROCESS_AND_VISUALIZE_PROMPT

def get_two_phase_system_prompt() -> str:
    """Two-Phase system overview"""
    return """
MMA Savant with Two-Phase Reasoning:
Phase 1: Understand query, select tools, collect data
Phase 2: Process data, create visualizations, generate response
"""

def validate_phase1_output(output: dict) -> bool:
    """Validate Phase 1 output format"""
    required = ["user_query_analysis", "tools_executed", "raw_data_collected"]
    return all(key in output for key in required)

def validate_phase2_output(output: dict) -> bool:
    """Validate Phase 2 output format"""
    required = ["selected_visualization", "visualization_data", "insights"]
    return all(key in output for key in required)

def create_phase_prompt(phase: int, context: dict = None) -> str:
    """Create phase prompt with context"""
    if phase == 1:
        base_prompt = get_phase1_prompt()
        if context and "available_tools" in context:
            tools_info = "\n\n## Available Tools:\n" + "\n".join(f"- {tool}" for tool in context["available_tools"])
            base_prompt += tools_info
        return base_prompt
    
    elif phase == 2:
        base_prompt = get_phase2_prompt()
        if context and "phase1_results" in context:
            base_prompt += f"\n\n## Phase 1 Results:\n{context['phase1_results']}\n"
        return base_prompt
    
    else:
        raise ValueError("Phase must be 1 or 2")