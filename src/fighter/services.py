from typing import Optional, Literal, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.dto import (
    FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO,
    FightersByStanceDTO, UndefeatedFightersDTO, FightersByPhysicalAttributesDTO,
    FightersPerformanceAnalysisDTO, WeightClassDepthAnalysisDTO
)
from fighter.models import FighterSchema
from fighter import repositories as fighter_repo
from fighter.exceptions import (
    FighterNotFoundError, FighterValidationError, FighterQueryError, 
    FighterWeightClassError, FighterSearchError, FighterPerformanceError
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
    

async def get_fighter_by_name(session: AsyncSession, name: str) -> FighterWithRankingsDTO:
    """
    fighter_name로 fighter 조회.
    """
    # 입력 검증
    if not name or not name.strip():
        raise FighterValidationError("name", name, "Fighter name cannot be empty")
    
    try:
        fighter = await fighter_repo.get_fighter_by_name(session, name)
        if not fighter:
            raise FighterNotFoundError(name, "name")
        return await _build_fighter_with_rankings(session, fighter)
    
    except FighterNotFoundError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_by_name", {"name": name}, str(e))

async def get_fighter_by_nickname(session: AsyncSession, nickname: str) -> FighterWithRankingsDTO:
    """
    fighter_nickname로 fighter 조회.
    """
    # 입력 검증
    if not nickname or not nickname.strip():
        raise FighterValidationError("nickname", nickname, "Fighter nickname cannot be empty")
    
    try:
        fighter = await fighter_repo.get_fighter_by_nickname(session, nickname)
        if not fighter:
            raise FighterNotFoundError(nickname, "nickname")
        
        return await _build_fighter_with_rankings(session, fighter)
    
    except FighterNotFoundError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_by_nickname", {"nickname": nickname}, str(e))

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

async def get_fighters_by_stance_analysis(session: AsyncSession, stance: str) -> FightersByStanceDTO:
    """
    특정 스탠스의 파이터들을 분석 정보와 함께 제공합니다.
    """
    # 입력 검증
    if not stance or not stance.strip():
        raise FighterValidationError("stance", stance, "Stance cannot be empty")
    
    valid_stances = ["Orthodox", "Southpaw", "Switch", "Open Stance"]
    if stance not in valid_stances:
        raise FighterValidationError("stance", stance, f"stance must be one of: {', '.join(valid_stances)}")
    
    try:
        fighters = await fighter_repo.get_fighters_by_stance(session, stance)
        
        if not fighters:
            return FightersByStanceDTO(
                stance=stance,
                total_fighters=0,
                fighters=[],
                analysis={
                    "average_wins": 0,
                    "total_wins": 0,
                    "total_losses": 0,
                    "total_fights": 0,
                    "champions_count": 0,
                    "win_percentage": 0
                }
            )
        
        # 분석 정보 계산
        total_wins = sum(f.wins for f in fighters)
        total_losses = sum(f.losses for f in fighters)
        total_fights = sum(f.wins + f.losses + f.draws for f in fighters)
        avg_wins = total_wins / len(fighters) if fighters else 0
        champions_count = sum(1 for f in fighters if f.belt)
        
        return FightersByStanceDTO(
            stance=stance,
            total_fighters=len(fighters),
            fighters=fighters[:10],  # 상위 10명만 반환
            analysis={
                "average_wins": round(avg_wins, 2),
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_fights": total_fights,
                "champions_count": champions_count,
                "win_percentage": round((total_wins / total_fights * 100), 2) if total_fights > 0 else 0
            }
        )
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterPerformanceError(0, "stance_analysis", str(e))

async def get_undefeated_fighters_analysis(session: AsyncSession, min_wins: int = 5) -> UndefeatedFightersDTO:
    """
    무패 파이터들의 분석 정보를 제공합니다.
    """
    # 입력 검증
    if not isinstance(min_wins, int) or min_wins < 0:
        raise FighterValidationError("min_wins", min_wins, "min_wins must be a non-negative integer")
    
    try:
        undefeated = await fighter_repo.get_undefeated_fighters(session, min_wins)
        
        if not undefeated:
            return UndefeatedFightersDTO(
                total_undefeated=0,
                min_wins_threshold=min_wins,
                fighters=[],
                analysis={
                    "average_wins": 0,
                    "total_wins": 0,
                    "champions_count": 0,
                    "most_wins": 0
                }
            )
        
        # 무패 파이터들을 랭킹 정보와 함께 구성
        fighters_with_rankings = []
        for fighter in undefeated:
            fighter_with_rankings = await _build_fighter_with_rankings(session, fighter)
            if fighter_with_rankings:
                fighters_with_rankings.append(fighter_with_rankings)
        
        # 분석 정보
        total_wins = sum(f.fighter.wins for f in fighters_with_rankings)
        avg_wins = total_wins / len(fighters_with_rankings) if fighters_with_rankings else 0
        champions_count = sum(1 for f in fighters_with_rankings if f.fighter.belt)
        
        return UndefeatedFightersDTO(
            total_undefeated=len(fighters_with_rankings),
            min_wins_threshold=min_wins,
            fighters=fighters_with_rankings,
            analysis={
                "average_wins": round(avg_wins, 2),
                "total_wins": total_wins,
                "champions_count": champions_count,
                "most_wins": max(f.fighter.wins for f in fighters_with_rankings) if fighters_with_rankings else 0
            }
        )
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_undefeated_fighters_analysis", {"min_wins": min_wins}, str(e))

async def get_fighters_by_physical_attributes(
    session: AsyncSession,
    min_height: Optional[float] = None,
    max_height: Optional[float] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_reach: Optional[float] = None,
    limit: int = 20
) -> FightersByPhysicalAttributesDTO:
    """
    신체 조건으로 파이터들을 조회하고 분석 정보를 제공합니다.
    """
    fighters = await fighter_repo.get_fighters_by_physical_stats(
        session, min_height, max_height, min_weight, max_weight, min_reach, limit
    )
    
    if not fighters:
        return FightersByPhysicalAttributesDTO(
            criteria={
                "min_height": min_height,
                "max_height": max_height,
                "min_weight": min_weight,
                "max_weight": max_weight,
                "min_reach": min_reach
            },
            total_fighters=0,
            fighters=[],
            physical_analysis={
                "avg_height": 0,
                "avg_weight": 0,
                "avg_reach": 0,
                "height_range": {"min": 0, "max": 0},
                "weight_range": {"min": 0, "max": 0}
            }
        )
    
    # 신체 통계 계산
    heights = [f.height for f in fighters if f.height]
    weights = [f.weight for f in fighters if f.weight]
    reaches = [f.reach for f in fighters if f.reach]
    
    return FightersByPhysicalAttributesDTO(
        criteria={
            "min_height": min_height,
            "max_height": max_height,
            "min_weight": min_weight,
            "max_weight": max_weight,
            "min_reach": min_reach
        },
        total_fighters=len(fighters),
        fighters=fighters,
        physical_analysis={
            "avg_height": round(sum(heights) / len(heights), 2) if heights else 0,
            "avg_weight": round(sum(weights) / len(weights), 2) if weights else 0,
            "avg_reach": round(sum(reaches) / len(reaches), 2) if reaches else 0,
            "height_range": {
                "min": min(heights) if heights else 0,
                "max": max(heights) if heights else 0
            },
            "weight_range": {
                "min": min(weights) if weights else 0,
                "max": max(weights) if weights else 0
            }
        }
    )

async def get_fighters_performance_analysis(session: AsyncSession) -> FightersPerformanceAnalysisDTO:
    """
    전체 파이터들의 성과 분석을 제공합니다.
    """
    stats = await fighter_repo.get_fighters_statistics(session)
    win_percentage_leaders = await fighter_repo.get_fighters_by_win_percentage(session, min_fights=5, limit=10)
    
    return FightersPerformanceAnalysisDTO(
        overall_statistics=stats,
        win_percentage_leaders=win_percentage_leaders,
        performance_insights={
            "average_career_length": round((stats["avg_wins"] + stats["avg_losses"]), 2),
            "competitive_ratio": round(stats["avg_losses"] / stats["avg_wins"], 2) if stats["avg_wins"] > 0 else 0,
            "champion_percentage": round((stats["champions"] / stats["total_fighters"] * 100), 2) if stats["total_fighters"] > 0 else 0
        }
    )

async def get_weight_class_depth_analysis(session: AsyncSession, weight_class_name: str) -> WeightClassDepthAnalysisDTO:
    """
    특정 체급의 깊이 분석을 제공합니다.
    """
    weight_class_id = WeightClassSchema.get_id_by_name(weight_class_name)
    if not weight_class_id:
        raise fighter_exc.InvalidWeightClassError(weight_class_name)
    
    # 랭킹된 파이터들 조회
    ranked_fighters = await fighter_repo.get_ranked_fighters_by_weight_class(session, weight_class_id, limit=15)
    
    # 체급 내 총 파이터 수
    total_fighters = await fighter_repo.get_fighter_count_by_weight_class(session, weight_class_id)
    
    if not ranked_fighters:
        return WeightClassDepthAnalysisDTO(
            weight_class=weight_class_name,
            total_ranked_fighters=0,
            total_fighters_in_division=total_fighters,
            champion=None,
            ranked_fighters=[],
            depth_analysis={
                "average_wins_in_rankings": 0,
                "top_5_average_wins": 0,
                "ranking_competition": "low",
                "champion_dominance": 0
            }
        )
    
    # 챔피언 찾기 (랭킹 1위)
    champion = None
    for ranked_fighter in ranked_fighters:
        if ranked_fighter["ranking"] == 1:
            champion = ranked_fighter["fighter"]
            break
    
    # 분석 계산
    avg_wins = sum(rf["fighter"].wins for rf in ranked_fighters) / len(ranked_fighters)
    top_5_avg_wins = sum(rf["fighter"].wins for rf in ranked_fighters[:5]) / min(5, len(ranked_fighters))
    
    return WeightClassDepthAnalysisDTO(
        weight_class=weight_class_name,
        total_ranked_fighters=len(ranked_fighters),
        total_fighters_in_division=total_fighters,
        champion=champion,
        ranked_fighters=ranked_fighters,
        depth_analysis={
            "average_wins_in_rankings": round(avg_wins, 2),
            "top_5_average_wins": round(top_5_avg_wins, 2),
            "ranking_competition": "high" if len(ranked_fighters) >= 10 else "moderate" if len(ranked_fighters) >= 5 else "low",
            "champion_dominance": champion.wins if champion else 0
        }
    )
