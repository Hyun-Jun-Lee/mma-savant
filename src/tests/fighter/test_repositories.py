"""
Fighter Repository Layer 테스트 - Test Database 사용
SPEC.md 가이드라인에 따른 Repository Layer 완전한 통합 테스트
"""
import pytest
from datetime import date, datetime
from typing import List

import database
from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from fighter import repositories as fighter_repo
from common.utils import normalize_name


class TestFighterRepositoryWithTestDB:
    """Test DB를 사용한 Fighter Repository 완전 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_id_existing(self, sample_fighter, clean_test_session):
        """존재하는 파이터 ID로 조회 테스트"""
        # When: Repository 함수 호출 (sample_fighter fixture 사용)
        result = await fighter_repo.get_fighter_by_id(clean_test_session, sample_fighter.id)
        
        # Then: 올바른 FighterSchema 반환
        assert result is not None
        assert isinstance(result, FighterSchema)
        assert result.id == sample_fighter.id
        assert result.name == "Sample Fighter"
        assert result.nickname == "The Sample"
        assert result.wins == 10
        assert result.losses == 2
        assert result.stance == "Orthodox"
        assert result.height == 72.0
        assert result.weight == 185.0
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_id_nonexistent(self, clean_test_session):
        """존재하지 않는 파이터 ID로 조회 테스트"""
        # When: 존재하지 않는 ID로 조회
        result = await fighter_repo.get_fighter_by_id(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_name_with_normalization(self, clean_test_session):
        """이름 정규화를 통한 파이터 검색 테스트"""
        # Given: 특수문자 포함 이름의 파이터
        original_name = "José Aldó Jr."
        normalized_name = normalize_name(original_name)
        
        test_fighter = FighterModel(
            name=normalized_name,
            nickname="Junior",
            wins=28,
            losses=7,
            draws=0
        )
        clean_test_session.add(test_fighter)
        await clean_test_session.flush()
        
        # When: 원본 이름으로 검색
        result = await fighter_repo.get_fighter_by_name(clean_test_session, original_name)
        
        # Then: 정규화를 통해 올바르게 찾아짐
        assert result is not None
        assert result.name == normalized_name
        assert result.nickname == "Junior"
        assert result.wins == 28
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_name_case_insensitive(self, clean_test_session):
        """대소문자 무관한 이름 검색 테스트"""
        # Given: 소문자로 저장된 파이터
        test_fighter = FighterModel(
            name="anderson silva",
            nickname="The Spider", 
            wins=34,
            losses=11,
            draws=0,
            stance="Southpaw"
        )
        clean_test_session.add(test_fighter)
        await clean_test_session.flush()
        
        # When: 다양한 케이스로 검색
        test_cases = ["ANDERSON SILVA", "Anderson Silva", "anderson silva"]
        
        for search_name in test_cases:
            result = await fighter_repo.get_fighter_by_name(clean_test_session, search_name)
            
            # Then: 모든 케이스에서 올바르게 찾아짐
            assert result is not None, f"Failed to find fighter with name: {search_name}"
            assert result.name == "anderson silva"
            assert result.nickname == "The Spider"
    
    @pytest.mark.asyncio
    async def test_get_all_fighter(self, multiple_fighters, clean_test_session):
        """모든 파이터 조회 테스트"""
        # When: 모든 파이터 조회 (multiple_fighters fixture 사용)
        result = await fighter_repo.get_all_fighter(clean_test_session)
        
        # Then: 생성된 파이터들이 모두 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        result_names = [f.name for f in result]
        assert "Fighter Alpha" in result_names
        assert "Fighter Beta" in result_names
        assert "Fighter Gamma" in result_names
        
        # 모든 결과가 FighterSchema 타입인지 확인
        for fighter in result:
            assert isinstance(fighter, FighterSchema)


class TestRankingRepositoryWithTestDB:
    """Test DB를 사용한 랭킹 Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_ranking_by_fighter_id_multiple_rankings(self, fighter_with_rankings, clean_test_session):
        """다중 체급 랭킹을 가진 파이터 테스트"""
        # Given: fighter_with_rankings fixture 사용
        fighter, rankings = fighter_with_rankings
        
        # When: 파이터 ID로 랭킹 조회
        result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, fighter.id)
        
        # Then: 모든 랭킹 정보 반환
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 체급별 랭킹 확인
        weight_class_rankings = {r.weight_class_id: r.ranking for r in result}
        assert weight_class_rankings[4] == 3  # Lightweight
        assert weight_class_rankings[5] == 5  # Welterweight
        
        # 모든 결과가 RankingSchema 타입인지 확인
        for ranking in result:
            assert isinstance(ranking, RankingSchema)
            assert ranking.fighter_id == fighter.id
    
    @pytest.mark.asyncio
    async def test_get_ranking_by_fighter_id_no_rankings(self, clean_test_session):
        """랭킹이 없는 파이터 테스트"""
        # Given: 랭킹이 없는 파이터
        test_fighter = FighterModel(
            name="Unranked Prospect",
            wins=5,
            losses=2,
            draws=0
        )
        clean_test_session.add(test_fighter)
        await clean_test_session.flush()
        
        # When: 파이터 ID로 랭킹 조회
        result = await fighter_repo.get_ranking_by_fighter_id(clean_test_session, test_fighter.id)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0


class TestWeightClassRankingRepositoryWithTestDB:
    """Test DB를 사용한 체급별 랭킹 Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighters_by_weight_class_ranking_ordered(self, weight_class_fighters, clean_test_session):
        """체급별 랭킹 순서 정렬 테스트"""
        # Given: weight_class_fighters fixture 사용
        fighters, rankings = weight_class_fighters
        
        # When: 체급별 랭킹 조회 (Lightweight = 4)
        result = await fighter_repo.get_fighters_by_weight_class_ranking(clean_test_session, 4)
        
        # Then: 랭킹 순서대로 정렬되어 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        # 랭킹 순서 확인
        assert result[0].name == "LW Champion"  # 1위
        assert result[1].name == "LW Contender 1"  # 2위
        assert result[2].name == "LW Contender 2"  # 3위
        
        # 챔피언 벨트 확인
        assert result[0].belt is True
        assert result[1].belt is False
        assert result[2].belt is False


class TestTopFightersByRecordWithTestDB:
    """Test DB를 사용한 기록 기준 상위 파이터 Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_top_fighter_by_record_wins_complete(self, fighters_for_record_test, clean_test_session):
        """승수 기준 상위 파이터 조회 완전 테스트"""
        # When: 승수 기준 상위 3명 조회 (fighters_for_record_test fixture 사용)
        result = await fighter_repo.get_top_fighter_by_record(clean_test_session, "win", limit=3)
        
        # Then: 승수 순으로 정렬되어 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        # 반환 형식 확인
        for idx, item in enumerate(result):
            assert "ranking" in item
            assert "fighter" in item
            assert item["ranking"] == idx + 1
            assert isinstance(item["fighter"], FighterSchema)
        
        # 승수 순서 확인 (High Wins Fighter가 30승으로 1위)
        assert result[0]["fighter"].name == "High Wins Fighter"  # 30승
        assert result[0]["fighter"].wins == 30
        
        # 상위 3명이 올바른 순서인지 확인
        for i in range(len(result) - 1):
            assert result[i]["fighter"].wins >= result[i + 1]["fighter"].wins
    
    @pytest.mark.asyncio
    async def test_get_top_fighter_by_record_with_weight_class_filter(self, clean_test_session):
        """체급 필터링이 포함된 기록 기준 조회 테스트"""
        # Given: 다른 체급의 파이터들
        fighters = [
            FighterModel(name="LW Champion", wins=25, losses=1, draws=0),
            FighterModel(name="LW Contender", wins=22, losses=2, draws=0),
            FighterModel(name="WW Champion", wins=30, losses=0, draws=0)  # 더 높은 승수지만 다른 체급
        ]
        clean_test_session.add_all(fighters)
        await clean_test_session.flush()
        
        # 체급별 랭킹 정보 추가
        rankings = [
            RankingModel(fighter_id=fighters[0].id, weight_class_id=4, ranking=1),  # Lightweight
            RankingModel(fighter_id=fighters[1].id, weight_class_id=4, ranking=2),  # Lightweight
            RankingModel(fighter_id=fighters[2].id, weight_class_id=5, ranking=1)   # Welterweight
        ]
        clean_test_session.add_all(rankings)
        await clean_test_session.flush()
        
        # When: Lightweight (4) 필터링으로 승수 기준 조회
        result = await fighter_repo.get_top_fighter_by_record(clean_test_session, "win", weight_class_id=4, limit=5)
        
        # Then: Lightweight 파이터들만 반환
        assert isinstance(result, list)
        assert len(result) == 2
        
        fighter_names = [item["fighter"].name for item in result]
        assert "LW Champion" in fighter_names
        assert "LW Contender" in fighter_names
        assert "WW Champion" not in fighter_names  # 다른 체급은 제외
        
        # 승수 순서 확인
        assert result[0]["fighter"].wins >= result[1]["fighter"].wins


class TestRepositoryDataIntegrityWithTestDB:
    """Test DB를 사용한 Repository 데이터 무결성 테스트"""
    
    @pytest.mark.asyncio
    async def test_schema_conversion_complete_integrity(self, complete_fighter_data, clean_test_session):
        """완전한 스키마 변환 무결성 테스트"""
        # When: Repository를 통해 조회 (complete_fighter_data fixture 사용)
        result = await fighter_repo.get_fighter_by_id(clean_test_session, complete_fighter_data.id)
        
        # Then: 모든 필드가 정확히 변환됨
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
        assert result.detail_url == "http://example.com/complete-fighter"
        assert result.wins == 30
        assert result.losses == 2
        assert result.draws == 1
        assert result.created_at is not None
        assert result.updated_at is not None
