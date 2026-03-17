"""SQL 실행 도구 모듈"""
import json
import re
from typing import Dict, Any
from langchain.tools import Tool
from database.connection.postgres_conn import get_readonly_db_context, get_async_readonly_db_context
from sqlalchemy import text
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


def execute_sql_query(query: str) -> str:
    """
    읽기 전용 DB 연결을 사용하는 SQL 실행 (동기)

    Args:
        query: 실행할 SQL 쿼리

    Returns:
        JSON 형식의 쿼리 실행 결과
    """
    LOGGER.debug(f"🔧 [SQL Tool] Executing query (sync): {query}")

    try:
        cleaned_query = _clean_query(query)
        _validate_query(cleaned_query)

        with get_readonly_db_context() as session:
            result = session.execute(text(cleaned_query))
            rows = result.fetchall()
            columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]

            response = {
                "query": cleaned_query,
                "success": True,
                "data": data,
                "columns": list(columns),
                "row_count": len(data)
            }

            LOGGER.info(f"✅ [SQL Tool] Query executed successfully: {len(data)} rows")
            return json.dumps(response, ensure_ascii=False, default=str)

    except Exception as e:
        error_response = {
            "query": query,
            "success": False,
            "error": str(e),
            "data": [],
            "columns": [],
            "row_count": 0
        }
        LOGGER.error(f"❌ [SQL Tool] Query failed: {e}")
        return json.dumps(error_response, ensure_ascii=False)


async def execute_sql_query_async(query: str) -> str:
    """
    읽기 전용 DB 연결을 사용하는 SQL 실행 (비동기)
    이벤트 루프를 블로킹하지 않는 asyncpg 기반 실행

    Args:
        query: 실행할 SQL 쿼리

    Returns:
        JSON 형식의 쿼리 실행 결과
    """
    LOGGER.debug(f"🔧 [SQL Tool] Executing query (async): {query}")

    try:
        cleaned_query = _clean_query(query)
        _validate_query(cleaned_query)

        async with get_async_readonly_db_context() as session:
            result = await session.execute(text(cleaned_query))
            rows = result.fetchall()
            columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]

            response = {
                "query": cleaned_query,
                "success": True,
                "data": data,
                "columns": list(columns),
                "row_count": len(data)
            }

            LOGGER.info(f"✅ [SQL Tool] Query executed successfully (async): {len(data)} rows")
            return json.dumps(response, ensure_ascii=False, default=str)

    except Exception as e:
        error_response = {
            "query": query,
            "success": False,
            "error": str(e),
            "data": [],
            "columns": [],
            "row_count": 0
        }
        LOGGER.error(f"❌ [SQL Tool] Query failed (async): {e}")
        return json.dumps(error_response, ensure_ascii=False)


FORBIDDEN_KEYWORDS = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|EXEC|EXECUTE|MERGE|CALL)\b',
    re.IGNORECASE,
)

DANGEROUS_PATTERNS = re.compile(
    r'(;\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE))|'  # 세미콜론 뒤 위험 구문
    r'(--\s*$)|'                                                 # SQL 주석으로 끝남
    r'(INTO\s+OUTFILE|LOAD_FILE|pg_read_file|pg_write_file)',    # 파일 접근
    re.IGNORECASE,
)


def _validate_query(query: str) -> None:
    """
    SQL 쿼리 안전성 검증

    Args:
        query: 검증할 SQL 쿼리

    Raises:
        ValueError: 위험한 쿼리가 감지된 경우
    """
    normalized = query.strip().rstrip(';').strip()

    # SELECT/WITH로 시작하는지 확인
    if not re.match(r'^(SELECT|WITH)\b', normalized, re.IGNORECASE):
        raise ValueError(f"Only SELECT queries are allowed. Got: {normalized[:50]}")

    # 금지 키워드 검사
    match = FORBIDDEN_KEYWORDS.search(normalized)
    if match:
        raise ValueError(f"Forbidden SQL keyword detected: {match.group()}")

    # 위험 패턴 검사
    match = DANGEROUS_PATTERNS.search(normalized)
    if match:
        raise ValueError(f"Dangerous SQL pattern detected: {match.group()}")


def _clean_query(query: str) -> str:
    """
    쿼리 전처리 - JSON 형식 및 마크다운 래퍼 제거

    Args:
        query: 원본 쿼리 문자열

    Returns:
        정리된 쿼리 문자열
    """
    # JSON 형식으로 잘못 전달된 경우 처리
    if query.startswith("{") and query.endswith("}"):
        try:
            query_data = json.loads(query)
            if "query" in query_data:
                query = query_data["query"]
        except:
            pass

    # 마크다운 래퍼 제거
    query = query.strip()
    if query.startswith("```") and query.endswith("```"):
        query = re.sub(r'^```\w*\n?', '', query)
        query = re.sub(r'\n?```$', '', query)
        query = query.strip()

    return query


def create_sql_tool() -> Tool:
    """
    SQL 실행 도구 생성 (sync + async 지원)

    Returns:
        LangChain Tool 객체
    """
    return Tool(
        name="execute_raw_sql_query",
        func=execute_sql_query,
        coroutine=execute_sql_query_async,
        description="""UFC 데이터베이스에서 읽기 전용 SQL 쿼리를 실행합니다.

                중요한 테이블명 규칙 (단수형 사용):
                - 'fighter' (파이터 정보)
                - 'match' (매치 정보)
                - 'fighter_match' (파이터-매치 관계)
                - 'event' (이벤트 정보)
                - 'ranking' (랭킹 정보)
                - 'weight_class' (체급 정보)

                읽기 전용 계정이므로 SELECT만 가능합니다.

                올바른 쿼리 예시:
                SELECT f.name, COUNT(*) as ko_wins FROM fighter f JOIN fighter_match fm ON f.id = fm.fighter_id JOIN match m ON fm.match_id = m.id WHERE m.method ILIKE '%ko%' GROUP BY f.name ORDER BY ko_wins DESC LIMIT 3;

                Args:
                    query (str): 실행할 SQL 쿼리 (읽기 전용)
                """
    )
