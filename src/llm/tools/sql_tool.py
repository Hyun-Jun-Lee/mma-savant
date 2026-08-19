"""SQL 실행 도구 모듈"""
import json
import re
from langchain_core.tools import tool
from database.connection.postgres_conn import get_async_readonly_db_context
from sqlalchemy import text
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

MAX_RESULT_ROWS = 100


@tool
async def execute_raw_sql_query(query: str) -> str:
    """UFC 데이터베이스에서 읽기 전용 SQL 쿼리를 실행합니다.

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
        query: 실행할 SQL 쿼리 (읽기 전용)
    """
    LOGGER.debug(f"🔧 [SQL Tool] Executing query: {query}")

    try:
        cleaned_query = _clean_query(query)
        _validate_query(cleaned_query)

        async with get_async_readonly_db_context() as session:
            result = await session.execute(text(cleaned_query))
            rows = result.fetchall()
            columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]

            if len(data) > MAX_RESULT_ROWS:
                LOGGER.warning(f"⚠️ [SQL Tool] Result truncated: {len(data)} → {MAX_RESULT_ROWS} rows")
                data = data[:MAX_RESULT_ROWS]

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

    query = _strip_single_outer_parentheses(query)

    return query


def _strip_single_outer_parentheses(query: str) -> str:
    """Remove one pair of parentheses only when it wraps the entire SELECT/WITH query."""
    stripped = query.strip()
    if not (stripped.startswith("(") and stripped.endswith(")")):
        return stripped

    depth = 0
    in_single_quote = False
    in_double_quote = False

    idx = 0
    while idx < len(stripped):
        char = stripped[idx]
        if char == "'" and not in_double_quote:
            if in_single_quote and idx + 1 < len(stripped) and stripped[idx + 1] == "'":
                idx += 2
                continue
            in_single_quote = not in_single_quote
            idx += 1
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            idx += 1
            continue

        if in_single_quote or in_double_quote:
            idx += 1
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and idx != len(stripped) - 1:
                return stripped
            if depth < 0:
                return stripped
        idx += 1

    if depth != 0:
        return stripped

    candidate = stripped[1:-1].strip()
    if re.match(r'^(SELECT|WITH)\b', candidate, re.IGNORECASE):
        return candidate
    return stripped
