from typing import List, Dict, Any, Optional
import json
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from tools.load_tools import mcp
from database.connection.postgres_conn import get_async_db_context


@mcp.tool()
async def execute_raw_sql_query(
    query: str,
    description: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    사전 정의된 도구로 답변할 수 없는 복잡한 요청을 위한 직접 SQL 쿼리 실행 도구.
    보안을 위해 SELECT 문만 허용하며, 결과를 제한합니다.
    
    중요: 모든 테이블명은 단수형을 사용합니다
    - 'match' (matches X)
    - 'fighter' (fighters X)
    - 'event' (events X)
    - 'ranking' (rankings X)
    
    Args:
        query (str): 실행할 SQL 쿼리 (SELECT 문만 허용, 단수형 테이블명 사용)
        description (str, optional): 쿼리 목적 설명
        limit (int): 최대 반환 행 수 (기본값: 100, 최대: 1000)
    
    Returns:
        Dict[str, Any]: 쿼리 결과와 메타데이터
    """
    
    # 보안 검증: SELECT 문만 허용
    query_stripped = query.strip().upper()
    if not query_stripped.startswith('SELECT'):
        return {
            "error": "보안상 SELECT 문만 허용됩니다",
            "allowed_operations": ["SELECT"]
        }
    
    # 위험한 키워드 차단
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in query_stripped:
            return {
                "error": f"보안상 '{keyword}' 문은 허용되지 않습니다",
                "query": query
            }
    
    # 결과 제한
    limit = min(max(1, limit), 1000)
    
    # LIMIT 절이 없으면 추가
    if 'LIMIT' not in query_stripped:
        query = f"{query.rstrip(';')} LIMIT {limit}"
    
    try:
        async with get_async_db_context() as session:
            result = await session.execute(text(query))
            rows = result.fetchall()
            
            # 결과를 딕셔너리 형태로 변환
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = []
            
            return {
                "success": True,
                "description": description,
                "query": query,
                "row_count": len(data),
                "data": data,
                "columns": list(result.keys()) if rows else []
            }
            
    except SQLAlchemyError as e:
        return {
            "error": f"SQL 실행 오류: {str(e)}",
            "query": query,
            "success": False
        }
    except Exception as e:
        return {
            "error": f"예상치 못한 오류: {str(e)}",
            "query": query,
            "success": False
        }


# get_database_schema_info() function removed
# Schema information is now provided directly in Phase 1 prompts via schema_prompt.json
