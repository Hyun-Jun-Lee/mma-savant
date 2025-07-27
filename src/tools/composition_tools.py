from typing import List, Dict, Optional, Any

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from composition import match_composer, fighter_composer, event_composer


# Event Composer Tools

@mcp.tool()
async def get_event_summary(event_id: int) -> Optional[Dict[str, Any]]:
    """
    특정 이벤트의 요약 정보를 조회합니다.
    
    Args:
        event_id (int): 조회할 이벤트의 ID
    
    Returns:
        Optional[Dict[str, Any]]: 이벤트 요약 정보
    """
    async with async_db_session() as session:
        summary = await event_composer.get_event_summary(session, int(event_id))
        return summary.model_dump() if summary else None

@mcp.tool()
async def get_recent_events_with_main_match(limit: int = 10) -> List[Dict]:
    """
    최근 이벤트들과 각각의 메인 이벤트 경기만을 조회합니다.
    
    Args:
        limit (int, optional): 조회할 최대 이벤트 수. 기본값 10개
    
    Returns:
        List[Dict]: 최근 이벤트들의 메인 매치 정보
    """
    async with async_db_session() as session:
        results = await event_composer.get_recent_events_with_main_match(session, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def get_upcoming_events_with_featured_matches(limit: int = 5) -> List[Dict]:
    """
    다가오는 이벤트들과 주목할만한 매치들을 조회합니다.
    
    Args:
        limit (int, optional): 조회할 최대 이벤트 수. 기본값 5개
    
    Returns:
        List[Dict]: 다가오는 이벤트들의 주요 매치 정보
    """
    async with async_db_session() as session:
        results = await event_composer.get_upcoming_events_with_featured_matches(session, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def compare_events_by_performance(event_id1: int, event_id2: int) -> Optional[Dict]:
    """
    두 이벤트의 성과를 비교 분석합니다.
    
    Args:
        event_id1 (int): 첫 번째 이벤트의 고유 ID 번호
        event_id2 (int): 두 번째 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 두 이벤트의 비교 분석 결과
    """
    async with async_db_session() as session:
        result = await event_composer.compare_events_by_performance(session, event_id1, event_id2)
        return result.model_dump() if result else None


@mcp.tool()
async def get_event_rankings_impact(event_id: int) -> Dict:
    """
    특정 이벤트가 파이터 랭킹에 미친 영향을 분석합니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Dict: 이벤트의 랭킹 영향 분석 결과
    """
    async with async_db_session() as session:
        result = await event_composer.get_event_rankings_impact(session, event_id)
        return result.model_dump()


# Match Composer Tools

@mcp.tool()
async def get_event_matches(event_id: int) -> Optional[Dict]:
    """
    특정 이벤트에 속한 모든 경기와 참가 파이터 정보를 조회합니다.
    
    Args:
        event_id (int): 조회할 이벤트 ID
    
    Returns:
        Optional[Dict]: 이벤트 정보와 전체 매치 목록
    """
    async with async_db_session() as session:
        result = await match_composer.get_event_matches(session, event_id)
        return result.model_dump() if result else None


@mcp.tool()
async def get_fight_of_the_night_candidates(event_id: int) -> Optional[Dict]:
    """
    특정 이벤트에서 Fight of the Night 후보가 될만한 경기들을 분석합니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: FOTN 후보 분석 결과
    """
    async with async_db_session() as session:
        result = await match_composer.get_fight_of_the_night_candidates(session, event_id)
        return result.model_dump() if result else None


@mcp.tool()
async def analyze_card_quality(event_id: int) -> Optional[Dict]:
    """
    이벤트 카드의 전반적인 품질을 종합적으로 분석합니다.
    
    이 도구는 UFC 이벤트의 카드 품질을 평가합니다. 랭킹 파이터 수, 챔피언 참여, 
    체급 다양성, 피니시율 등을 종합하여 Premium부터 Below Average까지 등급을 매깁니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 카드 품질 분석 결과
        {
            "event": Dict,  # 이벤트 기본 정보
            "card_analysis": Dict,  # 상세 카드 분석 (매치 수, 랭킹 파이터 등)
            "quality_assessment": Dict  # 품질 평가 (등급, 점수)
        }
    """
    async with async_db_session() as session:
        result = await match_composer.analyze_card_quality(session, event_id)
        return result.model_dump() if result else None


@mcp.tool()
async def get_most_exciting_matches_by_period(days: int = 30, limit: int = 10) -> List[Dict]:
    """
    지정된 기간 내에서 가장 흥미진진한 경기들을 분석합니다.
    
    이 도구는 최근 특정 기간 동안 가장 흥미진진했던 경기들을 찾아 순위를 매깁니다.
    피니시 방법, 메인 이벤트 여부, 랭킹 파이터 참여, 챔피언 참여 등을 고려합니다.
    
    Args:
        days (int, optional): 분석할 기간 (일). 기본값 30일
        limit (int, optional): 반환할 최대 경기 수. 기본값 10개
    
    Returns:
        List[Dict]: 흥미진진한 경기 목록 (흥미도 점수순)
        [
            {
                "event": Dict,  # 이벤트 정보
                "match": Dict,  # 매치 정보
                "fighters": List[Dict],  # 참가 파이터들
                "winner": Dict,  # 승자 정보
                "excitement_score": float,  # 흥미도 점수
                "highlights": Dict  # 하이라이트 (피니시 방법, 랭킹 파이터 수 등)
            }
        ]
    """
    async with async_db_session() as session:
        results = await match_composer.get_most_exciting_matches_by_period(session, days, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def analyze_comeback_performances(event_id: int) -> Dict:
    """
    특정 이벤트에서 컴백 승리나 역전승을 분석합니다.
    
    이 도구는 이벤트에서 일어난 극적인 컴백 승리들을 분석합니다. 
    늦은 라운드 피니시, 업셋 승리, 서브미션/KO 컴백 등을 식별합니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Dict: 컴백 성과 분석 결과
        {
            "event_id": int,
            "comeback_performances": List[Dict],  # 컴백 승리 목록
            "total_comebacks": int  # 총 컴백 수
        }
    """
    async with async_db_session() as session:
        result = await match_composer.analyze_comeback_performances(session, event_id)
        return result.model_dump()


@mcp.tool()
async def get_style_clash_analysis(match_id: int) -> Optional[Dict]:
    """
    특정 매치에서 파이터들의 스타일 대조와 매치업을 분석합니다.
    
    이 도구는 두 파이터의 스타일적 차이를 분석합니다. 스탠스, 신체 조건, 
    경험 등의 대조를 통해 매치업의 흥미로운 요소들을 찾아냅니다.
    
    Args:
        match_id (int): 분석할 매치의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 스타일 충돌 분석 결과
        {
            "match": Dict,  # 매치 기본 정보
            "fighters": List[Dict],  # 두 파이터 정보
            "style_contrasts": List[Dict],  # 스타일 대조 분석
            "match_result": Dict,  # 매치 결과
            "outcome_analysis": str,  # 결과 분석
            "contrast_summary": str  # 대조 요약
        }
    """
    async with async_db_session() as session:
        result = await match_composer.get_style_clash_analysis(session, match_id)
        return result.model_dump() if result else None


@mcp.tool()
async def get_performance_outliers_in_event(event_id: int) -> Dict:
    """
    특정 이벤트에서 예상을 뛰어넘는 성과를 보인 파이터들을 분석합니다.
    
    이 도구는 이벤트에서 통계적으로 예외적인 성과를 보인 파이터들을 찾습니다.
    스트라이킹, 그래플링, 컨트롤 타임 등 각 카테고리에서 임계값을 초과한 성과를 분석합니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Dict: 성과 예외자 분석 결과
        {
            "event_id": int,
            "outlier_performances": List[Dict],  # 예외적 성과 목록
            "analysis_summary": Dict  # 분석 요약 (총 예외자 수, 카테고리 등)
        }
    """
    async with async_db_session() as session:
        result = await match_composer.get_performance_outliers_in_event(session, event_id)
        return result.model_dump()


# Fighter Composer Tools

@mcp.tool()
async def get_fighter_all_matches(fighter_id: int) -> List[Dict]:
    """
    특정 파이터의 모든 경기 기록을 시간순으로 조회합니다.
    
    이 도구는 파이터의 전체 UFC 커리어 경기 기록을 제공합니다. 
    각 경기마다 이벤트, 상대방, 결과, 체급 정보를 포함합니다.
    
    Args:
        fighter_id (int): 조회할 파이터의 고유 ID 번호
    
    Returns:
        List[Dict]: 파이터의 모든 경기 기록
        [
            {
                "event": Dict,  # 이벤트 정보
                "opponent": Dict,  # 상대방 정보
                "match": Dict,  # 매치 정보
                "result": str,  # 경기 결과 (Win/Loss/Draw)
                "weight_class": str  # 체급명
            }
        ]
    """
    async with async_db_session() as session:
        results = await fighter_composer.get_fighter_all_matches(session, fighter_id)
        return [result.model_dump() for result in results]


@mcp.tool()
async def get_fighter_vs_record(fighter_id1: int, fighter_id2: int) -> List[Dict]:
    """
    두 파이터 간의 과거 대전 기록을 조회합니다.
    
    이 도구는 두 파이터가 과거에 맞붙었던 모든 경기의 상세 기록을 제공합니다.
    각 경기마다 매치 정보, 두 파이터의 결과, 통계 등을 포함합니다.
    
    Args:
        fighter_id1 (int): 첫 번째 파이터의 고유 ID 번호
        fighter_id2 (int): 두 번째 파이터의 고유 ID 번호
    
    Returns:
        List[Dict]: 두 파이터 간의 대전 기록
        [
            {
                "match_info": Dict,  # 매치 기본 정보 (이벤트명, 날짜 등)
                "fighter1": Dict,  # 첫 번째 파이터 정보와 결과
                "fighter2": Dict   # 두 번째 파이터 정보와 결과
            }
        ]
    
    """
    async with async_db_session() as session:
        results = await fighter_composer.get_fighter_vs_record(session, fighter_id1, fighter_id2)
        return [result.model_dump() for result in results]


@mcp.tool()
async def get_fighter_total_stat(fighter_id: int) -> Optional[Dict]:
    """
    특정 파이터의 모든 경기 통계를 종합하여 반환합니다.
    
    이 도구는 파이터의 UFC 커리어 전체 통계를 집계합니다. 
    기본 통계, 유효타 통계, 정확도 등을 포함한 종합 분석을 제공합니다.
    
    Args:
        fighter_id (int): 조회할 파이터의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 파이터 종합 통계
        {
            "fighter": Dict,  # 파이터 기본 정보
            "basic_stats": Dict,  # 기본 통계 (녹다운, 테이크다운 등)
            "sig_str_stats": Dict,  # 유효타 통계
            "accuracy": Dict  # 정확도 통계
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.get_fighter_total_stat(session, fighter_id)
        return result.model_dump() if result else None


@mcp.tool()
async def compare_fighters_stats(fighter_id1: int, fighter_id2: int) -> Optional[Dict]:
    """
    두 파이터의 모든 통계를 상세히 비교 분석합니다.
    
    이 도구는 두 파이터의 통계를 항목별로 비교하여 각각의 장단점을 분석합니다.
    기본 통계, 유효타, 정확도 등 모든 카테고리에서 누가 우위인지 보여줍니다.
    
    Args:
        fighter_id1 (int): 첫 번째 파이터의 고유 ID 번호
        fighter_id2 (int): 두 번째 파이터의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 두 파이터의 통계 비교 결과
        {
            "fighter1": Dict,  # 첫 번째 파이터 정보와 통계
            "fighter2": Dict,  # 두 번째 파이터 정보와 통계
            "comparison": Dict  # 항목별 비교 결과 (누가 우위인지)
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.compare_fighters_stats(session, fighter_id1, fighter_id2)
        return result.model_dump() if result else None


@mcp.tool()
async def get_fighter_with_top_stat(stat_name: str, limit: int = 10) -> List[Dict]:
    """
    특정 통계에서 가장 높은 값을 가진 파이터들을 순위별로 조회합니다.
    
    이 도구는 wins, losses, draws 등 기본 전적 통계에서 상위 파이터들을 찾습니다.
    각 통계 항목별로 리더보드를 제공합니다.
    
    Args:
        stat_name (str): 조회할 통계 항목명 ("wins", "losses", "draws")
        limit (int, optional): 반환할 최대 파이터 수. 기본값 10명
    
    Returns:
        List[Dict]: 해당 통계 상위 파이터 목록
        [
            {
                "rank": int,  # 순위
                "fighter_name": str,  # 파이터명
                "fighter_id": int,  # 파이터 ID
                "stat_name": str,  # 통계 항목명
                "total_stat": float  # 통계값
            }
        ]
    """
    async with async_db_session() as session:
        results = await fighter_composer.get_fighter_with_top_stat(session, stat_name, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def get_fighter_career_timeline(fighter_id: int) -> Dict:
    """
    파이터의 커리어 타임라인을 시간순으로 분석합니다.
    
    이 도구는 파이터의 경기를 시간순으로 정렬하고 커리어 하이라이트, 
    연승 기록, 메인 이벤트 참여 등을 종합 분석합니다.
    
    Args:
        fighter_id (int): 조회할 파이터의 고유 ID 번호
    
    Returns:
        Dict: 파이터 커리어 타임라인 분석
        {
            "fighter_id": int,
            "career_timeline": List[Dict],  # 시간순 경기 기록
            "summary": Dict  # 커리어 요약 (총 경기, 연승, 하이라이트 등)
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.get_fighter_career_timeline(session, fighter_id)
        return result.model_dump()


@mcp.tool()
async def analyze_fighter_vs_style(fighter_id: int, opponent_stance: str) -> Dict:
    """
    특정 파이터가 특정 스탠스의 상대들과의 대전 성과를 분석합니다.
    
    이 도구는 파이터가 Orthodox, Southpaw 등 특정 스탠스 상대와의 
    전적과 승률을 분석하여 스타일 매치업 선호도를 파악합니다.
    
    Args:
        fighter_id (int): 분석할 파이터의 고유 ID 번호
        opponent_stance (str): 상대방 스탠스 ("Orthodox", "Southpaw", "Switch" 등)
    
    Returns:
        Dict: 스탠스별 대전 분석 결과
        {
            "fighter": Dict,  # 파이터 정보
            "opponent_stance": str,  # 상대방 스탠스
            "analysis": Dict  # 분석 결과 (승률, 상세 기록 등)
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.analyze_fighter_vs_style(session, fighter_id, opponent_stance)
        return result.model_dump()


@mcp.tool()
async def get_divisional_elite_comparison(weight_class_id: int, top_n: int = 5) -> Dict:
    """
    특정 체급의 상위 파이터들을 종합적으로 비교 분석합니다.
    
    이 도구는 체급 내 엘리트 파이터들의 통계를 비교하고 각 분야별 
    리더를 찾아 체급의 선수층 깊이와 경쟁 구도를 분석합니다.
    
    Args:
        weight_class_id (int): 분석할 체급의 고유 ID 번호
        top_n (int, optional): 분석할 상위 파이터 수. 기본값 5명
    
    Returns:
        Dict: 체급 엘리트 비교 분석 결과
        {
            "weight_class": str,  # 체급명
            "weight_class_id": int,
            "elite_fighters": List[Dict],  # 엘리트 파이터들의 상세 정보
            "stat_leaders": Dict,  # 각 통계 분야별 리더
            "division_depth": int  # 체급 선수층 깊이
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.get_divisional_elite_comparison(session, weight_class_id, top_n)
        return result.model_dump()


@mcp.tool()
async def predict_fight_outcome(fighter_id1: int, fighter_id2: int) -> Dict:
    """
    두 파이터 간의 가상 매치업을 분석하고 결과를 예측합니다.
    
    이 도구는 두 파이터의 전적, 과거 대전 기록, 공통 상대, 통계 등을 
    종합하여 가상 경기의 승부를 예측하고 각종 분석 요소를 제공합니다.
    
    Args:
        fighter_id1 (int): 첫 번째 파이터의 고유 ID 번호
        fighter_id2 (int): 두 번째 파이터의 고유 ID 번호
    
    Returns:
        Dict: 경기 결과 예측 분석
        {
            "matchup": Dict,  # 매치업 정보 (두 파이터)
            "prediction": Dict,  # 예측 결과 (승률, 예측 승자, 신뢰도)
            "analysis_factors": Dict  # 분석 요소들 (헤드투헤드, 공통상대, 통계비교 등)
        }
    """
    async with async_db_session() as session:
        result = await fighter_composer.predict_fight_outcome(session, fighter_id1, fighter_id2)
        return result.model_dump()