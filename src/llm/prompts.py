"""
Two-Phase Reasoning System prompt templates
Phase 1: Intent analysis + SQL query execution
Phase 2: Data processing + visualization
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate


# =============================================================================
# Phase 1: SQL Query Analysis & Data Collection
# =============================================================================

PHASE1_PROMPT = """
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


# =============================================================================
# Phase 2: Data Processing & Visualization
# =============================================================================

PHASE2_PROMPT = """
You are MMA Savant Phase 2. Analyze SQL results and output ONLY valid JSON.

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
- Ensure valid JSON format
"""


# =============================================================================
# Prompt Generation Functions
# =============================================================================

def get_phase1_prompt() -> str:
    """
    Return Phase 1 prompt with dynamic schema loading

    Returns:
        str: Phase 1 prompt with database schema injected
    """
    from common.utils import load_schema_prompt

    # Load formatted schema text
    schema_text = load_schema_prompt()

    # Inject schema into prompt template
    return PHASE1_PROMPT.format(schema_info=schema_text)


def get_phase2_prompt() -> str:
    """
    Return Phase 2 prompt for data processing and visualization

    Returns:
        str: Phase 2 prompt text
    """
    return PHASE2_PROMPT


# =============================================================================
# Template Creation Functions
# =============================================================================

def create_phase1_prompt_template() -> ChatPromptTemplate:
    """
    Create LangChain ChatPromptTemplate for Phase 1

    Returns:
        ChatPromptTemplate: Configured prompt template for Phase 1 agent
    """
    phase1_prompt_text = get_phase1_prompt()

    return ChatPromptTemplate.from_messages([
        ("system", phase1_prompt_text),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


def prepare_phase2_input(
    user_query: str,
    phase1_data: Dict[str, Any],
) -> str:
    """
    Prepare Phase 2 input data from Phase 1 results

    Args:
        user_query: Original user query
        phase1_data: Results from Phase 1 execution

    Returns:
        str: Formatted input string for Phase 2
    """
    # Extract SQL execution results
    sql_query = phase1_data.get('sql_query', '')
    sql_success = phase1_data.get('sql_success', False)
    sql_data = phase1_data.get('sql_data', [])
    sql_columns = phase1_data.get('sql_columns', [])
    row_count = phase1_data.get('row_count', 0)

    # Handle SQL execution failure
    if not sql_success:
        return f"""
## User Query: {user_query}

## Phase 1 Results
### SQL Execution Failed
Query attempted: {sql_query}
Error: SQL query execution failed. Please check the query and try again.

## Your Task (Phase 2):
Unable to provide visualization due to SQL execution failure.
Please inform the user about the error and suggest corrections if possible.
"""

    # Format successful SQL results
    return f"""
## User Query: {user_query}

## Phase 1 Results
### SQL Query Executed:
```sql
{sql_query}
```

### Data Retrieved:
- Rows: {row_count}
- Columns: {', '.join(sql_columns) if sql_columns else 'No columns'}

### Raw Data:
{str(sql_data)}

## Your Task (Phase 2):
1. Analyze the structure and content of the SQL query results
2. Determine what type of MMA information we have (fighter stats, match results, rankings, etc.)
3. Select the most appropriate visualization from available charts
4. Format the data for the selected visualization
5. Generate key insights from the data

Required output: Provide a structured response with your selected visualization type, formatted data, and insights.
"""
