from typing import List, Dict, Optional

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from fighter import services as fighter_services

@mcp.tool()
async def get_fighter_info_by_id(fighter_id: int) -> Optional[Dict]:
    """
    특정 파이터 ID로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    이 도구는 정확한 파이터 ID를 알고 있을 때 사용합니다. 파이터의 기본 정보, 전적, 체급별 랭킹 등 
    모든 상세 정보를 포함하여 반환합니다.
    
    Args:
        fighter_id (int): 조회할 파이터의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리 또는 None (파이터가 없을 경우)
        {
            "id": int,
            "name": str,
            "nickname": str,
            "wins": int,
            "losses": int,
            "draws": int,
            "belt": bool,
            "stance": str,
            "height": float,
            "weight": float,
            "rankings": List[Dict]
        }
    
    사용 시점:
    - 다른 도구에서 파이터 ID를 얻은 후 상세 정보가 필요할 때
    - 파이터 프로필 페이지나 상세 분석이 필요할 때
    - 특정 파이터의 랭킹 정보를 포함한 전체 정보가 필요할 때
    
    사용자 질문 예시:
    - "파이터 ID 123번의 상세 정보를 알려줘"
    - "이 파이터의 랭킹 정보도 포함해서 보여줘"
    - "파이터 프로필을 자세히 보고 싶어"
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_id(session, int(fighter_id))
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_name(fighter_name: str) -> Optional[Dict]:
    """
    파이터의 실명으로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    이 도구는 사용자가 파이터의 정확한 이름을 제공했을 때 사용합니다. 이름 기반 검색으로 
    파이터의 모든 정보를 조회하며, 대소문자 구분 없이 정확한 매칭을 지원합니다.
    
    Args:
        fighter_name (str): 조회할 파이터의 실명 (예: "Conor McGregor", "Jon Jones")
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리 또는 None (파이터가 없을 경우)
        {
            "id": int,
            "name": str,
            "nickname": str,
            "wins": int,
            "losses": int,
            "draws": int,
            "belt": bool,
            "stance": str,
            "height": float,
            "weight": float,
            "rankings": List[Dict]
        }
    
    사용 시점:
    - 사용자가 파이터의 정확한 실명을 언급했을 때
    - "코너 맥그리거", "존 존스" 등 풀네임으로 검색할 때
    - 닉네임이 아닌 본명으로 파이터를 찾을 때
    
    사용자 질문 예시:
    - "Conor McGregor의 정보를 보여줘"
    - "존 존스의 전적이 어떻게 돼?"
    - "Anderson Silva의 랭킹을 알려줘"
    - "이스라엘 아데산야에 대해 알려줘"
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_name(session, fighter_name)
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_nickname(fighter_nickname: str) -> Optional[Dict]:
    """
    파이터의 링네임(닉네임)으로 파이터의 상세 정보와 랭킹을 조회합니다.
    
    이 도구는 사용자가 파이터의 링네임이나 별명을 언급했을 때 사용합니다. MMA에서 파이터들은 
    종종 닉네임으로 더 잘 알려져 있기 때문에 이 기능이 유용합니다.
    
    Args:
        fighter_nickname (str): 조회할 파이터의 링네임/별명 (예: "The Notorious", "Bones", "The Spider")
    
    Returns:
        Optional[Dict]: 파이터 정보와 랭킹을 포함한 딕셔너리 또는 None (파이터가 없을 경우)
        {
            "id": int,
            "name": str,
            "nickname": str,
            "wins": int,
            "losses": int,
            "draws": int,
            "belt": bool,
            "stance": str,
            "height": float,
            "weight": float,
            "rankings": List[Dict]
        }
    
    사용 시점:
    - 사용자가 파이터의 링네임이나 별명을 언급했을 때
    - "The Notorious", "Bones" 등 닉네임으로 파이터를 찾을 때
    - 본명보다 닉네임이 더 유명한 파이터를 검색할 때
    
    사용자 질문 예시:
    - "The Notorious의 정보를 알려줘"
    - "Bones Jones의 전적은?"
    - "The Spider의 랭킹이 궁금해"
    - "Iron Mike 타이슨은 UFC에 있어?"
    - "The Mountain에 대해 알려줘"
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_nickname(session, fighter_nickname)
    return fighter_with_ranking.model_dump()


@mcp.tool()
async def search_fighters(search_term: str, limit: int = 10) -> List[Dict]:
    """
    이름이나 닉네임으로 파이터를 검색하고 랭킹 정보와 함께 반환합니다.
    
    이 도구는 사용자가 파이터 이름의 일부만 기억하거나, 여러 파이터를 찾고 싶을 때 사용합니다.
    부분 매칭을 지원하므로 정확하지 않은 이름도 찾을 수 있으며, 관련성 높은 순서로 결과를 제공합니다.
    
    Args:
        search_term (str): 검색할 키워드 (파이터 이름이나 닉네임의 일부)
        limit (int, optional): 반환할 최대 결과 수. 기본값은 10
    
    Returns:
        List[Dict]: 검색된 파이터 목록, 각 항목은 파이터 정보와 랭킹을 포함
    
    사용 시점:
    - 사용자가 파이터 이름을 정확히 기억하지 못할 때
    - 이름의 일부만으로 파이터를 찾고 싶을 때
    - 여러 파이터 중에서 선택하고 싶을 때
    - 비슷한 이름의 파이터들을 비교하고 싶을 때
    
    사용자 질문 예시:
    - "존으로 시작하는 파이터들을 찾아줘"
    - "맥그리거가 포함된 파이터를 검색해줘"
    - "Silva라는 성씨를 가진 파이터들이 궁금해"
    - "코너와 비슷한 이름의 파이터들을 보여줘"
    - "안데르손이 들어간 파이터를 찾아봐"
    """
    async with async_db_session() as session:
        fighters = await fighter_services.search_fighters(session, search_term, limit)
        return [fighter.model_dump() for fighter in fighters]


@mcp.tool()
async def get_all_champions() -> List[Dict]:
    """
    현재 모든 체급의 챔피언들을 랭킹 정보와 함께 조회합니다.
    
    이 도구는 사용자가 현재 UFC의 모든 챔피언에 대해 궁금해할 때 사용합니다.
    각 체급별 현재 벨트 보유자들을 한 번에 확인할 수 있습니다.
    
    Returns:
        List[Dict]: 모든 현재 챔피언들의 정보와 랭킹 목록
    
    사용 시점:
    - 사용자가 현재 UFC 챔피언들에 대해 궁금할 때
    - 모든 체급의 현재 상황을 파악하고 싶을 때
    - 챔피언들의 전적을 비교하고 싶을 때
    
    사용자 질문 예시:
    - "현재 UFC 챔피언들이 누구야?"
    - "모든 체급 챔피언을 보여줘"
    - "지금 벨트를 가지고 있는 파이터들은?"
    - "UFC 현재 왕자들을 알려줘"
    - "모든 디비전의 챔피언 목록을 보고 싶어"
    """
    async with async_db_session() as session:
        champions = await fighter_services.get_all_champions(session)
        return [champion.model_dump() for champion in champions]


@mcp.tool()
async def get_fighters_by_stance_analysis(stance: str) -> Dict[str, Any]:
    """
    특정 스탠스의 파이터들을 분석 정보와 함께 제공합니다.
    
    이 도구는 사용자가 특정 파이팅 스탠스에 관심이 있거나, 스탠스별 파이터들의 
    성과와 특성을 알고 싶을 때 사용합니다. 통계적 분석도 함께 제공됩니다.
    
    Args:
        stance (str): 분석할 스탠스 (예: "Orthodox", "Southpaw", "Switch")
    
    Returns:
        Dict[str, Any]: 해당 스탠스 파이터들의 정보와 분석 데이터
        {
            "stance": str,
            "total_fighters": int,
            "fighters": List[Dict],
            "analysis": {
                "average_wins": float,
                "total_wins": int,
                "total_losses": int,
                "total_fights": int,
                "champions_count": int,
                "win_percentage": float
            }
        }
    
    사용 시점:
    - 사용자가 특정 스탠스의 파이터들에 관심이 있을 때
    - 스탠스별 성과 차이를 궁금해할 때
    - 왼손잡이 vs 오른손잡이 파이터들을 비교하고 싶을 때
    
    사용자 질문 예시:
    - "사우스포 파이터들이 얼마나 강해?"
    - "오른손잡이 파이터들의 성과는 어때?"
    - "스위치 스탠스 파이터들을 보여줘"
    - "왼손잡이 파이터들의 승률이 궁금해"
    - "어떤 스탠스가 더 유리한지 알려줘"
    """
    async with async_db_session() as session:
        analysis = await fighter_services.get_fighters_by_stance_analysis(session, stance)
        return analysis


@mcp.tool()
async def get_undefeated_fighters_analysis(min_wins: int = 5) -> Dict[str, Any]:
    """
    무패 파이터들의 분석 정보를 제공합니다.
    
    이 도구는 사용자가 무패 행진을 이어가고 있는 파이터들에 관심이 있을 때 사용합니다.
    신진 유망주나 떠오르는 스타들을 찾는 데 유용합니다.
    
    Args:
        min_wins (int, optional): 최소 승수 조건. 기본값은 5
    
    Returns:
        Dict[str, Any]: 무패 파이터들의 정보와 분석 데이터
        {
            "total_undefeated": int,
            "min_wins_threshold": int,
            "fighters": List[Dict],
            "analysis": {
                "average_wins": float,
                "total_wins": int,
                "champions_count": int,
                "most_wins": int
            }
        }
    
    사용 시점:
    - 사용자가 무패 파이터들에 관심이 있을 때
    - 떠오르는 신예들을 찾고 싶을 때
    - 완벽한 전적을 가진 파이터들을 궁금해할 때
    
    사용자 질문 예시:
    - "무패 파이터들이 누구야?"
    - "한 번도 져본 적 없는 파이터들을 보여줘"
    - "완벽한 전적을 가진 선수들은?"
    - "떠오르는 무패 신예들이 궁금해"
    - "챔피언 중에 무패인 사람이 있어?"
    """
    async with async_db_session() as session:
        analysis = await fighter_services.get_undefeated_fighters_analysis(session, min_wins)
        return analysis


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
    
    이 도구는 사용자가 특정 신체 조건을 가진 파이터들에 관심이 있을 때 사용합니다.
    키, 몸무게, 리치 등의 물리적 특성으로 파이터들을 필터링할 수 있습니다.
    
    Args:
        min_height (Optional[float]): 최소 키 (cm)
        max_height (Optional[float]): 최대 키 (cm) 
        min_weight (Optional[float]): 최소 몸무게 (kg)
        max_weight (Optional[float]): 최대 몸무게 (kg)
        min_reach (Optional[float]): 최소 리치 (cm)
        limit (int, optional): 반환할 최대 결과 수. 기본값은 20
    
    Returns:
        Dict[str, Any]: 조건에 맞는 파이터들과 신체 통계 분석
    
    사용 시점:
    - 사용자가 특정 신체 조건의 파이터들에 관심이 있을 때
    - 키가 큰/작은 파이터들을 비교하고 싶을 때
    - 리치가 긴 파이터들의 우위를 궁금해할 때
    
    사용자 질문 예시:
    - "키 180cm 이상인 파이터들을 보여줘"
    - "리치가 긴 파이터들이 누구야?"
    - "가장 큰 파이터들은 누구인가?"
    - "작은 체구지만 강한 파이터들이 있어?"
    - "신체 조건이 비슷한 파이터들을 찾아줘"
    """
    async with async_db_session() as session:
        analysis = await fighter_services.get_fighters_by_physical_attributes(
            session, min_height, max_height, min_weight, max_weight, min_reach, limit
        )
        return analysis


@mcp.tool()
async def get_fighters_performance_analysis() -> Dict[str, Any]:
    """
    전체 파이터들의 성과 분석을 제공합니다.
    
    이 도구는 사용자가 UFC 전체 파이터들의 통계적 분석이나 성과 트렌드에 
    관심이 있을 때 사용합니다. 전반적인 UFC 생태계를 이해하는 데 도움이 됩니다.
    
    Returns:
        Dict[str, Any]: 전체 파이터들의 성과 분석 데이터
        {
            "overall_statistics": Dict,
            "win_percentage_leaders": List[Dict],
            "performance_insights": Dict
        }
    
    사용 시점:
    - 사용자가 UFC 전체적인 통계에 관심이 있을 때
    - 파이터들의 평균적인 성과를 궁금해할 때
    - UFC의 전반적인 트렌드를 알고 싶을 때
    
    사용자 질문 예시:
    - "UFC 파이터들의 평균 전적은 어떻게 돼?"
    - "가장 승률이 높은 파이터들은 누구야?"
    - "UFC 전체적인 통계를 보여줘"
    - "파이터들의 성과 분석이 궁금해"
    - "UFC에서 챔피언이 될 확률은 얼마나 돼?"
    """
    async with async_db_session() as session:
        analysis = await fighter_services.get_fighters_performance_analysis(session)
        return analysis


@mcp.tool()
async def get_weight_class_depth_analysis(weight_class_name: str) -> Dict[str, Any]:
    """
    특정 체급의 깊이 분석을 제공합니다.
    
    이 도구는 사용자가 특정 체급의 경쟁 수준이나 파이터 풀의 깊이에 
    관심이 있을 때 사용합니다. 체급별 랭킹 경쟁도와 챔피언 분석을 제공합니다.
    
    Args:
        weight_class_name (str): 분석할 체급명 (예: "Lightweight", "Heavyweight")
    
    Returns:
        Dict[str, Any]: 체급 깊이 분석 정보
        {
            "weight_class": str,
            "total_ranked_fighters": int,
            "total_fighters_in_division": int,
            "champion": Dict | None,
            "ranked_fighters": List[Dict],
            "depth_analysis": Dict
        }
    
    사용 시점:
    - 사용자가 특정 체급의 경쟁 수준을 궁금해할 때
    - 체급별 랭킹 시스템을 이해하고 싶을 때
    - 어떤 체급이 가장 경쟁이 치열한지 알고 싶을 때
    
    사용자 질문 예시:
    - "라이트웨이트 체급이 얼마나 경쟁이 치열해?"
    - "헤비웨이트 체급의 파이터 풀은 어때?"
    - "어떤 체급이 가장 깊이가 있어?"
    - "미들웨이트 랭킹을 분석해줘"
    - "페더웨이트 체급의 전체적인 상황은?"
    """
    async with async_db_session() as session:
        analysis = await fighter_services.get_weight_class_depth_analysis(session, weight_class_name)
        return analysis