from typing import List, Dict, Optional, Any

from tools.load_tools import mcp
from database import *
from database.connection.postgres_conn import get_async_db_context
from fighter import services as fighter_services

@mcp.tool()
async def get_fighter_info_by_id(fighter_id: int) -> Optional[Dict]:
    """
    특정 파이터 ID로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    Args:
        fighter_id (int): 조회할 파이터의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리
    """

    async with get_async_db_context() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_id(session, int(fighter_id))
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_name(fighter_name: str) -> Optional[Dict]:
    """
    파이터의 실명으로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    Args:
        fighter_name (str): 조회할 파이터의 실명
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리
    """

    async with get_async_db_context() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_name(session, fighter_name)
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_nickname(fighter_nickname: str) -> Optional[Dict]:
    """
    파이터의 링네임(닉네임)으로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    Args:
        fighter_nickname (str): 조회할 파이터의 링네임/별명
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리
    """

    async with get_async_db_context() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_nickname(session, fighter_nickname)
    return fighter_with_ranking.model_dump()


@mcp.tool()
async def search_fighters(search_term: str, limit: int = 10) -> List[Dict]:
    """
    이름이나 닉네임으로 파이터를 검색하고 랭킹 정보와 함께 반환합니다.
    
    Args:
        search_term (str): 검색할 키워드
        limit (int, optional): 반환할 최대 결과 수. 기본값은 10
    
    Returns:
        List[Dict]: 검색된 파이터 목록
    """
    async with get_async_db_context() as session:
        fighters = await fighter_services.search_fighters(session, search_term, limit)
        return [fighter.model_dump() for fighter in fighters]


@mcp.tool()
async def get_all_champions() -> List[Dict]:
    """
    현재 모든 체급의 챔피언들을 랭킹 정보와 함께 조회합니다.
    
    Returns:
        List[Dict]: 모든 현재 챔피언들의 정보와 랭킹 목록
    """
    async with get_async_db_context() as session:
        champions = await fighter_services.get_all_champions(session)
        return [champion.model_dump() for champion in champions]


@mcp.tool()
async def get_fighters_by_stance_analysis(stance: str) -> Dict[str, Any]:
    """
    특정 스탠스의 파이터들을 분석 정보와 함께 제공합니다.
    
    Args:
        stance (str): 분석할 스탠스
    
    Returns:
        Dict[str, Any]: 해당 스탠스 파이터들의 정보와 분석 데이터
    """
    async with get_async_db_context() as session:
        analysis = await fighter_services.get_fighters_by_stance_analysis(session, stance)
        return analysis.model_dump()


@mcp.tool()
async def get_undefeated_fighters_analysis(min_wins: int = 5) -> Dict[str, Any]:
    """
    무패 파이터들의 분석 정보를 제공합니다.
    
    Args:
        min_wins (int, optional): 최소 승수 조건. 기본값은 5
    
    Returns:
        Dict[str, Any]: 무패 파이터들의 정보와 분석 데이터
    """
    async with get_async_db_context() as session:
        analysis = await fighter_services.get_undefeated_fighters_analysis(session, min_wins)
        return analysis.model_dump()


@mcp.tool()
async def get_fighters_by_physical_attributes(
    min_height: Optional[float] = None,
    max_height: Optional[float] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_reach: Optional[float] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    신체 조건으로 파이터들을 조회하고 분석 정보를 제공합니다.
    
    Args:
        min_height (Optional[float]): 최소 키 (cm)
        max_height (Optional[float]): 최대 키 (cm)
        min_weight (Optional[float]): 최소 몸무게 (kg)
        max_weight (Optional[float]): 최대 몸무게 (kg)
        min_reach (Optional[float]): 최소 리치 (cm)
        limit (int, optional): 반환할 최대 결과 수. 기본값은 20
    
    Returns:
        Dict[str, Any]: 조건에 맞는 파이터들과 신체 통계 분석
    """
    async with get_async_db_context() as session:
        analysis = await fighter_services.get_fighters_by_physical_attributes(
            session, min_height, max_height, min_weight, max_weight, min_reach, limit
        )
        return analysis.model_dump()


@mcp.tool()
async def get_fighters_performance_analysis() -> Dict[str, Any]:
    """
    전체 파이터들의 성과 분석을 제공합니다.
    
    Returns:
        Dict[str, Any]: 전체 파이터들의 성과 분석 데이터
    """
    async with get_async_db_context() as session:
        analysis = await fighter_services.get_fighters_performance_analysis(session)
        return analysis.model_dump()


@mcp.tool()
async def get_weight_class_depth_analysis(weight_class_name: str) -> Dict[str, Any]:
    """
    특정 체급의 깊이 분석을 제공합니다.
    
    Args:
        weight_class_name (str): 분석할 체급명
    
    Returns:
        Dict[str, Any]: 체급 깊이 분석 정보
    """
    async with get_async_db_context() as session:
        analysis = await fighter_services.get_weight_class_depth_analysis(session, weight_class_name)
        return analysis.model_dump()