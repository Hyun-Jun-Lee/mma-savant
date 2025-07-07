from typing import List, Dict, Optional, Any

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from match import services as match_services
from match import repositories as match_repo


@mcp.tool()
async def get_event_matches(event_name: str) -> Optional[Dict]:
    """
    특정 이벤트에 속한 모든 경기와 참가 파이터 정보를 조회합니다.
    
    이 도구는 사용자가 특정 UFC 이벤트의 전체 카드를 보고 싶어할 때 사용합니다.
    이벤트의 모든 매치, 승패 결과, 참여 파이터들을 카드 순서대로 제공합니다.
    
    Args:
        event_name (str): 조회할 이벤트 이름 (예: "UFC 300", "UFC Fight Night")
    
    Returns:
        Optional[Dict]: 이벤트 정보와 전체 매치 목록
        {
            "event_name": str,
            "event_date": str,
            "matches": [
                {
                    "match": Dict,
                    "winner_fighter": Dict,
                    "loser_fighter": Dict,
                    "draw_fighters": List[Dict] (무승부인 경우)
                }
            ]
        }
    
    사용 시점:
    - 사용자가 특정 이벤트의 전체 카드를 확인하고 싶을 때
    - 이벤트 결과와 매치업을 한눈에 보고 싶을 때
    - 메인 카드부터 프렐림까지 전체 결과를 알고 싶을 때
    
    사용자 질문 예시:
    - "UFC 300의 전체 카드와 결과를 보여줘"
    - "UFC Fight Night London의 모든 경기 결과가 궁금해"
    - "이번 UFC 이벤트 매치업이 어떻게 됐어?"
    - "UFC 285에서 누가 누구와 싸웠고 누가 이겼어?"
    - "어제 UFC 경기 결과를 모두 알려줘"
    """
    async with async_db_session() as session:
        result = await match_services.get_event_matches(session, event_name)
        return result


@mcp.tool()
async def get_match_with_winner_loser(match_id: int) -> Optional[Dict]:
    """
    특정 매치의 상세 정보와 승자/패자를 조회합니다.
    
    이 도구는 사용자가 특정 경기의 결과와 참여 파이터들에 대해 자세히 알고 싶을 때 사용합니다.
    승부 결과와 함께 파이터 정보를 명확하게 분류하여 제공합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID
    
    Returns:
        Optional[Dict]: 매치 정보와 승자/패자 분류
        {
            "match": Dict,
            "fighters": List[Dict],
            "winner": Dict,
            "loser": Dict,
            "draw_fighters": List[Dict] (무승부인 경우)
        }
    
    사용 시점:
    - 특정 매치의 결과를 명확히 확인하고 싶을 때
    - 승자와 패자 정보를 분리해서 보고 싶을 때
    - 매치 결과 분석이 필요할 때
    
    사용자 질문 예시:
    - "이 경기에서 누가 이겼어?"
    - "매치 ID 123번의 결과를 알려줘"
    - "이 경기의 승자와 패자가 누구야?"
    - "경기 결과와 참여 파이터 정보를 보여줘"
    """
    async with async_db_session() as session:
        result = await match_repo.get_match_with_winner_loser(session, match_id)
        return result


@mcp.tool()
async def get_match_statistics(match_id: int) -> Optional[Dict]:
    """
    특정 매치의 상세 통계 정보를 조회합니다.
    
    이 도구는 사용자가 경기의 통계적 분석에 관심이 있을 때 사용합니다.
    타격 수, 테이크다운, 컨트롤 타임 등 상세한 파이트 메트릭을 제공합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID
    
    Returns:
        Optional[Dict]: 매치의 상세 통계 정보
        {
            "match_id": int,
            "fighter_stats": List[Dict],
            "combined_stats": Dict
        }
    
    사용 시점:
    - 경기의 통계적 분석이 필요할 때
    - 파이터들의 성과를 수치로 비교하고 싶을 때
    - 경기의 활동량이나 지배력을 확인하고 싶을 때
    
    사용자 질문 예시:
    - "이 경기의 타격 통계가 어떻게 돼?"
    - "누가 더 많은 타격을 성공시켰어?"
    - "테이크다운과 컨트롤 타임은 어땠어?"
    - "경기 통계를 자세히 보여줘"
    - "이 매치의 파이트 메트릭이 궁금해"
    """
    async with async_db_session() as session:
        result = await match_repo.get_match_statistics(session, match_id)
        return result


@mcp.tool()
async def get_matches_with_high_activity(min_strikes: int = 200, limit: int = 10) -> List[Dict]:
    """
    높은 활동량을 보인 액션 가득한 매치들을 조회합니다.
    
    이 도구는 사용자가 재미있고 활발한 경기들을 찾고 싶을 때 사용합니다.
    총 타격 시도 수를 기준으로 가장 활동적인 경기들을 찾아 제공합니다.
    
    Args:
        min_strikes (int, optional): 최소 타격 시도 수. 기본값은 200
        limit (int, optional): 반환할 최대 경기 수. 기본값은 10
    
    Returns:
        List[Dict]: 높은 활동량 매치 목록
        [
            {
                "match": Dict,
                "total_strikes": int,
                "activity_rating": str
            }
        ]
    
    사용 시점:
    - 액션 가득한 재미있는 경기들을 찾고 싶을 때
    - 활발한 타격전이 벌어진 매치를 보고 싶을 때
    - 엔터테인먼트 가치가 높은 경기를 추천받고 싶을 때
    
    사용자 질문 예시:
    - "가장 액션 가득한 경기들을 보여줘"
    - "타격전이 치열했던 매치들이 궁금해"
    - "재미있는 UFC 경기들을 추천해줘"
    - "활동량이 높았던 경기들은 어떤 게 있어?"
    - "볼거리 많은 경기를 찾아줘"
    """
    async with async_db_session() as session:
        result = await match_repo.get_matches_with_high_activity(session, min_strikes, limit)
        return result


@mcp.tool()
async def get_matches_by_finish_method(method_pattern: str, limit: int = 20) -> List[Dict]:
    """
    특정 피니시 방법으로 끝난 매치들을 조회합니다.
    
    이 도구는 사용자가 특정한 경기 종료 방식에 관심이 있을 때 사용합니다.
    KO, TKO, 서브미션, 판정 등 원하는 피니시 방법의 경기들을 찾을 수 있습니다.
    
    Args:
        method_pattern (str): 검색할 피니시 방법 (예: "KO", "Submission", "Decision")
        limit (int, optional): 반환할 최대 경기 수. 기본값은 20
    
    Returns:
        List[Dict]: 해당 피니시 방법의 매치 목록
    
    사용 시점:
    - 특정 피니시 방법의 경기들을 모아보고 싶을 때
    - KO나 서브미션 같은 드라마틱한 경기들을 찾을 때
    - 피니시 방법별 경기 분석이 필요할 때
    
    사용자 질문 예시:
    - "KO로 끝난 경기들을 보여줘"
    - "서브미션으로 결판난 매치들이 궁금해"
    - "판정승 경기들은 어떤 게 있어?"
    - "TKO 피니시 경기들을 찾아줘"
    - "드라마틱하게 끝난 경기들을 알려줘"
    """
    async with async_db_session() as session:
        result = await match_repo.get_matches_by_finish_method(session, method_pattern, limit)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_matches_by_duration(min_rounds: Optional[int] = None, max_rounds: Optional[int] = None, limit: int = 20) -> List[Dict]:
    """
    특정 지속 시간(라운드 수) 조건에 맞는 매치들을 조회합니다.
    
    이 도구는 사용자가 경기 길이에 따른 매치들을 찾고 싶을 때 사용합니다.
    빠른 피니시부터 풀 디스턴스 경기까지 원하는 길이의 경기를 찾을 수 있습니다.
    
    Args:
        min_rounds (Optional[int]): 최소 라운드 수
        max_rounds (Optional[int]): 최대 라운드 수  
        limit (int, optional): 반환할 최대 경기 수. 기본값은 20
    
    Returns:
        List[Dict]: 조건에 맞는 매치 목록
    
    사용 시점:
    - 빠른 피니시 경기들을 찾고 싶을 때
    - 긴 접전 경기들을 보고 싶을 때
    - 특정 라운드에 끝난 경기들을 분석하고 싶을 때
    
    사용자 질문 예시:
    - "1라운드에 끝난 빠른 경기들을 보여줘"
    - "3라운드 이상 지속된 접전들이 궁금해"
    - "풀 디스턴스까지 간 경기들은?"
    - "짧게 끝난 경기들을 찾아줘"
    - "오래 지속된 격투를 보고 싶어"
    """
    async with async_db_session() as session:
        result = await match_repo.get_matches_by_duration(session, min_rounds, max_rounds, limit)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_matches_between_fighters(fighter_id_1: int, fighter_id_2: int) -> List[Dict]:
    """
    두 파이터 간의 모든 대전 기록을 조회합니다.
    
    이 도구는 사용자가 특정 두 파이터의 라이벌전이나 재경기에 관심이 있을 때 사용합니다.
    과거 대전 기록과 결과를 시간순으로 제공합니다.
    
    Args:
        fighter_id_1 (int): 첫 번째 파이터의 ID
        fighter_id_2 (int): 두 번째 파이터의 ID
    
    Returns:
        List[Dict]: 두 파이터 간의 모든 매치 기록
    
    사용 시점:
    - 두 파이터의 과거 대전 기록을 확인하고 싶을 때
    - 라이벌전의 역사를 알고 싶을 때
    - 재경기나 삼겨 전 참고 자료가 필요할 때
    
    사용자 질문 예시:
    - "이 두 파이터가 과거에 싸운 적 있어?"
    - "A와 B의 대전 기록을 보여줘"
    - "이들의 라이벌전 역사가 궁금해"
    - "과거에 누가 이겼었어?"
    - "재경기 전에 이전 경기 결과를 알고 싶어"
    """
    async with async_db_session() as session:
        result = await match_repo.get_matches_between_fighters(session, fighter_id_1, fighter_id_2)
        return [match.model_dump() for match in result]


@mcp.tool()
async def get_match_by_id(match_id: int) -> Optional[Dict]:
    """
    특정 매치 ID로 매치의 기본 정보를 조회합니다.
    
    이 도구는 정확한 매치 ID를 알고 있을 때 해당 경기의 기본적인 정보를 
    빠르게 조회하는 데 사용합니다.
    
    Args:
        match_id (int): 조회할 매치의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 매치 기본 정보 또는 None (매치가 없을 경우)
        {
            "id": int,
            "event_id": int,
            "weight_class_id": int,
            "method": str,
            "result_round": int,
            "time": str,
            "order": int,
            "is_main_event": bool
        }
    
    사용 시점:
    - 정확한 매치 ID를 알고 있을 때
    - 매치의 기본 정보만 빠르게 확인하고 싶을 때
    - 다른 도구에서 얻은 매치 ID의 상세 정보가 필요할 때
    
    사용자 질문 예시:
    - "매치 ID 456의 정보를 알려줘"
    - "이 경기는 몇 라운드에 끝났어?"
    - "이 매치가 메인 이벤트였어?"
    - "경기 방법이 뭐였어?"
    """
    async with async_db_session() as session:
        result = await match_repo.get_match_by_id(session, match_id)
        return result.model_dump() if result else None


@mcp.tool()
async def get_matches_by_event_id(event_id: int) -> List[Dict]:
    """
    특정 이벤트 ID에 속한 모든 매치들을 조회합니다.
    
    이 도구는 이벤트 ID를 알고 있을 때 해당 이벤트의 전체 매치 목록을 
    카드 순서대로 조회하는 데 사용합니다.
    
    Args:
        event_id (int): 조회할 이벤트의 고유 ID
    
    Returns:
        List[Dict]: 이벤트의 모든 매치 목록 (카드 순서대로)
    
    사용 시점:
    - 정확한 이벤트 ID를 알고 있을 때
    - 이벤트의 전체 카드 구성을 확인하고 싶을 때
    - 매치 순서대로 경기 목록을 보고 싶을 때
    
    사용자 질문 예시:
    - "이벤트 ID 123의 모든 경기를 보여줘"
    - "이 이벤트에 몇 개의 경기가 있어?"
    - "카드 순서대로 매치를 알려줘"
    - "이 이벤트의 전체 구성이 궁금해"
    """
    async with async_db_session() as session:
        result = await match_repo.get_matches_by_event_id(session, event_id)
        return [match.model_dump() for match in result]