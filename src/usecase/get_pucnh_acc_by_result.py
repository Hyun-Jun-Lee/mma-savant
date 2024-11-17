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
