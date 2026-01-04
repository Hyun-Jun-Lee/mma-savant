"""
Fighter Repository Layer 테스트 - Test Database 사용
"""
import pytest
from datetime import date, datetime
from typing import List

import database
from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from fighter import repositories as fighter_repo
from common.utils import normalize_name


# =============================================================================
# get_fighter_by_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_by_id_existing(sample_fighter, clean_test_session):
    """존재하는 파이터 ID로 조회 테스트"""
    result = await fighter_repo.get_fighter_by_id(clean_test_session, sample_fighter.id)

    assert result is not None
    assert isinstance(result, FighterSchema)
    assert result.id == sample_fighter.id
    assert result.name == "Sample Fighter"
    assert result.nickname == "The Sample"
    assert result.wins == 10
    assert result.losses == 2


@pytest.mark.asyncio
async def test_get_fighter_by_id_nonexistent(clean_test_session):
    """존재하지 않는 파이터 ID로 조회 테스트"""
    result = await fighter_repo.get_fighter_by_id(clean_test_session, 99999)

    assert result is None


# =============================================================================
# get_all_fighter 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_all_fighter(multiple_fighters, clean_test_session):
    """모든 파이터 조회 테스트 (페이지네이션)"""
    result = await fighter_repo.get_all_fighter(clean_test_session, page=1, page_size=10)

    assert isinstance(result, list)
    assert len(result) == 3

    result_names = [f.name for f in result]
    assert "Fighter Alpha" in result_names
    assert "Fighter Beta" in result_names
    assert "Fighter Gamma" in result_names


@pytest.mark.asyncio
async def test_get_all_fighter_pagination(clean_test_session):
    """페이지네이션 테스트"""
    # 5명의 파이터 추가
    fighters = [
        FighterModel(name=f"Fighter {i}", wins=i, losses=0, draws=0)
        for i in range(1, 6)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    # 첫 번째 페이지 (2개씩)
    page1 = await fighter_repo.get_all_fighter(clean_test_session, page=1, page_size=2)
    assert len(page1) == 2

    # 두 번째 페이지
    page2 = await fighter_repo.get_all_fighter(clean_test_session, page=2, page_size=2)
    assert len(page2) == 2

    # 세 번째 페이지
    page3 = await fighter_repo.get_all_fighter(clean_test_session, page=3, page_size=2)
    assert len(page3) == 1

    # 중복 확인
    page1_ids = {f.id for f in page1}
    page2_ids = {f.id for f in page2}
    assert page1_ids.isdisjoint(page2_ids)


# =============================================================================
# get_fighter_by_name_best_record 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_by_name_best_record_finds_best(clean_test_session):
    """동명이인 중 가장 좋은 전적의 파이터 조회"""
    fighters = [
        FighterModel(name="John Smith", wins=5, losses=5, draws=0),
        FighterModel(name="John Smith", wins=20, losses=2, draws=0),
        FighterModel(name="John Smith", wins=10, losses=3, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    result = await fighter_repo.get_fighter_by_name_best_record(clean_test_session, "John Smith")

    assert result is not None
    assert result.wins == 20  # 가장 승수가 많은 파이터


@pytest.mark.asyncio
async def test_get_fighter_by_name_best_record_case_insensitive(clean_test_session):
    """대소문자 무관한 이름 검색"""
    test_fighter = FighterModel(name="anderson silva", nickname="The Spider", wins=34, losses=11, draws=0)
    clean_test_session.add(test_fighter)
    await clean_test_session.flush()

    result = await fighter_repo.get_fighter_by_name_best_record(clean_test_session, "ANDERSON SILVA")

    assert result is not None
    assert result.name == "anderson silva"


@pytest.mark.asyncio
async def test_get_fighter_by_name_best_record_by_nickname(clean_test_session):
    """닉네임으로도 검색 가능"""
    test_fighter = FighterModel(name="Jon Jones", nickname="Bones", wins=26, losses=1, draws=0)
    clean_test_session.add(test_fighter)
    await clean_test_session.flush()

    result = await fighter_repo.get_fighter_by_name_best_record(clean_test_session, "Bones")

    assert result is not None
    assert result.name == "Jon Jones"


@pytest.mark.asyncio
async def test_get_fighter_by_name_best_record_not_found(clean_test_session):
    """파이터를 찾지 못한 경우"""
    result = await fighter_repo.get_fighter_by_name_best_record(clean_test_session, "Nonexistent Fighter")

    assert result is None


# =============================================================================
# get_ranking_by_fighter_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_ranking_by_fighter_id_multiple_rankings(fighter_with_rankings, clean_test_session):
    """다중 체급 랭킹을 가진 파이터 테스트"""
    fighter, rankings = fighter_with_rankings

    result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, fighter.id)

    assert isinstance(result, list)
    assert len(result) == 2

    weight_class_rankings = {r.weight_class_id: r.ranking for r in result}
    assert weight_class_rankings[4] == 3
    assert weight_class_rankings[5] == 5


@pytest.mark.asyncio
async def test_get_ranking_by_fighter_id_no_rankings(clean_test_session):
    """랭킹이 없는 파이터 테스트"""
    test_fighter = FighterModel(name="Unranked Prospect", wins=5, losses=2, draws=0)
    clean_test_session.add(test_fighter)
    await clean_test_session.flush()

    result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, test_fighter.id)

    assert isinstance(result, list)
    assert len(result) == 0


# =============================================================================
# get_fighters_by_weight_class_ranking 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighters_by_weight_class_ranking_ordered(weight_class_fighters, clean_test_session):
    """체급별 랭킹 순서 정렬 테스트"""
    fighters, rankings = weight_class_fighters

    result = await fighter_repo.get_fighters_by_weight_class_ranking(clean_test_session, 4)

    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0].name == "LW Champion"
    assert result[1].name == "LW Contender 1"
    assert result[2].name == "LW Contender 2"


# =============================================================================
# get_top_fighter_by_record 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_top_fighter_by_record_wins(fighters_for_record_test, clean_test_session):
    """승수 기준 상위 파이터 조회"""
    result = await fighter_repo.get_top_fighter_by_record(clean_test_session, "win", limit=3)

    assert isinstance(result, list)
    assert len(result) == 3

    for idx, item in enumerate(result):
        assert "ranking" in item
        assert "fighter" in item
        assert item["ranking"] == idx + 1
        assert isinstance(item["fighter"], FighterSchema)

    assert result[0]["fighter"].name == "High Wins Fighter"
    assert result[0]["fighter"].wins == 30


@pytest.mark.asyncio
async def test_get_top_fighter_by_record_with_weight_class_filter(clean_test_session):
    """체급 필터링이 포함된 기록 기준 조회"""
    fighters = [
        FighterModel(name="LW Champion", wins=25, losses=1, draws=0),
        FighterModel(name="LW Contender", wins=22, losses=2, draws=0),
        FighterModel(name="WW Champion", wins=30, losses=0, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    rankings = [
        RankingModel(fighter_id=fighters[0].id, weight_class_id=4, ranking=1),
        RankingModel(fighter_id=fighters[1].id, weight_class_id=4, ranking=2),
        RankingModel(fighter_id=fighters[2].id, weight_class_id=5, ranking=1)
    ]
    clean_test_session.add_all(rankings)
    await clean_test_session.flush()

    result = await fighter_repo.get_top_fighter_by_record(clean_test_session, "win", weight_class_id=4, limit=5)

    assert isinstance(result, list)
    assert len(result) == 2

    fighter_names = [item["fighter"].name for item in result]
    assert "LW Champion" in fighter_names
    assert "LW Contender" in fighter_names
    assert "WW Champion" not in fighter_names


# =============================================================================
# search_fighters_by_name 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_search_fighters_by_name(clean_test_session):
    """이름으로 파이터 검색"""
    fighters = [
        FighterModel(name="Jon Jones", nickname="Bones", wins=26, losses=1, draws=0),
        FighterModel(name="Jon Fitch", nickname="", wins=32, losses=8, draws=1),
        FighterModel(name="Daniel Cormier", nickname="DC", wins=22, losses=3, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    result = await fighter_repo.search_fighters_by_name(clean_test_session, "Jon", limit=10)

    assert isinstance(result, list)
    assert len(result) == 2

    result_names = [f.name for f in result]
    assert "Jon Jones" in result_names
    assert "Jon Fitch" in result_names
    assert "Daniel Cormier" not in result_names


@pytest.mark.asyncio
async def test_search_fighters_by_nickname(clean_test_session):
    """닉네임으로 파이터 검색"""
    fighters = [
        FighterModel(name="Jon Jones", nickname="Bones", wins=26, losses=1, draws=0),
        FighterModel(name="Daniel Cormier", nickname="DC", wins=22, losses=3, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    result = await fighter_repo.search_fighters_by_name(clean_test_session, "Bones", limit=10)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].name == "Jon Jones"


# =============================================================================
# get_champions 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_champions(clean_test_session):
    """챔피언 조회"""
    fighters = [
        FighterModel(name="Champion 1", belt=True, wins=20, losses=0, draws=0),
        FighterModel(name="Champion 2", belt=True, wins=18, losses=1, draws=0),
        FighterModel(name="Contender", belt=False, wins=15, losses=2, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    result = await fighter_repo.get_champions(clean_test_session)

    assert isinstance(result, list)
    assert len(result) == 2

    result_names = [f.name for f in result]
    assert "Champion 1" in result_names
    assert "Champion 2" in result_names
    assert "Contender" not in result_names


# =============================================================================
# get_ranked_fighters_by_weight_class 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_ranked_fighters_by_weight_class(clean_test_session):
    """체급별 랭킹된 파이터 조회"""
    fighters = [
        FighterModel(name="Fighter 1", wins=20, losses=1, draws=0),
        FighterModel(name="Fighter 2", wins=18, losses=2, draws=0),
        FighterModel(name="Fighter 3", wins=15, losses=3, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()

    rankings = [
        RankingModel(fighter_id=fighters[0].id, weight_class_id=4, ranking=1),
        RankingModel(fighter_id=fighters[1].id, weight_class_id=4, ranking=2),
        RankingModel(fighter_id=fighters[2].id, weight_class_id=4, ranking=3)
    ]
    clean_test_session.add_all(rankings)
    await clean_test_session.flush()

    result = await fighter_repo.get_ranked_fighters_by_weight_class(clean_test_session, 4, limit=10)

    assert isinstance(result, list)
    assert len(result) == 3

    assert result[0]["ranking"] == 1
    assert result[0]["fighter"].name == "Fighter 1"
    assert result[1]["ranking"] == 2
    assert result[2]["ranking"] == 3


# =============================================================================
# delete_all_rankings 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_delete_all_rankings(clean_test_session):
    """모든 랭킹 삭제"""
    fighter = FighterModel(name="Test Fighter", wins=10, losses=2, draws=0)
    clean_test_session.add(fighter)
    await clean_test_session.flush()

    rankings = [
        RankingModel(fighter_id=fighter.id, weight_class_id=4, ranking=1),
        RankingModel(fighter_id=fighter.id, weight_class_id=5, ranking=2)
    ]
    clean_test_session.add_all(rankings)
    await clean_test_session.flush()

    # 삭제 전 확인
    before_result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, fighter.id)
    assert len(before_result) == 2

    # 삭제 실행
    await fighter_repo.delete_all_rankings(clean_test_session)

    # 삭제 후 확인
    after_result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, fighter.id)
    assert len(after_result) == 0


# =============================================================================
# 데이터 무결성 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_schema_conversion_complete_integrity(complete_fighter_data, clean_test_session):
    """완전한 스키마 변환 무결성 테스트"""
    result = await fighter_repo.get_fighter_by_id(clean_test_session, complete_fighter_data.id)

    assert result is not None
    assert result.name == "Complete Fighter"
    assert result.nickname == "The Complete"
    assert result.height == 74.0
    assert result.height_cm == 188.0
    assert result.weight == 205.0
    assert result.weight_kg == 93.0
    assert result.reach == 80.0
    assert result.reach_cm == 203.0
    assert result.stance == "Southpaw"
    assert result.belt is True
    assert result.wins == 30
    assert result.losses == 2
    assert result.draws == 1
