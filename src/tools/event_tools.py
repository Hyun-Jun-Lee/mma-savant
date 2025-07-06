from typing import List, Dict, Optional, Any
from datetime import date

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from event import services as event_services
from event import repositories as event_repo


@mcp.tool()
async def get_event_info_by_id(event_id: int) -> Optional[Dict]:
    """
    특정 이벤트 ID로 이벤트의 기본 정보를 조회합니다.
    
    이 도구는 정확한 이벤트 ID를 알고 있을 때 사용합니다. 이벤트의 이름, 날짜, 장소 등 
    기본적인 정보를 빠르게 조회할 수 있습니다.
    
    Args:
        event_id (int): 조회할 이벤트의 고유 ID 번호
    
    Returns:
        Optional[Dict]: 이벤트 정보를 담은 딕셔너리 또는 None (이벤트가 없을 경우)
        {
            "id": int,
            "name": str,
            "event_date": str,
            "location": str,
            "url": str
        }
    
    사용 시점:
    - 다른 도구에서 이벤트 ID를 얻은 후 기본 정보가 필요할 때
    - 이벤트 ID가 명시적으로 제공되었을 때
    - 빠른 이벤트 정보 확인이 필요할 때
    
    사용자 질문 예시:
    - "이벤트 ID 123번이 뭐야?"
    - "이벤트 456의 정보를 알려줘"
    - "ID 789번 이벤트는 언제 어디서 열려?"
    """
    async with async_db_session() as session:
        event = await event_repo.get_event_by_id(session, int(event_id))
        if event:
            return event.model_dump()
        return None


@mcp.tool()
async def get_event_info_by_name(event_name: str) -> Optional[Dict]:
    """
    이벤트 이름으로 이벤트 정보를 조회합니다. (부분 매칭 지원)
    
    사용자가 UFC 이벤트 이름이나 번호를 언급했을 때 사용합니다. 
    부분 문자열 검색을 지원하므로 정확하지 않은 이름도 찾을 수 있습니다.
    
    Args:
        event_name (str): 조회할 이벤트의 이름 (부분 매칭 가능)
    
    Returns:
        Optional[Dict]: 이벤트 정보를 담은 딕셔너리 또는 None (이벤트가 없을 경우)
        {
            "id": int,
            "name": str,
            "event_date": str,
            "location": str,
            "url": str
        }
    
    사용 시점:
    - 사용자가 특정 UFC 이벤트 이름을 언급했을 때
    - "UFC 300", "Fight Night" 등 이벤트명으로 검색할 때
    - 이벤트 이름의 일부만 기억하는 경우
    
    사용자 질문 예시:
    - "UFC 300에 대해 알려줘"
    - "UFC Fight Night London은 언제야?"
    - "올해 가장 큰 UFC 이벤트는 뭐야?"
    - "이번 주 UFC 이벤트가 있어?"
    """
    async with async_db_session() as session:
        event = await event_repo.get_event_by_name(session, event_name)
        if event:
            return event.model_dump()
        return None


@mcp.tool()
async def search_events(query: str, search_type: str = "name", limit: int = 10) -> List[Dict]:
    """
    다양한 기준으로 이벤트를 검색하고 관련성 순으로 결과를 반환합니다.
    
    이 도구는 사용자가 모호한 검색어나 여러 조건으로 이벤트를 찾고자 할 때 사용합니다.
    이름, 장소, 또는 모든 기준으로 검색할 수 있으며 관련성 점수와 함께 결과를 제공합니다.
    
    Args:
        query (str): 검색할 키워드 (이벤트명, 장소명 등)
        search_type (str, optional): 검색 타입 ("name", "location", "all"). 기본값은 "name"
        limit (int, optional): 반환할 최대 결과 수. 기본값은 10
    
    Returns:
        List[Dict]: 검색 결과 목록, 각 항목은 다음을 포함:
        [
            {
                "event": Dict,
                "match_type": str,
                "relevance": float
            }
        ]
    
    사용 시점:
    - 사용자가 여러 이벤트 중에서 찾고 있는 경우
    - 검색어가 모호하거나 여러 결과가 예상될 때
    - 장소나 이름으로 동시에 검색하고 싶을 때
    - 관련성 있는 여러 이벤트를 비교하고 싶을 때
    
    사용자 질문 예시:
    - "라스베가스에서 열린 UFC 이벤트들을 찾아줘"
    - "300과 관련된 모든 UFC 이벤트 보여줘"
    - "런던에서 열린 이벤트들 중 어떤 게 있어?"
    - "올해 가장 큰 이벤트들을 찾아봐"
    """
    async with async_db_session() as session:
        results = await event_services.search_events(session, query, search_type, limit)
        return [result for result in results]


@mcp.tool()
async def get_upcoming_events(limit: int = 5) -> List[Dict]:
    """
    다가오는 UFC/MMA 이벤트들을 날짜순으로 조회합니다.
    
    사용자가 미래의 이벤트, 예정된 경기, 다음에 볼 수 있는 이벤트에 대해 물어볼 때 사용합니다.
    가장 가까운 이벤트부터 시간순으로 정렬되어 반환됩니다.
    
    Args:
        limit (int, optional): 반환할 최대 이벤트 수. 기본값은 5
    
    Returns:
        List[Dict]: 다가오는 이벤트 목록 (날짜 오름차순)
    
    사용 시점:
    - 사용자가 다가오는 이벤트에 대해 관심을 보일 때
    - 미래의 경기 일정을 확인하고 싶을 때
    - 다음에 볼 수 있는 UFC 이벤트를 알고 싶을 때
    
    사용자 질문 예시:
    - "다음에 있을 UFC 이벤트가 언제야?"
    - "이번 달에 어떤 UFC 경기가 있어?"
    - "앞으로 예정된 이벤트들을 보여줘"
    - "다가오는 UFC 일정을 알려줘"
    - "언제 다음 경기를 볼 수 있어?"
    """
    async with async_db_session() as session:
        events = await event_repo.get_upcoming_events(session, limit)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_recent_events(limit: int = 5) -> List[Dict]:
    """
    최근에 개최된 UFC/MMA 이벤트들을 최신순으로 조회합니다.
    
    사용자가 지난 이벤트들, 놓친 경기, 최근 결과에 대해 궁금해할 때 사용합니다.
    가장 최근 이벤트부터 역시간순으로 정렬되어 반환됩니다.
    
    Args:
        limit (int, optional): 반환할 최대 이벤트 수. 기본값은 5
    
    Returns:
        List[Dict]: 최근 이벤트 목록 (날짜 내림차순)
    
    사용 시점:
    - 사용자가 최근 열린 이벤트에 대해 관심을 보일 때
    - 놓친 경기나 지난 이벤트를 확인하고 싶을 때
    - 최근 UFC 결과나 이벤트를 알고 싶을 때
    
    사용자 질문 예시:
    - "최근에 어떤 UFC 이벤트가 있었어?"
    - "지난주에 UFC 경기가 있었나?"
    - "내가 놓친 최근 이벤트들을 보여줘"
    - "최근 UFC 결과가 궁금해"
    - "어제 UFC 있었어?"
    """
    async with async_db_session() as session:
        events = await event_repo.get_recent_events(session, limit)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_next_and_last_events() -> Dict[str, Any]:
    """
    가장 가까운 다음 이벤트와 가장 최근 이벤트 정보를 날짜 계산과 함께 제공합니다.
    
    사용자가 UFC 일정의 전체적인 상황을 파악하고 싶거나, 다음 이벤트까지 얼마나 남았는지,
    마지막 이벤트가 언제였는지 등 시간적 맥락이 중요한 질문을 할 때 사용합니다.
    
    Returns:
        Dict[str, Any]: 다음/최근 이벤트 정보와 날짜 계산 결과
        {
            "next_event": Dict | None,
            "last_event": Dict | None, 
            "days_until_next": int,
            "days_since_last": int
        }
    
    사용 시점:
    - 사용자가 UFC 일정의 전반적인 상황을 알고 싶을 때
    - 다음 이벤트까지의 대기 시간을 궁금해할 때
    - 최근 이벤트로부터 얼마나 시간이 지났는지 궁금할 때
    - UFC 팬이 다음 경기를 기다리는 맥락에서 질문할 때
    
    사용자 질문 예시:
    - "다음 UFC까지 얼마나 남았어?"
    - "마지막 UFC가 언제였고 다음은 언제야?"
    - "UFC 일정이 어떻게 돼?"
    - "얼마나 기다려야 다음 경기를 볼 수 있어?"
    - "UFC 휴식기가 얼마나 길어?"
    """
    async with async_db_session() as session:
        result = await event_services.get_next_and_last_events(session)
        
        formatted_result = {}
        if result.get("next_event"):
            formatted_result["next_event"] = result["next_event"].model_dump()
        else:
            formatted_result["next_event"] = None
            
        if result.get("last_event"):
            formatted_result["last_event"] = result["last_event"].model_dump()
        else:
            formatted_result["last_event"] = None
            
        if "days_until_next" in result:
            formatted_result["days_until_next"] = result["days_until_next"]
        if "days_since_last" in result:
            formatted_result["days_since_last"] = result["days_since_last"]
            
        return formatted_result


@mcp.tool()
async def get_event_timeline(period: str = "month") -> Dict[str, Any]:
    """
    지정된 기간에 대한 이벤트 타임라인을 조회합니다.
    
    Args:
        period (str, optional): 타임라인 기간 ("month", "year" 등). 기본값은 "month"
    
    Returns:
        Dict[str, Any]: 타임라인 정보를 담은 딕셔너리
        {
            "period": str,
            "current_period": str,
            "previous_events": List[Dict],
            "current_events": List[Dict],
            "upcoming_events": List[Dict]
        }
    """
    async with async_db_session() as session:
        timeline = await event_services.get_event_timeline(session, period)
        
        formatted_timeline = {
            "period": timeline["period"],
            "current_period": timeline["current_period"],
            "previous_events": [event.model_dump() for event in timeline["previous_events"]],
            "current_events": [event.model_dump() for event in timeline["current_events"]],
            "upcoming_events": [event.model_dump() for event in timeline["upcoming_events"]]
        }
        
        return formatted_timeline


@mcp.tool()
async def get_event_summary(event_id: int) -> Optional[Dict[str, Any]]:
    """
    특정 이벤트의 요약 정보를 조회합니다.
    이벤트 기본 정보와 통계 정보를 포함합니다.
    
    Args:
        event_id (int): 조회할 이벤트의 ID
    
    Returns:
        Optional[Dict[str, Any]]: 이벤트 요약 정보를 담은 딕셔너리 또는 None
        {
            "event": Dict,
            "stats": Dict
        }
    """
    async with async_db_session() as session:
        summary = await event_services.get_event_summary(session, int(event_id))
        if summary:
            formatted_summary = {
                "event": summary["event"].model_dump(),
                "stats": summary["stats"]
            }
            return formatted_summary
        return None


@mcp.tool()
async def get_events_by_location(location: str) -> List[Dict]:
    """
    특정 장소나 도시에서 개최된 모든 이벤트들을 조회합니다.
    
    사용자가 특정 도시, 국가, 또는 경기장에서 열린 UFC 이벤트들에 관심이 있을 때 사용합니다.
    부분 문자열 매칭을 지원하므로 정확한 장소명을 몰라도 검색 가능합니다.
    
    Args:
        location (str): 검색할 장소 이름 (도시, 국가, 경기장 등)
    
    Returns:
        List[Dict]: 해당 장소에서 개최된 이벤트 목록 (최신순)
    
    사용 시점:
    - 사용자가 특정 도시나 국가의 UFC 이벤트에 관심이 있을 때
    - 여행 지역의 UFC 이벤트 역사를 알고 싶을 때
    - 특정 장소에서의 UFC 개최 빈도를 궁금해할 때
    
    사용자 질문 예시:
    - "라스베가스에서 열린 UFC 이벤트들을 보여줘"
    - "한국에서 UFC 이벤트가 열린 적 있어?"
    - "런던에서 몇 번이나 UFC가 열렸어?"
    - "일본에서 열린 UFC 이벤트가 궁금해"
    - "브라질에서 UFC 이벤트 역사를 알려줘"
    """
    async with async_db_session() as session:
        events = await event_repo.get_events_by_location(session, location)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_events_by_year(year: int) -> List[Dict]:
    """
    특정 연도에 개최된 모든 이벤트를 조회합니다.
    
    Args:
        year (int): 조회할 연도
    
    Returns:
        List[Dict]: 해당 연도의 이벤트 목록
    """
    async with async_db_session() as session:
        events = await event_repo.get_events_by_year(session, year)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_events_by_month(year: int, month: int) -> List[Dict]:
    """
    특정 연도와 월에 개최된 모든 이벤트를 조회합니다.
    
    Args:
        year (int): 조회할 연도
        month (int): 조회할 월(1-12)
    
    Returns:
        List[Dict]: 해당 연도와 월의 이벤트 목록
    """
    async with async_db_session() as session:
        events = await event_repo.get_events_by_month(session, year, month)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_events_calendar(year: int, month: Optional[int] = None) -> Dict[str, Any]:
    """
    특정 연도 또는 연도와 월에 대한 이벤트 캘린더를 조회합니다.
    월이 지정되면 일별 이벤트 목록을, 월이 지정되지 않으면 월별 이벤트 요약을 반환합니다.
    
    Args:
        year (int): 조회할 연도
        month (Optional[int], optional): 조회할 월(1-12). None이면 연간 캘린더를 반환
    
    Returns:
        Dict[str, Any]: 캘린더 정보를 담은 딕셔너리
        월간 캘린더일 경우:
        {
            "type": "monthly",
            "year": int,
            "month": int,
            "total_events": int,
            "calendar": {일자: [이벤트 목록]}
        }
        연간 캘린더일 경우:
        {
            "type": "yearly",
            "year": int,
            "total_events": int,
            "monthly_breakdown": {월: {"count": int, "events": [이벤트 목록]}}
        }
    """
    async with async_db_session() as session:
        calendar_data = await event_services.get_events_calendar(session, year, month)
        
        if calendar_data["type"] == "monthly":
            formatted_calendar = {
                "type": calendar_data["type"],
                "year": calendar_data["year"],
                "month": calendar_data["month"],
                "total_events": calendar_data["total_events"],
                "calendar": {}
            }
            
            for day, events in calendar_data["calendar"].items():
                formatted_calendar["calendar"][day] = [event.model_dump() for event in events]
                
        else:  # yearly
            formatted_calendar = {
                "type": calendar_data["type"],
                "year": calendar_data["year"],
                "total_events": calendar_data["total_events"],
                "monthly_breakdown": {}
            }
            
            for month, data in calendar_data["monthly_breakdown"].items():
                formatted_calendar["monthly_breakdown"][month] = {
                    "count": data["count"],
                    "events": [event.model_dump() for event in data["events"]]
                }
        
        return formatted_calendar


@mcp.tool()
async def get_location_statistics() -> Dict[str, Any]:
    """
    이벤트 개최 장소에 관한 통계 정보를 조회합니다.
    가장 많은 이벤트가 열린 장소, 국가별 이벤트 수 등의 정보를 제공합니다.
    
    Returns:
        Dict[str, Any]: 장소 통계 정보를 담은 딕셔너리
    """

    async with async_db_session() as session:
        stats = await event_services.get_location_statistics(session)
        return stats


@mcp.tool()
async def get_event_recommendations(recommendation_type: str = "upcoming") -> Dict[str, Any]:
    """
    사용자에게 맞춤형 이벤트 추천을 제공합니다.
    
    사용자가 어떤 이벤트를 봐야 할지 모르거나, 추천을 요청하거나, 
    인기 있는 이벤트에 관심을 보일 때 사용합니다.
    
    Args:
        recommendation_type (str, optional): 추천 유형
            - "upcoming": 다가오는 추천 이벤트
            - "recent": 최근 개최된 인기 이벤트  
            - "popular": 인기 있는 이벤트
            기본값은 "upcoming"
    
    Returns:
        Dict[str, Any]: 추천 정보와 설명을 포함한 딕셔너리
        {
            "type": str,
            "title": str,
            "description": str,
            "events": List[Dict]
        }
    
    사용 시점:
    - 사용자가 어떤 이벤트를 봐야 할지 추천을 요청할 때
    - UFC 입문자가 어떤 이벤트부터 봐야 할지 물어볼 때
    - 인기 있는 이벤트나 놓치면 안 되는 이벤트를 궁금해할 때
    
    사용자 질문 예시:
    - "어떤 UFC 이벤트를 추천해줄 수 있어?"
    - "봐야 할 인기 있는 UFC 이벤트가 있어?"
    - "UFC 초보자에게 추천할만한 이벤트는?"
    - "놓치면 안 되는 다가오는 이벤트가 있어?"
    - "가장 기대되는 UFC 이벤트는 뭐야?"
    """
    async with async_db_session() as session:
        recommendations = await event_services.get_event_recommendations(session, recommendation_type)
        
        # EventSchema ��D dict\ �X
        formatted_recommendations = {
            "type": recommendations["type"],
            "title": recommendations["title"],
            "description": recommendations["description"],
            "events": [event.model_dump() for event in recommendations["events"]]
        }
        
        return formatted_recommendations


@mcp.tool()
async def get_event_trends(period: str = "yearly") -> Dict[str, Any]:
    """
    지정된 기간에 대한 이벤트 트렌드 정보를 조회합니다.
    기간별 이벤트 개최 횟수, 인기 장소 등의 트렌드 정보를 제공합니다.
    
    Args:
        period (str, optional): 트렌드 분석 기간 ("yearly", "monthly" 등). 기본값은 "yearly"
    
    Returns:
        Dict[str, Any]: 트렌드 정보를 담은 딕셔너리
    """
    async with async_db_session() as session:
        trends = await event_services.get_event_trends(session, period)
        return trends


@mcp.tool()
async def get_events_by_date_range(start_year: int, start_month: int, start_day: int, 
                                  end_year: int, end_month: int, end_day: int) -> List[Dict]:
    """
    지정된 날짜 범위 내에 개최된 이벤트들을 조회합니다.
    
    Args:
        start_year (int): 시작 날짜의 연도
        start_month (int): 시작 날짜의 월(1-12)
        start_day (int): 시작 날짜의 일
        end_year (int): 종료 날짜의 연도
        end_month (int): 종료 날짜의 월(1-12)
        end_day (int): 종료 날짜의 일
    
    Returns:
        List[Dict]: 지정된 날짜 범위 내의 이벤트 목록
    """
    async with async_db_session() as session:
        start_date = date(start_year, start_month, start_day)
        end_date = date(end_year, end_month, end_day)
        events = await event_repo.get_events_date_range(session, start_date, end_date)
        return [event.model_dump() for event in events]


@mcp.tool()
async def get_event_count_by_year(year: int) -> int:
    """
    특정 연도에 개최된 이벤트 수를 반환합니다.
    
    Args:
        year (int): 조회할 연도
    
    Returns:
        int: 해당 연도의 이벤트 개수
    """
    async with async_db_session() as session:
        count = await event_repo.get_event_count_by_year(session, year)
        return count


@mcp.tool()
async def get_event_count_by_location(location: str) -> int:
    """
    특정 장소에서 개최된 이벤트 수를 반환합니다.
    부분 일치 검색을 지원합니다 (대소문자 구분 없음).
    
    Args:
        location (str): 검색할 장소 이름
    
    Returns:
        int: 해당 장소의 이벤트 개수
    """
    async with async_db_session() as session:
        count = await event_repo.get_event_count_by_location(session, location)
        return count