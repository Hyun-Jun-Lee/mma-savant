from typing import List, Dict, Optional, Any

from tools.load_tools import mcp
from database import *
from database.connection.postgres_conn import get_async_db_context
from match import repositories as match_repo

@mcp.tool()
async def get_match_with_winner_loser(match_id: int) -> Optional[Dict]:
    """
    특정 매치의 상세 정보와 승자/패자를 조회합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID
    
    Returns:
        Optional[Dict]: 매치 정보와 승자/패자 분류
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_match_with_winner_loser(session, match_id)
        return result


@mcp.tool()
async def get_match_statistics(match_id: int) -> Optional[Dict]:
    """
    특정 매치의 상세 통계 정보를 조회합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID
    
    Returns:
        Optional[Dict]: 매치의 상세 통계 정보
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_match_statistics(session, match_id)
        return result


@mcp.tool()
async def get_matches_with_high_activity(min_strikes: int = 200, limit: int = 10) -> List[Dict]:
    """
    높은 활동량을 보인 액션 가득한 매치들을 조회합니다.
    
    Args:
        min_strikes (int, optional): 최소 타격 시도 수. 기본값은 200
        limit (int, optional): 반환할 최대 경기 수. 기본값은 10
    
    Returns:
        List[Dict]: 높은 활동량 매치 목록
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_matches_with_high_activity(session, min_strikes, limit)
        return result


@mcp.tool()
async def get_matches_by_finish_method(method_pattern: str, limit: int = 20) -> List[Dict]:
    """
    특정 피니시 방법으로 끝난 매치들을 조회합니다.
    
    Args:
        method_pattern (str): 검색할 피니시 방법 (예: "KO", "Submission", "Decision")
        limit (int, optional): 반환할 최대 경기 수. 기본값은 20
    
    Returns:
        List[Dict]: 해당 피니시 방법의 매치 목록
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_matches_by_finish_method(session, method_pattern, limit)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_matches_by_duration(min_rounds: Optional[int] = None, max_rounds: Optional[int] = None, limit: int = 20) -> List[Dict]:
    """
    특정 지속 시간(라운드 수) 조건에 맞는 매치들을 조회합니다.
    
    Args:
        min_rounds (Optional[int]): 최소 라운드 수
        max_rounds (Optional[int]): 최대 라운드 수  
        limit (int, optional): 반환할 최대 경기 수. 기본값은 20
    
    Returns:
        List[Dict]: 조건에 맞는 매치 목록
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_matches_by_duration(session, min_rounds, max_rounds, limit)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_matches_between_fighters(fighter_id_1: int, fighter_id_2: int) -> List[Dict]:
    """
    두 파이터 간의 모든 대전 기록을 조회합니다.
    
    Args:
        fighter_id_1 (int): 첫 번째 파이터의 ID
        fighter_id_2 (int): 두 번째 파이터의 ID
    
    Returns:
        List[Dict]: 두 파이터 간의 모든 매치 기록
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_matches_between_fighters(session, fighter_id_1, fighter_id_2)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_match_by_id(match_id: int) -> Optional[Dict]:
    """
    특정 매치 ID로 매치의 기본 정보를 조회합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 매치 기본 정보 또는 None
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_match_by_id(session, match_id)
        return result.model_dump() if result else None


@mcp.tool()
async def get_matches_by_event_id(event_id: int) -> List[Dict]:
    """
    특정 이벤트 ID에 속한 모든 매치들을 조회합니다.
    
    Args:
        event_id (int): 조회할 이벤트의 고유 ID
    
    Returns:
        List[Dict]: 이벤트의 모든 매치 목록
    """
    async with get_async_db_context() as session:
        result = await match_repo.get_matches_by_event_id(session, event_id)
        return [match.model_dump() for match in result]