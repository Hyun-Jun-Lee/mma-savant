from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from match.exceptions import (
    MatchNotFoundError, MatchValidationError, MatchQueryError
)
from match.dto import MatchDetailDTO, MatchWithResultDTO
from match.models import MatchSchema
from match import repositories as match_repo


async def get_match_detail(session: AsyncSession, match_id: int) -> MatchDetailDTO:
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

        return MatchDetailDTO(
            match=match,
            fighters=participants.fighters if participants else [],
            statistics=statistics
        )

    except MatchNotFoundError:
        raise
    except MatchValidationError:
        raise
    except Exception as e:
        raise MatchQueryError("get_match_detail", {"match_id": match_id}, str(e))


async def get_match_with_winner_loser(session: AsyncSession, match_id: int) -> MatchWithResultDTO:
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


async def get_matches_between_fighters(session: AsyncSession, fighter_id_1: int, fighter_id_2: int) -> List[MatchSchema]:
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
