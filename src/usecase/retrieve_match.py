from services.match_services import MatchService
from exceptions.match_exception import MatchNotFoundException

async def retrieve_match(match_service: MatchService, match_id: int):
    match = await match_service.get_match(match_id)

    if not match:
        raise MatchNotFoundException(match_id)
    
    winner_stats = match.get_winner_stats()
    loser_stats = match.get_loser_stats()
    return {
        "match": match.to_dict(),
        "winner_stats": winner_stats.to_dict(),
        "loser_stats": loser_stats.to_dict()
    }
