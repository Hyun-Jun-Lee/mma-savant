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
- **Method column patterns**: Use ILIKE for flexible matching
    - KO/TKO victories: `WHERE m.method ILIKE '%ko%'`
    - Submissions: `WHERE m.method ILIKE '%sub%'`
    - Decisions: `WHERE m.method ILIKE '%dec%'`

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
    """Get Phase 2 prompt with static chart information"""

    base_prompt = """You are MMA Savant Phase 2. Analyze SQL results and output ONLY valid JSON.

## Chart Options
- table: detailed data comparison
- bar_chart: category comparison
- pie_chart: proportions/distribution
- line_chart: trends over time
- scatter_plot: correlation analysis
- text_summary: insights/simple answers

## Required Output
Return ONLY a valid JSON object with this exact structure:
```json
{
    "selected_visualization": "chart_type",
    "visualization_data": {
        "title": "차트 제목",
        "data": [...],
        "x_axis": "field_name",
        "y_axis": "field_name"
    },
    "insights": ["insight1", "insight2", "insight3"]
}
```

IMPORTANT:
- Output ONLY the JSON object, no additional text
- Use Korean for title and insights
- Ensure valid JSON format"""
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