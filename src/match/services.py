from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from match.exceptions import (
    MatchNotFoundError, MatchValidationError, MatchQueryError
)

from match import repositories as match_repo

async def get_match_detail(session: AsyncSession, match_id: int) -> Dict:
    """
    특정 경기의 정보와 fighter들의 stat을 조회합니다.
    """
    # 입력 검증
    if not isinstance(match_id, int) or match_id <= 0:
        raise MatchValidationError("match_id", match_id, "match_id must be a positive integer")
    
    try:
        # 매치 기본 정보 조회
        match = await match_repo.get_match_by_id(session, match_id)
        if not match:
            raise MatchNotFoundError(match_id, "id")
        
        # 매치 참가자 정보 조회
        participants = await match_repo.get_match_with_participants(session, match_id)
        
        # 매치 통계 정보 조회
        statistics = await match_repo.get_match_statistics(session, match_id)
        
        return {
            "match": match,
            "fighters": participants["fighters"] if participants else [],
            "statistics": statistics if statistics else {}
        }
    
    except MatchNotFoundError:
        raise
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_match_detail", {"match_id": match_id}, str(e))

async def get_highest_stats_matches(session: AsyncSession, stat_name: str, limit: int = 10):
    """
    특정 스탯 기준 TOP 10 경기 조회
    """
    # 입력 검증
    if not stat_name or not stat_name.strip():
        raise MatchValidationError("stat_name", stat_name, "Stat name cannot be empty")
    
    if not isinstance(limit, int) or limit <= 0:
        raise MatchValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        # 스탯 이름에 따른 매치 조회
        if stat_name == "total_strikes":
            # 높은 활동량 매치들 조회 (총 타격 수 기준)
            return await match_repo.get_matches_with_high_activity(session, min_strikes=200, limit=limit)
        
        elif stat_name == "knockouts":
            # KO/TKO로 끝난 매치들
            return await match_repo.get_matches_by_finish_method(session, "KO", limit)
        
        elif stat_name == "submissions":
            # 서브미션으로 끝난 매치들
            return await match_repo.get_matches_by_finish_method(session, "Submission", limit)
        
        elif stat_name == "long_fights":
            # 긴 경기들 (3라운드 이상)
            return await match_repo.get_matches_by_duration(session, min_rounds=3, limit=limit)
        
        elif stat_name == "quick_finishes":
            # 빠른 피니시 (1라운드)
            return await match_repo.get_matches_by_duration(session, max_rounds=1, limit=limit)
        
        else:
            # 기본적으로 높은 활동량 매치 반환
            return await match_repo.get_matches_with_high_activity(session, min_strikes=150, limit=limit)
    
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_highest_stats_matches", {"stat_name": stat_name, "limit": limit}, str(e))


async def get_matches_by_finish_method(session: AsyncSession, method: str, limit: int = 20) -> list:
    """
    특정 피니시 방법으로 끝난 매치들을 조회합니다.
    """
    # 입력 검증
    if not method or not method.strip():
        raise MatchValidationError("method", method, "Finish method cannot be empty")
    
    if not isinstance(limit, int) or limit <= 0:
        raise MatchValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        return await match_repo.get_matches_by_finish_method(session, method, limit)
    
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_matches_by_finish_method", {"method": method, "limit": limit}, str(e))


async def get_matches_by_duration(session: AsyncSession, min_rounds: int = None, max_rounds: int = None, limit: int = 20) -> list:
    """
    특정 지속 시간(라운드 수) 조건에 맞는 매치들을 조회합니다.
    """
    # 입력 검증
    if min_rounds is not None and (not isinstance(min_rounds, int) or min_rounds <= 0):
        raise MatchValidationError("min_rounds", min_rounds, "min_rounds must be a positive integer or None")
    
    if max_rounds is not None and (not isinstance(max_rounds, int) or max_rounds <= 0):
        raise MatchValidationError("max_rounds", max_rounds, "max_rounds must be a positive integer or None")
    
    if min_rounds is not None and max_rounds is not None and min_rounds > max_rounds:
        raise MatchValidationError("rounds", f"min_rounds: {min_rounds}, max_rounds: {max_rounds}", "min_rounds cannot be greater than max_rounds")
    
    if not isinstance(limit, int) or limit <= 0:
        raise MatchValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        return await match_repo.get_matches_by_duration(session, min_rounds, max_rounds, limit)
    
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_matches_by_duration", {"min_rounds": min_rounds, "max_rounds": max_rounds, "limit": limit}, str(e))


async def get_match_with_winner_loser(session: AsyncSession, match_id: int) -> Dict:
    """
    특정 매치의 정보와 승자/패자 정보를 조회합니다.
    """
    # 입력 검증
    if not isinstance(match_id, int) or match_id <= 0:
        raise MatchValidationError("match_id", match_id, "match_id must be a positive integer")
    
    try:
        result = await match_repo.get_match_with_winner_loser(session, match_id)
        if not result:
            raise MatchNotFoundError(match_id, "id")
        
        return result
    
    except MatchNotFoundError:
        raise
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_match_with_winner_loser", {"match_id": match_id}, str(e))


async def get_matches_between_fighters(session: AsyncSession, fighter_id_1: int, fighter_id_2: int) -> list:
    """
    두 선수 간의 모든 대결 경기를 조회합니다.
    """
    # 입력 검증
    if not isinstance(fighter_id_1, int) or fighter_id_1 <= 0:
        raise MatchValidationError("fighter_id_1", fighter_id_1, "fighter_id_1 must be a positive integer")
    
    if not isinstance(fighter_id_2, int) or fighter_id_2 <= 0:
        raise MatchValidationError("fighter_id_2", fighter_id_2, "fighter_id_2 must be a positive integer")
    
    if fighter_id_1 == fighter_id_2:
        raise MatchValidationError("fighter_ids", f"{fighter_id_1}, {fighter_id_2}", "fighter_id_1 and fighter_id_2 cannot be the same")
    
    try:
        return await match_repo.get_matches_between_fighters(session, fighter_id_1, fighter_id_2)
    
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_matches_between_fighters", {"fighter_id_1": fighter_id_1, "fighter_id_2": fighter_id_2}, str(e))