"""
Fighter Services 통합 테스트
실제 테스트 DB를 사용한 서비스 레이어 검증
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from fighter.dto import FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO
from fighter import services as fighter_services
from fighter.exceptions import (
    FighterNotFoundError, FighterValidationError, FighterQueryError,
    FighterWeightClassError, FighterSearchError
)


# =============================================================================
# 헬퍼 함수: 테스트용 파이터/랭킹 생성
# =============================================================================

async def create_test_fighter(
    session: AsyncSession,
    name: str,
    nickname: str = None,
    wins: int = 10,
    losses: int = 2,
    draws: int = 0,
    belt: bool = False,
    stance: str = "Orthodox"
) -> FighterModel:
    """테스트용 파이터 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    fighter = FighterModel(
        name=f"{name}_{timestamp}",
        nickname=nickname,
        wins=wins,
        losses=losses,
        draws=draws,
        belt=belt,
        stance=stance
    )
    session.add(fighter)
    await session.flush()
    return fighter


async def create_test_ranking(
    session: AsyncSession,
    fighter_id: int,
    weight_class_id: int,
    ranking: int
) -> RankingModel:
    """테스트용 랭킹 생성"""
    ranking_model = RankingModel(
        fighter_id=fighter_id,
        weight_class_id=weight_class_id,
        ranking=ranking
    )
    session.add(ranking_model)
    await session.flush()
    return ranking_model


# =============================================================================
# get_fighter_by_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_by_id_success(clean_test_session: AsyncSession):
    """정상적으로 파이터를 찾은 경우"""
    # Given: 테스트 파이터 생성
    fighter = await create_test_fighter(
        clean_test_session,
        name="Jon Jones",
        nickname="Bones",
        wins=26,
        losses=1,
        draws=0
    )

    # 랭킹 추가 (Lightweight=4, Welterweight=5)
    await create_test_ranking(clean_test_session, fighter.id, 4, 1)
    await create_test_ranking(clean_test_session, fighter.id, 5, 3)

    # When: 서비스 호출
    result = await fighter_services.get_fighter_by_id(clean_test_session, fighter.id)

    # Then: FighterWithRankingsDTO 반환
    assert isinstance(result, FighterWithRankingsDTO)
    assert result.fighter.id == fighter.id
    assert "Jones" in result.fighter.name
    assert result.fighter.wins == 26
    assert result.fighter.losses == 1
    assert len(result.rankings) == 2


@pytest.mark.asyncio
async def test_get_fighter_by_id_not_found(clean_test_session: AsyncSession):
    """파이터를 찾지 못한 경우 예외 발생"""
    # When & Then: 존재하지 않는 ID로 조회 시 예외
    with pytest.raises(FighterNotFoundError) as exc_info:
        await fighter_services.get_fighter_by_id(clean_test_session, 99999)

    assert "Fighter not found with id: 99999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_fighter_by_id_no_rankings(clean_test_session: AsyncSession):
    """랭킹이 없는 파이터의 경우"""
    # Given: 랭킹 없는 파이터 생성
    fighter = await create_test_fighter(
        clean_test_session,
        name="Unknown Fighter",
        wins=5,
        losses=2,
        draws=0
    )

    # When: 서비스 호출
    result = await fighter_services.get_fighter_by_id(clean_test_session, fighter.id)

    # Then: 빈 랭킹
    assert isinstance(result, FighterWithRankingsDTO)
    assert result.rankings == {}


@pytest.mark.asyncio
async def test_get_fighter_by_id_invalid_id(clean_test_session: AsyncSession):
    """잘못된 fighter ID 처리 테스트"""
    # When & Then: 음수 ID
    with pytest.raises(FighterValidationError, match="fighter_id must be a positive integer"):
        await fighter_services.get_fighter_by_id(clean_test_session, -1)

    # When & Then: 0 ID
    with pytest.raises(FighterValidationError, match="fighter_id must be a positive integer"):
        await fighter_services.get_fighter_by_id(clean_test_session, 0)


# =============================================================================
# get_fighter_ranking_by_weight_class 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_ranking_by_weight_class_success(clean_test_session: AsyncSession):
    """정상적으로 체급별 랭킹을 조회한 경우"""
    # Given: Lightweight(4) 체급에 파이터 3명 생성
    fighter1 = await create_test_fighter(clean_test_session, "LW Fighter 1", wins=20, losses=1)
    fighter2 = await create_test_fighter(clean_test_session, "LW Fighter 2", wins=18, losses=2)
    fighter3 = await create_test_fighter(clean_test_session, "LW Fighter 3", wins=15, losses=3)

    await create_test_ranking(clean_test_session, fighter1.id, 4, 1)
    await create_test_ranking(clean_test_session, fighter2.id, 4, 2)
    await create_test_ranking(clean_test_session, fighter3.id, 4, 3)

    # When: 서비스 호출
    result = await fighter_services.get_fighter_ranking_by_weight_class(
        clean_test_session, "Lightweight"
    )

    # Then: WeightClassRankingsDTO 반환
    assert isinstance(result, WeightClassRankingsDTO)
    assert result.weight_class_name == "Lightweight"
    assert len(result.rankings) == 3

    # 랭킹 순서 확인
    assert result.rankings[0].ranking == 1
    assert result.rankings[1].ranking == 2
    assert result.rankings[2].ranking == 3


@pytest.mark.asyncio
async def test_get_fighter_ranking_by_weight_class_invalid_weight_class(clean_test_session: AsyncSession):
    """잘못된 체급명인 경우 예외 발생"""
    # When & Then
    with pytest.raises(FighterWeightClassError):
        await fighter_services.get_fighter_ranking_by_weight_class(
            clean_test_session, "Invalid Weight Class"
        )


@pytest.mark.asyncio
async def test_get_fighter_ranking_by_weight_class_empty_name(clean_test_session: AsyncSession):
    """빈 체급 이름 처리 테스트"""
    # When & Then
    with pytest.raises(FighterValidationError, match="Weight class name cannot be empty"):
        await fighter_services.get_fighter_ranking_by_weight_class(clean_test_session, "")


@pytest.mark.asyncio
async def test_get_fighter_ranking_by_weight_class_empty_rankings(clean_test_session: AsyncSession):
    """해당 체급에 랭킹된 파이터가 없는 경우"""
    # Given: Featherweight(3)에는 랭킹 없음
    # When: 서비스 호출
    result = await fighter_services.get_fighter_ranking_by_weight_class(
        clean_test_session, "Featherweight"
    )

    # Then: 빈 랭킹 리스트
    assert isinstance(result, WeightClassRankingsDTO)
    assert result.weight_class_name == "Featherweight"
    assert len(result.rankings) == 0


# =============================================================================
# get_top_fighters_by_record 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_top_fighters_by_record_by_wins(clean_test_session: AsyncSession):
    """승수 기준 상위 파이터들을 조회한 경우"""
    # Given: 다양한 승수의 파이터 생성
    await create_test_fighter(clean_test_session, "Low Wins", wins=5, losses=0)
    await create_test_fighter(clean_test_session, "Mid Wins", wins=15, losses=2)
    await create_test_fighter(clean_test_session, "High Wins", wins=30, losses=1)

    # When: 승수 기준 top 3 조회
    result = await fighter_services.get_top_fighters_by_record(
        clean_test_session, "win", weight_class_id=None, limit=3
    )

    # Then: WeightClassRankingsDTO 반환
    assert isinstance(result, WeightClassRankingsDTO)
    assert result.weight_class_name is None  # 전체 조회
    assert len(result.rankings) >= 1

    # 승수 내림차순 정렬 확인
    if len(result.rankings) >= 2:
        assert result.rankings[0].fighter.wins >= result.rankings[1].fighter.wins


@pytest.mark.asyncio
async def test_get_top_fighters_by_record_with_weight_class_filter(clean_test_session: AsyncSession):
    """체급 필터링이 포함된 기록 기준 조회"""
    # Given: 두 체급에 파이터 생성
    lw_fighter = await create_test_fighter(clean_test_session, "LW Top", wins=25, losses=1)
    ww_fighter = await create_test_fighter(clean_test_session, "WW Top", wins=30, losses=0)

    await create_test_ranking(clean_test_session, lw_fighter.id, 4, 1)  # Lightweight
    await create_test_ranking(clean_test_session, ww_fighter.id, 5, 1)  # Welterweight

    # When: Lightweight만 조회
    result = await fighter_services.get_top_fighters_by_record(
        clean_test_session, "win", weight_class_id=4, limit=5
    )

    # Then: Lightweight 파이터만 포함
    assert isinstance(result, WeightClassRankingsDTO)
    assert result.weight_class_name == "lightweight"

    # WW 파이터는 포함되지 않아야 함
    fighter_names = [r.fighter.name for r in result.rankings]
    assert not any("WW Top" in name for name in fighter_names)


@pytest.mark.asyncio
async def test_get_top_fighters_by_record_invalid_record(clean_test_session: AsyncSession):
    """잘못된 record 값 처리 테스트"""
    # When & Then
    with pytest.raises(FighterValidationError, match="record must be 'win', 'loss', or 'draw'"):
        await fighter_services.get_top_fighters_by_record(clean_test_session, "invalid")


@pytest.mark.asyncio
async def test_get_top_fighters_by_record_invalid_limit(clean_test_session: AsyncSession):
    """잘못된 limit 값 처리 테스트"""
    # When & Then
    with pytest.raises(FighterValidationError, match="limit must be a positive integer"):
        await fighter_services.get_top_fighters_by_record(clean_test_session, "win", limit=0)


# =============================================================================
# search_fighters 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_search_fighters_by_name(clean_test_session: AsyncSession):
    """이름으로 파이터를 검색한 경우"""
    # Given: 파이터들 생성
    await create_test_fighter(clean_test_session, "Jon Jones", nickname="Bones", wins=26)
    await create_test_fighter(clean_test_session, "Jon Fitch", wins=32)
    await create_test_fighter(clean_test_session, "Daniel Cormier", nickname="DC", wins=22)

    # When: "Jon" 검색
    result = await fighter_services.search_fighters(clean_test_session, "Jon", limit=10)

    # Then: Jon이 포함된 파이터만
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(r, FighterWithRankingsDTO) for r in result)

    result_names = [r.fighter.name for r in result]
    assert any("Jon Jones" in name for name in result_names)
    assert any("Jon Fitch" in name for name in result_names)
    assert not any("Daniel" in name for name in result_names)


@pytest.mark.asyncio
async def test_search_fighters_by_nickname(clean_test_session: AsyncSession):
    """닉네임으로 파이터를 검색한 경우"""
    # Given: 닉네임이 있는 파이터 생성
    await create_test_fighter(clean_test_session, "Jon Jones", nickname="Bones", wins=26)

    # When: 닉네임으로 검색
    result = await fighter_services.search_fighters(clean_test_session, "Bones", limit=10)

    # Then: 닉네임 매칭
    assert len(result) >= 1
    assert any("Jones" in r.fighter.name for r in result)


@pytest.mark.asyncio
async def test_search_fighters_empty_search_term(clean_test_session: AsyncSession):
    """빈 검색어 처리 테스트"""
    # When & Then
    with pytest.raises(FighterValidationError, match="Search term cannot be empty"):
        await fighter_services.search_fighters(clean_test_session, "")


@pytest.mark.asyncio
async def test_search_fighters_invalid_limit(clean_test_session: AsyncSession):
    """잘못된 limit 값 처리 테스트"""
    # When & Then
    with pytest.raises(FighterValidationError, match="limit must be a positive integer"):
        await fighter_services.search_fighters(clean_test_session, "Jon", limit=0)


@pytest.mark.asyncio
async def test_search_fighters_no_results(clean_test_session: AsyncSession):
    """검색 결과가 없는 경우"""
    # When: 존재하지 않는 이름 검색
    result = await fighter_services.search_fighters(
        clean_test_session, "NonExistentFighterXYZ123", limit=10
    )

    # Then: 빈 리스트
    assert isinstance(result, list)
    assert len(result) == 0


# =============================================================================
# get_all_champions 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_all_champions_success(clean_test_session: AsyncSession):
    """정상적으로 챔피언들을 조회한 경우"""
    # Given: 챔피언과 일반 파이터 생성
    await create_test_fighter(clean_test_session, "Champion 1", wins=20, belt=True)
    await create_test_fighter(clean_test_session, "Champion 2", wins=18, belt=True)
    await create_test_fighter(clean_test_session, "Contender", wins=15, belt=False)

    # When: 챔피언 조회
    result = await fighter_services.get_all_champions(clean_test_session)

    # Then: 챔피언만 포함
    assert isinstance(result, list)
    assert len(result) >= 2
    assert all(isinstance(c, FighterWithRankingsDTO) for c in result)

    # 모든 결과가 belt=True
    for champion in result:
        assert champion.fighter.belt is True


@pytest.mark.asyncio
async def test_get_all_champions_no_champions(clean_test_session: AsyncSession):
    """챔피언이 없는 경우"""
    # Given: 일반 파이터만 생성
    await create_test_fighter(clean_test_session, "Contender 1", wins=15, belt=False)
    await create_test_fighter(clean_test_session, "Contender 2", wins=12, belt=False)

    # When: 챔피언 조회
    result = await fighter_services.get_all_champions(clean_test_session)

    # Then: 빈 리스트 (이 테스트 이전 챔피언이 없다고 가정할 수 없으므로 타입만 확인)
    assert isinstance(result, list)


# =============================================================================
# _build_fighter_with_rankings 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_build_fighter_with_rankings_multiple_weight_classes(clean_test_session: AsyncSession):
    """여러 체급에서 랭킹을 가진 파이터"""
    # Given: 두 체급에 랭킹된 파이터
    fighter = await create_test_fighter(
        clean_test_session, "Multi-Division Champion", wins=20
    )
    await create_test_ranking(clean_test_session, fighter.id, 4, 1)  # Lightweight
    await create_test_ranking(clean_test_session, fighter.id, 5, 1)  # Welterweight

    # 파이터 스키마 조회
    from fighter import repositories as fighter_repo
    fighter_schema = await fighter_repo.get_fighter_by_id(clean_test_session, fighter.id)

    # When: _build_fighter_with_rankings 호출
    result = await fighter_services._build_fighter_with_rankings(
        clean_test_session, fighter_schema
    )

    # Then: 두 체급 랭킹 포함
    assert isinstance(result, FighterWithRankingsDTO)
    assert len(result.rankings) == 2
    assert "lightweight" in result.rankings
    assert "welterweight" in result.rankings


@pytest.mark.asyncio
async def test_build_fighter_with_rankings_no_rankings(clean_test_session: AsyncSession):
    """랭킹이 없는 파이터"""
    # Given: 랭킹 없는 파이터
    fighter = await create_test_fighter(clean_test_session, "Unranked Fighter", wins=5)

    from fighter import repositories as fighter_repo
    fighter_schema = await fighter_repo.get_fighter_by_id(clean_test_session, fighter.id)

    # When: _build_fighter_with_rankings 호출
    result = await fighter_services._build_fighter_with_rankings(
        clean_test_session, fighter_schema
    )

    # Then: 빈 랭킹
    assert isinstance(result, FighterWithRankingsDTO)
    assert result.rankings == {}


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_full_fighter_workflow(clean_test_session: AsyncSession):
    """전체 파이터 워크플로우 통합 테스트"""
    # 1. 챔피언 파이터 생성
    champion = await create_test_fighter(
        clean_test_session,
        name="Integration Test Champion",
        nickname="The Integrator",
        wins=25,
        losses=0,
        belt=True
    )

    # 2. 랭킹 추가
    await create_test_ranking(clean_test_session, champion.id, 4, 1)  # Lightweight

    # 3. ID로 조회
    fighter_result = await fighter_services.get_fighter_by_id(
        clean_test_session, champion.id
    )
    assert fighter_result.fighter.belt is True
    assert "lightweight" in fighter_result.rankings
    assert fighter_result.rankings["lightweight"] == 1

    # 4. 체급별 랭킹 조회
    ranking_result = await fighter_services.get_fighter_ranking_by_weight_class(
        clean_test_session, "Lightweight"
    )
    assert len(ranking_result.rankings) >= 1

    # 5. 이름으로 검색
    search_result = await fighter_services.search_fighters(
        clean_test_session, "Integration Test", limit=10
    )
    assert len(search_result) >= 1

    # 6. 챔피언 목록 조회
    champions = await fighter_services.get_all_champions(clean_test_session)
    champion_ids = [c.fighter.id for c in champions]
    assert champion.id in champion_ids


@pytest.mark.asyncio
async def test_top_fighters_by_different_records(clean_test_session: AsyncSession):
    """다양한 기록 기준으로 상위 파이터 조회"""
    # Given: 다양한 기록의 파이터들
    await create_test_fighter(clean_test_session, "High Win", wins=30, losses=1, draws=0)
    await create_test_fighter(clean_test_session, "High Loss", wins=10, losses=15, draws=0)
    await create_test_fighter(clean_test_session, "High Draw", wins=15, losses=10, draws=5)

    # When: 각 기준으로 조회
    win_result = await fighter_services.get_top_fighters_by_record(
        clean_test_session, "win", limit=5
    )
    loss_result = await fighter_services.get_top_fighters_by_record(
        clean_test_session, "loss", limit=5
    )
    draw_result = await fighter_services.get_top_fighters_by_record(
        clean_test_session, "draw", limit=5
    )

    # Then: 각 결과가 올바른 타입
    assert isinstance(win_result, WeightClassRankingsDTO)
    assert isinstance(loss_result, WeightClassRankingsDTO)
    assert isinstance(draw_result, WeightClassRankingsDTO)


if __name__ == "__main__":
    print("Fighter Services 통합 테스트")
    print("실제 테스트 DB를 사용한 서비스 레이어 검증")
    print("\n테스트 실행:")
    print("uv run pytest tests/fighter/test_fighter_services.py -v")
