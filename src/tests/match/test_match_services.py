"""
Match Services 통합 테스트
match/services.py의 비즈니스 로직 레이어에 대한 통합 테스트
실제 테스트 DB를 사용하여 서비스 레이어 검증
"""
import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from match import services as match_service
from match import repositories as match_repo
from match.exceptions import (
    MatchNotFoundError, MatchValidationError, MatchQueryError
)
from match.dto import MatchDetailDTO, MatchWithResultDTO
from match.models import MatchModel, FighterMatchModel, BasicMatchStatModel, SigStrMatchStatModel
from fighter.models import FighterModel
from event.models import EventModel


# =============================================================================
# 헬퍼 함수: 테스트용 데이터 생성
# =============================================================================

async def create_test_event(session: AsyncSession, name: str = "Test Event") -> EventModel:
    """테스트용 이벤트 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    event = EventModel(
        name=f"{name}_{timestamp}",
        event_date=date(2024, 1, 15),
        location="Las Vegas, NV"
    )
    session.add(event)
    await session.flush()
    return event


async def create_test_fighter(
    session: AsyncSession,
    name: str,
    wins: int = 10,
    losses: int = 2
) -> FighterModel:
    """테스트용 파이터 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    fighter = FighterModel(
        name=f"{name}_{timestamp}",
        wins=wins,
        losses=losses,
        draws=0
    )
    session.add(fighter)
    await session.flush()
    return fighter


async def create_test_match(
    session: AsyncSession,
    event_id: int,
    method: str = "Decision - Unanimous",
    result_round: int = 3,
    time: str = "15:00",
    is_main_event: bool = False
) -> MatchModel:
    """테스트용 매치 생성"""
    match = MatchModel(
        event_id=event_id,
        weight_class_id=5,  # Welterweight
        method=method,
        result_round=result_round,
        time=time,
        order=1,
        is_main_event=is_main_event,
        detail_url=f"http://example.com/match/{datetime.now().strftime('%H%M%S%f')}"
    )
    session.add(match)
    await session.flush()
    return match


async def create_fighter_match(
    session: AsyncSession,
    fighter_id: int,
    match_id: int,
    result: str = "win"
) -> FighterMatchModel:
    """테스트용 파이터-매치 관계 생성"""
    fighter_match = FighterMatchModel(
        fighter_id=fighter_id,
        match_id=match_id,
        result=result
    )
    session.add(fighter_match)
    await session.flush()
    return fighter_match


async def create_basic_stats(
    session: AsyncSession,
    fighter_match_id: int,
    knockdowns: int = 0,
    control_time_seconds: int = 0,
    sig_str_landed: int = 0,
    sig_str_attempted: int = 0
) -> BasicMatchStatModel:
    """테스트용 기본 통계 생성"""
    stats = BasicMatchStatModel(
        fighter_match_id=fighter_match_id,
        knockdowns=knockdowns,
        control_time_seconds=control_time_seconds,
        submission_attempts=0,
        sig_str_landed=sig_str_landed,
        sig_str_attempted=sig_str_attempted,
        total_str_landed=sig_str_landed + 10,
        total_str_attempted=sig_str_attempted + 15,
        td_landed=2,
        td_attempted=4,
        round=3
    )
    session.add(stats)
    await session.flush()
    return stats


async def create_sig_str_stats(
    session: AsyncSession,
    fighter_match_id: int,
    head_strikes_landed: int = 20,
    head_strikes_attempts: int = 40
) -> SigStrMatchStatModel:
    """테스트용 스트라이크 상세 통계 생성"""
    stats = SigStrMatchStatModel(
        fighter_match_id=fighter_match_id,
        head_strikes_landed=head_strikes_landed,
        head_strikes_attempts=head_strikes_attempts,
        body_strikes_landed=10,
        body_strikes_attempts=20,
        leg_strikes_landed=5,
        leg_strikes_attempts=10,
        takedowns_landed=2,
        takedowns_attempts=4,
        clinch_strikes_landed=3,
        clinch_strikes_attempts=6,
        ground_strikes_landed=5,
        ground_strikes_attempts=8,
        round=3
    )
    session.add(stats)
    await session.flush()
    return stats


# =============================================================================
# get_match_detail 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_match_detail_success(clean_test_session: AsyncSession):
    """매치 상세 정보 조회 성공 테스트"""
    # Given: 매치와 파이터들 생성
    event = await create_test_event(clean_test_session, "Detail Test Event")
    fighter1 = await create_test_fighter(clean_test_session, "Detail Fighter 1")
    fighter2 = await create_test_fighter(clean_test_session, "Detail Fighter 2")
    match = await create_test_match(clean_test_session, event.id, method="KO/TKO", result_round=2)

    fm1 = await create_fighter_match(clean_test_session, fighter1.id, match.id, "win")
    fm2 = await create_fighter_match(clean_test_session, fighter2.id, match.id, "loss")

    await create_basic_stats(clean_test_session, fm1.id, knockdowns=2, sig_str_landed=45)
    await create_basic_stats(clean_test_session, fm2.id, knockdowns=0, sig_str_landed=30)
    await create_sig_str_stats(clean_test_session, fm1.id, head_strikes_landed=25)
    await create_sig_str_stats(clean_test_session, fm2.id, head_strikes_landed=15)

    # When: 매치 상세 정보 조회
    result = await match_service.get_match_detail(clean_test_session, match.id)

    # Then: MatchDetailDTO 반환
    assert isinstance(result, MatchDetailDTO)
    assert result.match.id == match.id
    assert result.match.method == "KO/TKO"
    assert result.match.result_round == 2

    # 파이터 정보 확인
    assert isinstance(result.fighters, list)
    assert len(result.fighters) == 2

    # 통계 정보 확인
    assert result.statistics is not None
    assert result.statistics.match_id == match.id


@pytest.mark.asyncio
async def test_get_match_detail_without_statistics(clean_test_session: AsyncSession):
    """통계 없는 매치 상세 정보 조회 테스트"""
    # Given: 통계 없이 매치와 파이터만 생성
    event = await create_test_event(clean_test_session, "No Stats Event")
    fighter1 = await create_test_fighter(clean_test_session, "No Stats Fighter 1")
    fighter2 = await create_test_fighter(clean_test_session, "No Stats Fighter 2")
    match = await create_test_match(clean_test_session, event.id)

    await create_fighter_match(clean_test_session, fighter1.id, match.id, "win")
    await create_fighter_match(clean_test_session, fighter2.id, match.id, "loss")

    # When: 매치 상세 정보 조회
    result = await match_service.get_match_detail(clean_test_session, match.id)

    # Then: 매치 정보는 있고 통계는 없거나 빈 상태
    assert isinstance(result, MatchDetailDTO)
    assert result.match.id == match.id
    assert len(result.fighters) == 2


@pytest.mark.asyncio
async def test_get_match_detail_nonexistent(clean_test_session: AsyncSession):
    """존재하지 않는 매치 상세 정보 조회 테스트"""
    # When & Then: 존재하지 않는 매치 ID로 조회시 MatchNotFoundError 발생
    with pytest.raises(MatchNotFoundError, match="Match not found with id"):
        await match_service.get_match_detail(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_match_detail_invalid_match_id_negative(clean_test_session: AsyncSession):
    """음수 매치 ID 처리 테스트"""
    # When & Then: 음수 매치 ID로 조회시 MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, -1)


@pytest.mark.asyncio
async def test_get_match_detail_invalid_match_id_zero(clean_test_session: AsyncSession):
    """0 매치 ID 처리 테스트"""
    # When & Then: 0으로 조회시 MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, 0)


@pytest.mark.asyncio
async def test_get_match_detail_invalid_match_id_string(clean_test_session: AsyncSession):
    """문자열 매치 ID 처리 테스트"""
    # When & Then: 문자열로 조회시 MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_detail(clean_test_session, "invalid")


# =============================================================================
# get_match_with_winner_loser 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_match_with_winner_loser_success(clean_test_session: AsyncSession):
    """승자/패자 정보 조회 성공 테스트"""
    # Given: 매치와 승자/패자 생성
    event = await create_test_event(clean_test_session, "Winner Loser Event")
    winner = await create_test_fighter(clean_test_session, "Winner Fighter", wins=15, losses=2)
    loser = await create_test_fighter(clean_test_session, "Loser Fighter", wins=10, losses=5)
    match = await create_test_match(clean_test_session, event.id, method="Submission", result_round=2)

    await create_fighter_match(clean_test_session, winner.id, match.id, "win")
    await create_fighter_match(clean_test_session, loser.id, match.id, "loss")

    # When: 승자/패자 정보 조회
    result = await match_service.get_match_with_winner_loser(clean_test_session, match.id)

    # Then: MatchWithResultDTO 반환
    assert isinstance(result, MatchWithResultDTO)
    assert result.match.id == match.id
    assert result.match.method == "Submission"

    # 승자 확인
    assert result.winner is not None
    assert result.winner.result.lower() == "win"
    assert result.winner.fighter.id == winner.id

    # 패자 확인
    assert result.loser is not None
    assert result.loser.result.lower() == "loss"
    assert result.loser.fighter.id == loser.id


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_draw(clean_test_session: AsyncSession):
    """무승부 매치 조회 테스트"""
    # Given: 무승부 매치 생성
    event = await create_test_event(clean_test_session, "Draw Event")
    fighter1 = await create_test_fighter(clean_test_session, "Draw Fighter 1")
    fighter2 = await create_test_fighter(clean_test_session, "Draw Fighter 2")
    match = await create_test_match(clean_test_session, event.id, method="Draw")

    await create_fighter_match(clean_test_session, fighter1.id, match.id, "draw")
    await create_fighter_match(clean_test_session, fighter2.id, match.id, "draw")

    # When: 승자/패자 정보 조회
    result = await match_service.get_match_with_winner_loser(clean_test_session, match.id)

    # Then: 매치 정보는 있지만 명확한 승자/패자 없음
    assert isinstance(result, MatchWithResultDTO)
    assert result.match.id == match.id
    # 무승부의 경우 winner/loser가 None일 수 있음
    assert len(result.fighters) == 2


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 매치 승부 결과 조회 테스트"""
    # When & Then: MatchNotFoundError 발생
    with pytest.raises(MatchNotFoundError, match="Match not found with id"):
        await match_service.get_match_with_winner_loser(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_invalid_id(clean_test_session: AsyncSession):
    """잘못된 매치 ID로 승부 결과 조회 테스트"""
    # When & Then: MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
        await match_service.get_match_with_winner_loser(clean_test_session, -1)


# =============================================================================
# get_matches_between_fighters 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_matches_between_fighters_success(clean_test_session: AsyncSession):
    """파이터 간 대결 조회 성공 테스트"""
    # Given: 두 파이터 간 여러 매치 생성
    fighter1 = await create_test_fighter(clean_test_session, "Rivalry Fighter 1")
    fighter2 = await create_test_fighter(clean_test_session, "Rivalry Fighter 2")

    event1 = await create_test_event(clean_test_session, "Fight 1")
    event2 = await create_test_event(clean_test_session, "Fight 2")
    event3 = await create_test_event(clean_test_session, "Fight 3")

    match1 = await create_test_match(clean_test_session, event1.id, method="Decision")
    match2 = await create_test_match(clean_test_session, event2.id, method="KO/TKO")
    match3 = await create_test_match(clean_test_session, event3.id, method="Submission")

    # 모든 매치에 두 파이터 연결
    await create_fighter_match(clean_test_session, fighter1.id, match1.id, "win")
    await create_fighter_match(clean_test_session, fighter2.id, match1.id, "loss")
    await create_fighter_match(clean_test_session, fighter1.id, match2.id, "loss")
    await create_fighter_match(clean_test_session, fighter2.id, match2.id, "win")
    await create_fighter_match(clean_test_session, fighter1.id, match3.id, "win")
    await create_fighter_match(clean_test_session, fighter2.id, match3.id, "loss")

    # When: 두 파이터 간 대결 조회
    result = await match_service.get_matches_between_fighters(
        clean_test_session, fighter1.id, fighter2.id
    )

    # Then: 3개의 매치 반환
    assert isinstance(result, list)
    assert len(result) == 3

    # 매치 방법들 확인
    methods = [match.method for match in result]
    assert "Decision" in methods
    assert "KO/TKO" in methods
    assert "Submission" in methods


@pytest.mark.asyncio
async def test_get_matches_between_fighters_no_matches(clean_test_session: AsyncSession):
    """대결 기록이 없는 파이터 간 조회 테스트"""
    # Given: 대결 기록이 없는 두 파이터
    fighter1 = await create_test_fighter(clean_test_session, "No Match Fighter 1")
    fighter2 = await create_test_fighter(clean_test_session, "No Match Fighter 2")

    # When: 대결 조회
    result = await match_service.get_matches_between_fighters(
        clean_test_session, fighter1.id, fighter2.id
    )

    # Then: 빈 리스트 반환
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_matches_between_fighters_invalid_fighter_id_1(clean_test_session: AsyncSession):
    """잘못된 fighter_id_1 처리 테스트"""
    # When & Then: MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="fighter_id_1 must be a positive integer"):
        await match_service.get_matches_between_fighters(clean_test_session, -1, 2)


@pytest.mark.asyncio
async def test_get_matches_between_fighters_invalid_fighter_id_2(clean_test_session: AsyncSession):
    """잘못된 fighter_id_2 처리 테스트"""
    # When & Then: MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="fighter_id_2 must be a positive integer"):
        await match_service.get_matches_between_fighters(clean_test_session, 1, 0)


@pytest.mark.asyncio
async def test_get_matches_between_fighters_same_fighter_id(clean_test_session: AsyncSession):
    """동일한 파이터 ID로 조회 테스트"""
    # When & Then: MatchValidationError 발생
    with pytest.raises(MatchValidationError, match="fighter_id_1 and fighter_id_2 cannot be the same"):
        await match_service.get_matches_between_fighters(clean_test_session, 1, 1)


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_full_match_query_workflow(clean_test_session: AsyncSession):
    """전체 매치 조회 워크플로우 통합 테스트"""
    # 1. 이벤트, 파이터, 매치 생성
    event = await create_test_event(clean_test_session, "Full Workflow Event")
    champion = await create_test_fighter(clean_test_session, "Champion", wins=25, losses=0)
    challenger = await create_test_fighter(clean_test_session, "Challenger", wins=18, losses=3)
    title_fight = await create_test_match(
        clean_test_session, event.id,
        method="TKO", result_round=4, is_main_event=True
    )

    fm_champion = await create_fighter_match(clean_test_session, champion.id, title_fight.id, "win")
    fm_challenger = await create_fighter_match(clean_test_session, challenger.id, title_fight.id, "loss")

    await create_basic_stats(clean_test_session, fm_champion.id, knockdowns=3, sig_str_landed=85)
    await create_basic_stats(clean_test_session, fm_challenger.id, knockdowns=1, sig_str_landed=62)
    await create_sig_str_stats(clean_test_session, fm_champion.id, head_strikes_landed=45)
    await create_sig_str_stats(clean_test_session, fm_challenger.id, head_strikes_landed=30)

    # 2. 매치 상세 정보 조회
    detail = await match_service.get_match_detail(clean_test_session, title_fight.id)
    assert detail.match.is_main_event is True
    assert detail.match.method == "TKO"
    assert len(detail.fighters) == 2

    # 3. 승자/패자 정보 조회
    result = await match_service.get_match_with_winner_loser(clean_test_session, title_fight.id)
    assert result.winner.fighter.id == champion.id
    assert result.loser.fighter.id == challenger.id

    # 4. 두 파이터 간 대결 기록 조회
    matches = await match_service.get_matches_between_fighters(
        clean_test_session, champion.id, challenger.id
    )
    assert len(matches) == 1
    assert matches[0].id == title_fight.id


@pytest.mark.asyncio
async def test_ko_finish_match_detail(clean_test_session: AsyncSession):
    """KO 피니시 매치 상세 정보 테스트"""
    # Given: KO 피니시 매치
    event = await create_test_event(clean_test_session, "KO Event")
    striker = await create_test_fighter(clean_test_session, "Striker")
    opponent = await create_test_fighter(clean_test_session, "KO Victim")
    match = await create_test_match(
        clean_test_session, event.id,
        method="KO/TKO", result_round=1, time="2:35"
    )

    fm_striker = await create_fighter_match(clean_test_session, striker.id, match.id, "win")
    fm_opponent = await create_fighter_match(clean_test_session, opponent.id, match.id, "loss")

    await create_basic_stats(clean_test_session, fm_striker.id, knockdowns=2)
    await create_basic_stats(clean_test_session, fm_opponent.id, knockdowns=0)

    # When: 매치 상세 조회
    detail = await match_service.get_match_detail(clean_test_session, match.id)

    # Then: KO 피니시 정보 확인
    assert detail.match.method == "KO/TKO"
    assert detail.match.result_round == 1
    assert detail.match.time == "2:35"


if __name__ == "__main__":
    print("Match Services 통합 테스트")
    print("실제 테스트 DB를 사용한 서비스 레이어 검증")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/match/test_match_services.py -v")
