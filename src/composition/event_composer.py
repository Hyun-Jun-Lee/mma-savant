from sqlalchemy.ext.asyncio import AsyncSession

async def get_event_with_all_matches(session: AsyncSession, event_name: int):
    """
    특정 이벤트에 속한 모든 경기와 승패결과를 조회합니다.
    """
    pass

async def get_recent_events_with_main_match(session: AsyncSession, limit: int = 10):
    """
    최근 event와 메인 이벤트 경기만 조회
    """
    pass