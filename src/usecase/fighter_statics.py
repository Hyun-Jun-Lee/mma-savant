from exceptions.fighter_exception import FighterNotFoundException


async def get_fighter_punch_accuracy(match_service, fighter_service, fighter_id: int):
    """Fighter의 승리 및 패배 경기 펀치 성공률 반환"""

    fighter = await fighter_service.get_fighter(fighter_id)
    if not fighter:
        raise FighterNotFoundException(fighter_id)
    
    win_accuracy = await match_service.get_punch_accuracy_by_result(fighter_id, "win")
    loss_accuracy = await match_service.get_punch_accuracy_by_result(fighter_id, "loss")
    
    return {
        "win_accuracy": win_accuracy,
        "loss_accuracy": loss_accuracy
    }

async def get_fighter_with_statics(match_service, fighter_service, fighter_id: int):
    fighter = await fighter_service.get_fighter_by_id(fighter_id)

    matches_with_statics = await match_service.get_matches_with_statistics_by_fighter(fighter_id)

    formatted_matches = [
        {
            "match": match_data["match"].to_dict(),
            "statistics": match_data["statistics"].to_dict(),
        }
        for match_data in matches_with_statics
    ]

    return {
        "fighter": fighter.to_dict(),
        "matches": formatted_matches
    }

async def get_fighter_stat_by_result(match_service, fighter_service, fighter_id: int, result: str):
    fighter = await fighter_service.get_fighter_by_id(fighter_id)
    if not fighter:
        raise FighterNotFoundException(fighter_id)
    
    return await match_service.get_stat_by_result(fighter_id, result)

async def get_fighter_detail_stat_by_result(match_service, fighter_service, fighter_id: int, result: str):
    fighter = await fighter_service.get_fighter_by_id(fighter_id)
    if not fighter:
        raise FighterNotFoundException(fighter_id)
    
    return await match_service.get_detail_stats_by_result(fighter_id, result)