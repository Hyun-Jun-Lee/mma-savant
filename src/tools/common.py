from sqlalchemy import text
from typing import List, Dict

from tools.base import mcp
from database.connection.postgres_conn import get_async_db_context

@mcp.tool
async def execute_sql_query(query: str) -> List[Dict]:
    """
    Execute raw SQL query on the UFC database and return results as list of dicts.
    Only SELECT queries are allowed. DO NOT modify data.
    """
    async with get_async_db_context() as session:
        result = await session.execute(text(query))
        rows = result.mappings().all()
        return [dict(row) for row in rows]