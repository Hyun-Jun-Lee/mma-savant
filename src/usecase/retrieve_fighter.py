from services.fighter_services import FighterService
from exceptions.fighter_exception import FighterNotFoundException

async def retrieve_fighter(fighter_service: FighterService, fighter_id: int):
    fighter = await fighter_service.get_fighter(fighter_id)
    if not fighter:
        raise FighterNotFoundException(fighter_id)
    
    return fighter.to_dict()