from typing import Optional, Literal, List

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.dto import FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO
from fighter.models import FighterSchema
from fighter import repositories as fighter_repo
from fighter.exceptions import (
    FighterNotFoundError, FighterValidationError, FighterQueryError,
    FighterWeightClassError, FighterSearchError
)

async def _build_fighter_with_rankings(session: AsyncSession, fighter: FighterSchema) -> Optional[FighterWithRankingsDTO]:
    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter.id)
    
    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_name = WeightClassSchema.get_name_by_id(ranking_obj.weight_class_id)
        if weight_class_name:  # None 값 체크
            ranking_result[weight_class_name] = ranking_obj.ranking
    
    return FighterWithRankingsDTO(
        fighter=fighter,
        rankings=ranking_result
    )

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> FighterWithRankingsDTO:
    """
    fighter_id로 fighter 조회.
    """
    # 입력 검증
    if not isinstance(fighter_id, int) or fighter_id <= 0:
        raise FighterValidationError("fighter_id", fighter_id, "fighter_id must be a positive integer")
    
    try:
        fighter = await fighter_repo.get_fighter_by_id(session, fighter_id)
        if not fighter:
            raise FighterNotFoundError(fighter_id, "id")

        return await _build_fighter_with_rankings(session, fighter)
    
    except FighterNotFoundError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_by_id", {"fighter_id": fighter_id}, str(e))
    

async def get_fighter_ranking_by_weight_class(session: AsyncSession, weight_class_name: str) -> WeightClassRankingsDTO:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    # 입력 검증
    if not weight_class_name or not weight_class_name.strip():
        raise FighterValidationError("weight_class_name", weight_class_name, "Weight class name cannot be empty")
    
    try:
        weight_class_id = WeightClassSchema.get_id_by_name(weight_class_name)
        if not weight_class_id:
            raise FighterWeightClassError(weight_class_name, f"Weight class '{weight_class_name}' not found")
            
        fighters = await fighter_repo.get_fighters_by_weight_class_ranking(session, weight_class_id)
        
        ranked_fighters = []
        for index, fighter in enumerate(fighters):
            ranked_fighters.append(
                RankedFighterDTO(
                    ranking=index + 1,
                    fighter=fighter
                )
            )
        
        ranked_fighters.sort(key=lambda x: x.ranking)
        
        return WeightClassRankingsDTO(
            weight_class_name=weight_class_name,
            rankings=ranked_fighters,
        )
    
    except FighterWeightClassError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_ranking_by_weight_class", {"weight_class_name": weight_class_name}, str(e))

async def get_top_fighters_by_record(session: AsyncSession, record: Literal["win", "loss", "draw"], weight_class_id: int = None, limit: int = 10) -> WeightClassRankingsDTO:
    """
    파이터의 기록(승,패,무) 기준으로 상위 limit개의 파이터 조회
    """
    # 입력 검증
    if record not in ["win", "loss", "draw"]:
        raise FighterValidationError("record", record, "record must be 'win', 'loss', or 'draw'")
    
    if not isinstance(limit, int) or limit <= 0:
        raise FighterValidationError("limit", limit, "limit must be a positive integer")
    
    if weight_class_id is not None and (not isinstance(weight_class_id, int) or weight_class_id <= 0):
        raise FighterValidationError("weight_class_id", weight_class_id, "weight_class_id must be a positive integer or None")
    
    try:
        fighter_with_rank = await fighter_repo.get_top_fighter_by_record(session, record, weight_class_id, limit)
        ranked_fighters = []
        
        weight_class_name = None
        if weight_class_id:
            weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
        
        for rank_dict in fighter_with_rank:
            ranked_fighter = RankedFighterDTO(
                ranking=rank_dict["ranking"],
                fighter=rank_dict["fighter"],  
            )
            ranked_fighters.append(ranked_fighter)
        
        return WeightClassRankingsDTO(
            weight_class_name=weight_class_name,
            rankings=ranked_fighters,
        )
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_top_fighters_by_record", {"record": record, "weight_class_id": weight_class_id, "limit": limit}, str(e))

async def search_fighters(session: AsyncSession, search_term: str, limit: int = 10) -> List[FighterWithRankingsDTO]:
    """
    이름이나 닉네임으로 파이터를 검색하고 랭킹 정보와 함께 반환합니다.
    """
    # 입력 검증
    if not search_term or not search_term.strip():
        raise FighterValidationError("search_term", search_term, "Search term cannot be empty")
    
    if not isinstance(limit, int) or limit <= 0:
        raise FighterValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        fighters = await fighter_repo.search_fighters_by_name(session, search_term, limit)
        
        results = []
        for fighter in fighters:
            fighter_with_rankings = await _build_fighter_with_rankings(session, fighter)
            if fighter_with_rankings:
                results.append(fighter_with_rankings)
        
        return results
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterSearchError({"search_term": search_term, "limit": limit}, str(e))

async def get_all_champions(session: AsyncSession) -> List[FighterWithRankingsDTO]:
    """
    현재 모든 챔피언들을 랭킹 정보와 함께 조회합니다.
    """
    try:
        champions = await fighter_repo.get_champions(session)
        
        results = []
        for champion in champions:
            champion_with_rankings = await _build_fighter_with_rankings(session, champion)
            if champion_with_rankings:
                results.append(champion_with_rankings)
        
        return results
    
    except Exception as e:
        raise FighterQueryError("get_all_champions", {}, str(e))
