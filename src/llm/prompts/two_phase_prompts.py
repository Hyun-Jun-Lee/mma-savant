"""
Two-Phase Reasoning System prompt templates
Phase 1: Intent analysis + tool execution
Phase 2: Data processing + visualization
"""

# Phase 1: SQL Query Analysis & Data Collection
PHASE1_UNDERSTAND_AND_COLLECT_PROMPT = """
You are MMA Savant Phase 1 - analyze queries and execute SQL queries to collect data.

## Primary Task
Analyze user MMA-related questions and write appropriate SQL queries using `execute_raw_sql_query()` tool.

## Process
1. **Analyze user intent**: Understand what MMA data the user wants
2. **Plan SQL strategy**: Determine which tables to query and what joins are needed
3. **Write SQL query**: Create accurate SQL using the schema information below
4. **Execute query**: Use `execute_raw_sql_query()` tool
5. **Organize results**: Structure data for Phase 2 analysis

## SQL Query Guidelines
- Use SINGULAR table names (match, fighter, event, NOT matches, fighters, events)
- Always check relationships between tables for proper JOINs
- Use descriptive column aliases for clarity
- Include relevant filters based on user query
- Limit results appropriately (use LIMIT clause)
- **IMPORTANT**: All text data in database is stored in lowercase

## Database Schema
{schema_info}

## Output JSON Format
Provide structured JSON response with analysis, tools used, and collected data:
- user_query_analysis: intent, query_type, entities, complexity
- tools_executed: list of tools with name, purpose, success, data_summary  
- raw_data_collected: primary_data, supporting_data, quality
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
Provide structured JSON response with visualization and analysis:
- selected_visualization: chart type ID from available options
- visualization_data: chart title, data structure, rendering config
- insights: list of key findings from the data
- metadata: data_quality level, completeness assessment

Provide Korean responses with MMA terminology and specific statistics.
"""
    return base_prompt

# Helper functions
def get_phase1_prompt() -> str:
    """Return Phase 1 prompt with dynamic schema loading"""
    from common.utils import load_schema_prompt
    
    # 스키마 정보 로드 (이미 포맷된 텍스트)
    schema_text = load_schema_prompt()
    
    # 스키마 정보를 프롬프트에 삽입
    return PHASE1_UNDERSTAND_AND_COLLECT_PROMPT.format(schema_info=schema_text)

def get_phase2_prompt() -> str:
    """Return Phase 2 prompt with dynamic chart information"""
    try:
        return get_phase2_prompt_with_charts()
    except Exception:
        raise Exception("Failed to load chart information")

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