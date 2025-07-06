from typing import List, Dict, Optional

from tools.main import mcp
from database import *
from database.connection.postgres_conn import async_db_session
from fighter import services as fighter_services

@mcp.tool()
async def get_fighter_info_by_id(fighter_id: int) -> Optional[Dict]:
    """
    Get fighter info by fighter_id
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_id(session, int(fighter_id))
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_name(fighter_name: str) -> Optional[Dict]:
    """
    Get fighter info by fighter_name
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_name(session, fighter_name)
    return fighter_with_ranking.model_dump()

@mcp.tool()
async def get_fighter_info_by_nickname(fighter_nickname: str) -> Optional[Dict]:
    """
    Get fighter info by fighter_nickname
    """

    async with async_db_session() as session:
        fighter_with_ranking = await fighter_services.get_fighter_by_nickname(session, fighter_nickname)
    return fighter_with_ranking.model_dump()