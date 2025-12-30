"""
Match Services 테스트
match/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch

from match import services as match_service
from match.exceptions import (
    MatchNotFoundError, MatchValidationError, MatchQueryError
)
from match.dto import MatchDetailDTO, MatchWithResultDTO, MatchStatisticsDTO, CombinedMatchStatsDTO


@pytest.mark.asyncio
async def test_get_match_detail_success(clean_test_session):
    """매치 상세 정보 조회 성공 테스트"""
    # Given: Mock 데이터 설정
    from match.models import MatchSchema
    from match.dto import MatchWithFightersDTO

    mock_match = MatchSchema(
        id=1, event_id=1, weight_class_id=1, method="KO", result_round=1, time="5:00",
        order=1, is_main_event=False, detail_url="test", created_at=None, updated_at=None
    )
    mock_participants = MatchWithFightersDTO(match=mock_match, fighters=[])
    mock_statistics = MatchStatisticsDTO(match_id=1, fighter_stats=[], combined_stats=CombinedMatchStatsDTO())

    with patch('match.services.match_repo.get_match_by_id', return_value=mock_match):
        with patch('match.services.match_repo.get_match_with_participants', return_value=mock_participants):
            with patch('match.services.match_repo.get_match_statistics', return_value=mock_statistics):
                # When: 매치 상세 정보 조회
                result = await match_service.get_match_detail(clean_test_session, 1)

    # Then: MatchDetailDTO 반환
    assert isinstance(result, MatchDetailDTO)
    assert result.match == mock_match
    assert isinstance(result.fighters, list)
    assert result.statistics == mock_statistics


@pytest.mark.asyncio
async def test_get_match_detail_nonexistent(clean_test_session):
    """존재하지 않는 매치 상세 정보 조회 테스트"""
    # When & Then: 존재하지 않는 매치 ID로 조회시 MatchNotFoundError 발생
    with pytest.raises(MatchNotFoundError, match="Match not found with id"):
        await match_service.get_match_detail(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_match_detail_invalid_match_id(clean_test_session):
    """잘못된 매치 ID 처리 테스트"""
    # When & Then: 잘못된 매치 ID로 조회시 MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, -1)

    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, 0)

    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, "invalid")


@pytest.mark.asyncio
async def test_get_match_detail_repository_error(clean_test_session):
    """get_match_detail Repository 에러 처리 테스트"""
    # Given: match_repo에서 예외 발생하도록 설정
    with patch('match.services.match_repo.get_match_by_id', side_effect=Exception("Database connection error")):

        # When & Then: MatchQueryError로 래핑되어 발생
        with pytest.raises(MatchQueryError, match="Match query 'get_match_detail' failed"):
            await match_service.get_match_detail(clean_test_session, 1)


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_success(clean_test_session):
    """승자/패자 정보 조회 성공 테스트"""
    # Given: Mock DTO 데이터 설정
    from match.models import MatchSchema
    from fighter.models import FighterSchema
    from match.dto import FighterResultDTO

    mock_match = MatchSchema(
        id=1, event_id=1, weight_class_id=1, method="KO", result_round=1, time="5:00",
        order=1, is_main_event=False, detail_url="test", created_at=None, updated_at=None
    )
    mock_winner = FighterResultDTO(
        fighter=FighterSchema(id=1, name="Fighter A", nickname="", dob=None, height=180, weight=70,
                            reach=180, stance="Orthodox", nationality="USA", created_at=None, updated_at=None),
        result="win"
    )
    mock_loser = FighterResultDTO(
        fighter=FighterSchema(id=2, name="Fighter B", nickname="", dob=None, height=180, weight=70,
                            reach=180, stance="Orthodox", nationality="USA", created_at=None, updated_at=None),
        result="loss"
    )
    mock_result = MatchWithResultDTO(
        match=mock_match,
        fighters=[mock_winner, mock_loser],
        winner=mock_winner,
        loser=mock_loser
    )

    with patch('match.services.match_repo.get_match_with_winner_loser', return_value=mock_result):
        # When: 매치 승부 결과 조회
        result = await match_service.get_match_with_winner_loser(clean_test_session, 1)

    # Then: MatchWithResultDTO 반환
    assert isinstance(result, MatchWithResultDTO)
    assert result.winner is not None
    assert result.loser is not None


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_not_found(clean_test_session):
    """존재하지 않는 매치 승부 결과 조회 테스트"""
    # Given: Repository에서 None 반환
    with patch('match.services.match_repo.get_match_with_winner_loser', return_value=None):

        # When & Then: MatchNotFoundError 발생
        with pytest.raises(MatchNotFoundError, match="Match not found with id"):
            await match_service.get_match_with_winner_loser(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_matches_between_fighters_success(clean_test_session):
    """파이터 간 대결 조회 성공 테스트"""
    # Given: Mock 데이터 설정
    mock_matches = [
        AsyncMock(id=1, event_id=1),
        AsyncMock(id=2, event_id=2)
    ]

    with patch('match.services.match_repo.get_matches_between_fighters', return_value=mock_matches):
        # When: 두 파이터 간 대결 조회
        result = await match_service.get_matches_between_fighters(clean_test_session, 1, 2)

    # Then: 매치 리스트 반환
    assert result == mock_matches


@pytest.mark.asyncio
async def test_get_matches_between_fighters_invalid_ids(clean_test_session):
    """잘못된 파이터 ID 처리 테스트"""
    # When & Then: 잘못된 파이터 ID로 조회시 MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="fighter_id_1 must be a positive integer"):
        await match_service.get_matches_between_fighters(clean_test_session, -1, 2)

    with pytest.raises(MatchValidationError, match="fighter_id_2 must be a positive integer"):
        await match_service.get_matches_between_fighters(clean_test_session, 1, 0)

    with pytest.raises(MatchValidationError, match="fighter_id_1 and fighter_id_2 cannot be the same"):
        await match_service.get_matches_between_fighters(clean_test_session, 1, 1)


if __name__ == "__main__":
    print("Match Services 테스트 실행...")
    print("✅ 비즈니스 로직 레이어 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_services.py -v")