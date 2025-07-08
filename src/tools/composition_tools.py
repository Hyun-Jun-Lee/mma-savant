from typing import List, Dict, Optional, Any

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from composition import match_composer, fighter_composer, event_composer


# Event Composer Tools

@mcp.tool()
async def get_event_with_all_matches(event_name: str) -> Optional[Dict]:
    """
    특정 이벤트에 속한 모든 경기와 승패결과를 조회합니다.
    
    이 도구는 특정 UFC 이벤트의 전체 카드와 모든 경기 결과를 상세히 제공합니다.
    각 매치마다 참여 파이터, 승패 결과, 경기 방식 등을 포함하여 이벤트 전체 요약을 제공합니다.
    
    Args:
        event_name (str): 조회할 이벤트 이름 (예: "UFC 300", "UFC Fight Night")
    
    Returns:
        Optional[Dict]: 이벤트와 모든 매치 정보
        {
            "event": Dict,  # 이벤트 기본 정보
            "matches": List[Dict],  # 모든 매치 상세 정보 (파이터, 결과 포함)
            "summary": Dict  # 이벤트 통계 요약 (총 매치 수, 결승 방법 등)
        }
    
    사용 시점:
    - 사용자가 특정 이벤트의 완전한 카드와 결과를 보고 싶을 때
    - 이벤트 전체 흐름과 매치 결과를 분석하고 싶을 때
    - 특정 UFC 이벤트의 종합 리포트가 필요할 때
    
    사용자 질문 예시:
    - "UFC 300의 전체 카드와 모든 결과를 보여줘"
    - "UFC Fight Night London에서 어떤 경기들이 있었고 누가 이겼어?"
    - "이번 이벤트 전체 매치업과 결과를 정리해줘"
    - "UFC 285 전체 카드 분석을 해줘"
    """
    async with async_db_session() as session:
        result = await event_composer.get_event_with_all_matches(session, event_name)
        return result.model_dump() if result else None


@mcp.tool()
async def get_recent_events_with_main_match(limit: int = 10) -> List[Dict]:
    """
    최근 이벤트들과 각각의 메인 이벤트 경기만을 조회합니다.
    
    이 도구는 최근에 열린 UFC 이벤트들의 메인 이벤트 매치만을 간략하게 제공합니다.
    각 이벤트별로 가장 중요한 메인 카드 경기와 그 결과를 보여줍니다.
    
    Args:
        limit (int, optional): 조회할 최대 이벤트 수. 기본값 10개
    
    Returns:
        List[Dict]: 최근 이벤트들의 메인 매치 정보
        [
            {
                "event": Dict,  # 이벤트 기본 정보
                "main_match": Dict  # 메인 이벤트 매치 상세 정보
            }
        ]
    
    사용 시점:
    - 사용자가 최근 UFC 이벤트들의 주요 결과를 빠르게 확인하고 싶을 때
    - 메인 이벤트 매치들만 간략히 보고 싶을 때
    - 최근 UFC 동향을 파악하고 싶을 때
    
    사용자 질문 예시:
    - "최근 UFC 이벤트들의 메인 매치 결과를 보여줘"
    - "이번 달 UFC 메인 이벤트들이 뭐였어?"
    - "최근 주요 UFC 경기 결과들을 알려줘"
    - "지난 몇 개 이벤트의 헤드라이너들을 보여줘"
    """
    async with async_db_session() as session:
        results = await event_composer.get_recent_events_with_main_match(session, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def get_upcoming_events_with_featured_matches(limit: int = 5) -> List[Dict]:
    """
    다가오는 이벤트들과 주목할만한 매치들을 조회합니다.
    
    이 도구는 앞으로 예정된 UFC 이벤트들과 각 이벤트의 메인 이벤트 및 
    주요 매치들을 미리 보여줍니다. 팬들이 기대할 만한 매치업들을 제공합니다.
    
    Args:
        limit (int, optional): 조회할 최대 이벤트 수. 기본값 5개
    
    Returns:
        List[Dict]: 다가오는 이벤트들의 주요 매치 정보
        [
            {
                "event": Dict,  # 이벤트 기본 정보
                "main_event": Dict,  # 메인 이벤트 매치
                "featured_matches": List[Dict]  # 주요 매치들 (최대 3개)
            }
        ]
    
    사용 시점:
    - 사용자가 앞으로 있을 UFC 이벤트들을 미리 확인하고 싶을 때
    - 다가오는 주요 매치업들을 알고 싶을 때
    - UFC 스케줄과 기대되는 경기들을 보고 싶을 때
    
    사용자 질문 예시:
    - "다음 UFC 이벤트들에서 어떤 경기들이 있어?"
    - "앞으로 있을 주요 UFC 매치업들을 알려줘"
    - "이번 달 예정된 UFC 카드들을 보여줘"
    - "기대되는 다음 UFC 경기들이 뭐야?"
    """
    async with async_db_session() as session:
        results = await event_composer.get_upcoming_events_with_featured_matches(session, limit)
        return [result.model_dump() for result in results]


@mcp.tool()
async def compare_events_by_performance(event_id1: int, event_id2: int) -> Optional[Dict]:
    """
    두 이벤트의 성과를 비교 분석합니다.
    
    이 도구는 두 개의 UFC 이벤트를 여러 지표로 비교합니다. 
    매치 수, 메인 이벤트 수, 결승 방법 등을 분석하여 어느 이벤트가 더 나은 성과를 보였는지 평가합니다.
    
    Args:
        event_id1 (int): 첫 번째 이벤트의 고유 ID 번호
        event_id2 (int): 두 번째 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 두 이벤트의 비교 분석 결과
        {
            "event1": Dict,  # 첫 번째 이벤트 정보와 통계
            "event2": Dict,  # 두 번째 이벤트 정보와 통계
            "comparison": Dict  # 비교 결과 (어느 이벤트가 더 나은지)
        }
    
    사용 시점:
    - 사용자가 두 이벤트의 품질이나 성과를 비교하고 싶을 때
    - 어떤 이벤트가 더 볼거리가 많았는지 분석하고 싶을 때
    - 과거 이벤트들의 상대적 평가가 필요할 때
    
    사용자 질문 예시:
    - "UFC 300과 UFC 299 중 어느 게 더 좋았어?"
    - "이 두 이벤트를 비교해서 분석해줘"
    - "어떤 이벤트가 더 많은 볼거리를 제공했어?"
    - "두 이벤트의 카드 품질을 비교해줘"
    """
    async with async_db_session() as session:
        result = await event_composer.compare_events_by_performance(session, event_id1, event_id2)
        return result.model_dump() if result else None


@mcp.tool()
async def get_event_rankings_impact(event_id: int) -> Dict:
    """
    특정 이벤트가 파이터 랭킹에 미친 영향을 분석합니다.
    
    이 도구는 UFC 이벤트 후 파이터들의 랭킹 변동 가능성을 분석합니다.
    랭킹된 파이터들의 경기 결과와 그것이 랭킹에 미칠 영향, 타이틀 도전 기회 등을 평가합니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Dict: 이벤트의 랭킹 영향 분석 결과
        {
            "event_id": int,
            "ranking_impacts": List[Dict],  # 매치별 랭킹 영향
            "summary": Dict  # 영향 요약 (랭킹 파이터 참여 매치 수, 타이틀 관련 매치 수)
        }
    
    사용 시점:
    - 사용자가 이벤트 후 랭킹 변화를 예측하고 싶을 때
    - 어떤 파이터들의 랭킹이 상승/하락할지 궁금할 때
    - 타이틀 도전권에 영향을 미친 경기들을 분석하고 싶을 때
    
    사용자 질문 예시:
    - "이번 이벤트 후 랭킹이 어떻게 바뀔까?"
    - "누구의 랭킹이 올라가고 누구의 랭킹이 내려갈까?"
    - "타이틀 도전에 영향을 준 경기들이 있어?"
    - "이벤트가 랭킹 판도에 미친 영향을 분석해줘"
    """
    async with async_db_session() as session:
        result = await event_composer.get_event_rankings_impact(session, event_id)
        return result.model_dump()


# Match Composer Tools

@mcp.tool()
async def get_fight_of_the_night_candidates(event_id: int) -> Optional[Dict]:
    """
    특정 이벤트에서 Fight of the Night 후보가 될만한 경기들을 분석합니다.
    
    이 도구는 UFC 이벤트의 가장 흥미진진했던 경기들을 찾아 FOTN 보너스 수상 후보를 분석합니다.
    경기 지속 시간, 결승 방법, 통계적 성과, 카드 위치 등을 종합적으로 고려하여 점수를 매깁니다.
    
    Args:
        event_id (int): 분석할 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: FOTN 후보 분석 결과
        {
            "event": Dict,  # 이벤트 기본 정보
            "fotn_candidates": List[Dict],  # 상위 5개 후보 경기 (점수순)
            "analysis_criteria": str  # 분석 기준 설명
        }
    
    사용 시점:
    - 사용자가 특정 이벤트의 최고 경기를 알고 싶을 때
    - FOTN 보너스 수상 예상 경기를 분석하고 싶을 때
    - 이벤트의 하이라이트 매치들을 찾고 싶을 때
    
    사용자 질문 예시:
    - "UFC 300에서 가장 재미있었던 경기는 뭐야?"
    - "이번 이벤트 FOTN 후보들을 분석해줘"
    - "어떤 경기가 Fight of the Night을 받을 만해?"
    - "가장 박진감 넘쳤던 경기들을 보여줘"
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
    
    사용 시점:
    - 사용자가 이벤트 카드의 전반적인 수준을 알고 싶을 때
    - PPV 구매 가치를 판단하고 싶을 때
    - 이벤트의 스타파워와 매치업 질을 평가하고 싶을 때
    
    사용자 질문 예시:
    - "이번 UFC 카드 수준이 어때?"
    - "이 이벤트 볼 만한가?"
    - "카드 품질을 평가해줘"
    - "얼마나 좋은 매치업들이 있어?"
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
    
    사용 시점:
    - 사용자가 최근 베스트 매치들을 알고 싶을 때
    - 놓친 경기 중 볼 만한 것을 찾고 싶을 때
    - 특정 기간의 하이라이트를 요약하고 싶을 때
    
    사용자 질문 예시:
    - "최근 한 달간 가장 재미있었던 경기들을 보여줘"
    - "이번 주 베스트 매치는 뭐야?"
    - "올해 가장 흥미진진했던 경기 TOP 10은?"
    - "놓친 경기 중에 꼭 봐야 할 것들을 추천해줘"
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
    
    사용 시점:
    - 사용자가 극적인 역전승에 관심이 있을 때
    - 이벤트의 드라마틱한 순간들을 분석하고 싶을 때
    - 예상을 뒤엎은 결과들을 찾고 싶을 때
    
    사용자 질문 예시:
    - "이번 이벤트에서 역전승이 있었어?"
    - "극적인 컴백 승리가 있었는지 알려줘"
    - "업셋이나 서프라이즈 결과를 분석해줘"
    - "예상과 다른 결과들을 보여줘"
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
    
    사용 시점:
    - 사용자가 매치업의 흥미로운 대조점을 알고 싶을 때
    - 스타일적 우위가 결과에 어떤 영향을 미쳤는지 궁금할 때
    - 파이터 간의 차이점을 분석하고 싶을 때
    
    사용자 질문 예시:
    - "이 매치에서 두 파이터의 스타일 차이가 어땠어?"
    - "Orthodox vs Southpaw 매치업이었나?"
    - "신체 조건이나 경험 차이가 결과에 영향을 줬을까?"
    - "이 경기에서 어떤 스타일적 우위가 있었어?"
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
    
    사용 시점:
    - 사용자가 이벤트의 특별한 개인 성과에 관심이 있을 때
    - 통계적으로 뛰어난 퍼포먼스를 확인하고 싶을 때
    - Performance of the Night 후보를 찾고 싶을 때
    
    사용자 질문 예시:
    - "이번 이벤트에서 특별한 개인 성과가 있었어?"
    - "누가 가장 인상적인 스탯을 기록했어?"
    - "Performance Bonus를 받을 만한 선수가 있나?"
    - "통계적으로 뛰어난 퍼포먼스를 보여줘"
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
    
    사용 시점:
    - 사용자가 파이터의 전체 경기 이력을 보고 싶을 때
    - 특정 파이터의 커리어 궤적을 분석하고 싶을 때
    - 과거 상대방들과 결과를 확인하고 싶을 때
    
    사용자 질문 예시:
    - "존 존스의 모든 경기 기록을 보여줘"
    - "이 파이터가 지금까지 누구와 싸웠어?"
    - "커리어 전체 경기 이력이 궁금해"
    - "이 선수의 UFC 데뷔부터 지금까지 기록을 알려줘"
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
    
    사용 시점:
    - 사용자가 두 파이터의 과거 대전 기록을 알고 싶을 때
    - 리매치 전에 이전 경기 결과를 확인하고 싶을 때
    - 헤드투헤드 분석이 필요할 때
    
    사용자 질문 예시:
    - "존 존스와 다니엘 코미어가 언제 싸웠어?"
    - "이 두 파이터 과거에 맞붙은 적 있어?"
    - "이전 대전에서 누가 이겼어?"
    - "헤드투헤드 기록을 보여줘"
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
    
    사용 시점:
    - 사용자가 파이터의 전체적인 실력을 수치로 보고 싶을 때
    - 통계적 분석이나 비교가 필요할 때
    - 파이터의 강점과 약점을 파악하고 싶을 때
    
    사용자 질문 예시:
    - "코너 맥그리거의 전체 통계를 보여줘"
    - "이 파이터의 정확도는 어때?"
    - "테이크다운 성공률이나 녹다운 수치를 알려줘"
    - "전체 커리어 스탯을 종합해서 보여줘"
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
    
    사용 시점:
    - 사용자가 두 파이터의 실력을 비교하고 싶을 때
    - 경기 전 매치업 분석이 필요할 때
    - 어떤 파이터가 어떤 면에서 우위인지 알고 싶을 때
    
    사용자 질문 예시:
    - "존 존스와 스티페 미오치치 누가 더 강해?"
    - "이 두 파이터 통계를 비교해줘"
    - "누가 스트라이킹이 더 좋고 누가 그래플링이 더 좋아?"
    - "각각의 장단점을 비교 분석해줘"
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
    
    사용 시점:
    - 사용자가 특정 분야의 최고 파이터들을 알고 싶을 때
    - 통계 리더보드를 보고 싶을 때
    - 전적이나 기록을 비교하고 싶을 때
    
    사용자 질문 예시:
    - "UFC에서 가장 많이 이긴 파이터는 누구야?"
    - "승수 TOP 10을 보여줘"
    - "가장 많이 진 파이터들은?"
    - "무승부가 많은 선수들을 알려줘"
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
    
    사용 시점:
    - 사용자가 파이터의 커리어 발전 과정을 보고 싶을 때
    - 시간순으로 경기 흐름을 분석하고 싶을 때
    - 커리어 하이라이트나 전환점을 찾고 싶을 때
    
    사용자 질문 예시:
    - "코너 맥그리거의 커리어 타임라인을 보여줘"
    - "이 파이터가 언제부터 강해졌어?"
    - "커리어 하이라이트와 중요한 경기들을 알려줘"
    - "시간순으로 경기 기록을 정리해줘"
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
    
    사용 시점:
    - 사용자가 특정 스타일 매치업에서의 성과를 알고 싶을 때
    - Orthodox vs Southpaw 등 스탠스별 분석이 필요할 때
    - 다음 상대의 스탠스에 따른 예측을 하고 싶을 때
    
    사용자 질문 예시:
    - "존 존스는 사우스포 상대로 어떤 성적이야?"
    - "이 파이터가 오소독스 상대로 약한가?"
    - "스탠스별 승률을 분석해줘"
    - "사우스포 킬러로 유명한데 실제 기록은 어때?"
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
    
    사용 시점:
    - 사용자가 특정 체급의 경쟁 구도를 알고 싶을 때
    - 체급 내 최고 파이터들을 비교하고 싶을 때
    - 각 분야별 최강자를 찾고 싶을 때
    
    사용자 질문 예시:
    - "라이트헤비급 톱 5를 비교해줘"
    - "헤비급에서 누가 가장 강해?"
    - "이 체급에서 스트라이킹/그래플링 최강자는?"
    - "체급 내 경쟁이 치열한가?"
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
    
    사용 시점:
    - 사용자가 두 파이터의 가상 매치업 결과를 궁금해할 때
    - 실제 경기 전 승부 예측을 하고 싶을 때
    - 매치업 분석이 필요할 때
    
    사용자 질문 예시:
    - "존 존스 vs 프란시스 은가누 누가 이길까?"
    - "이 두 파이터가 싸우면 누가 이겨?"
    - "매치업을 분석하고 승부를 예측해줘"
    - "각각의 승률은 어떻게 될까?"
    """
    async with async_db_session() as session:
        result = await fighter_composer.predict_fight_outcome(session, fighter_id1, fighter_id2)
        return result.model_dump()