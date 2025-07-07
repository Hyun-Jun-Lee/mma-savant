
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime

import database

from fighter.models import FighterSchema, RankingSchema
from fighter.dto import (
    FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO,
    FightersByStanceDTO, UndefeatedFightersDTO, FightersByPhysicalAttributesDTO,
    FightersPerformanceAnalysisDTO, WeightClassDepthAnalysisDTO
)
from fighter import services as fighter_services
from fighter import exceptions as fighter_exc


class TestGetFighterById:
    """get_fighter_by_id 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_id_success(self):
        """정상적으로 파이터를 찾은 경우"""
        # Given: 모킹된 세션과 파이터 데이터
        mock_session = AsyncMock()
        fighter_data = FighterSchema(
            id=1,
            name="Jon Jones",
            nickname="Bones",
            wins=26,
            losses=1,
            draws=0
        )
        ranking_data = [
            RankingSchema(id=1, fighter_id=1, weight_class_id=1, ranking=1),
            RankingSchema(id=2, fighter_id=1, weight_class_id=2, ranking=3)
        ]
        
        # Mock repository functions
        with patch('fighter.repositories.get_fighter_by_id', return_value=fighter_data) as mock_get_fighter, \
             patch('fighter.repositories.get_ranking_by_fighter_id', return_value=ranking_data) as mock_get_ranking, \
             patch('common.models.WeightClassSchema.get_name_by_id', side_effect=lambda x: f"WeightClass_{x}"):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_by_id(mock_session, 1)
            
            # Then: 올바른 DTO가 반환되고 repository 함수들이 호출됨
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.fighter.id == 1
            assert result.fighter.name == "Jon Jones"
            assert result.fighter.nickname == "Bones"
            assert len(result.rankings) == 2
            assert result.rankings["WeightClass_1"] == 1
            assert result.rankings["WeightClass_2"] == 3
            
            mock_get_fighter.assert_called_once_with(mock_session, 1)
            mock_get_ranking.assert_called_once_with(mock_session, 1)
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_id_not_found(self):
        """파이터를 찾지 못한 경우 예외 발생"""
        # Given: 모킹된 세션과 None 반환
        mock_session = AsyncMock()
        
        with patch('fighter.repositories.get_fighter_by_id', return_value=None):
            # When & Then: FighterNotFoundError 예외 발생 확인
            with pytest.raises(fighter_exc.FighterNotFoundError) as exc_info:
                await fighter_services.get_fighter_by_id(mock_session, 999)
            
            assert "Fighter not found: 999" in str(exc_info.value)
            assert exc_info.value.fighter_identifier == "999"
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_id_no_rankings(self):
        """랭킹이 없는 파이터의 경우"""
        # Given: 랭킹이 없는 파이터
        mock_session = AsyncMock()
        fighter_data = FighterSchema(
            id=2,
            name="Unknown Fighter",
            wins=5,
            losses=2,
            draws=0
        )
        
        with patch('fighter.repositories.get_fighter_by_id', return_value=fighter_data), \
             patch('fighter.repositories.get_ranking_by_fighter_id', return_value=[]):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_by_id(mock_session, 2)
            
            # Then: 빈 랭킹 딕셔너리와 함께 DTO 반환
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.fighter.id == 2
            assert result.rankings == {}


class TestGetFighterByName:
    """get_fighter_by_name 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_name_success(self):
        """정상적으로 이름으로 파이터를 찾은 경우"""
        # Given: 모킹된 데이터
        mock_session = AsyncMock()
        fighter_data = FighterSchema(
            id=3,
            name="Amanda Nunes",
            nickname="The Lioness",
            wins=22,
            losses=5,
            draws=0
        )
        ranking_data = [RankingSchema(id=3, fighter_id=3, weight_class_id=3, ranking=1)]
        
        with patch('fighter.repositories.get_fighter_by_name', return_value=fighter_data), \
             patch('fighter.repositories.get_ranking_by_fighter_id', return_value=ranking_data), \
             patch('common.models.WeightClassSchema.get_name_by_id', return_value="Bantamweight"):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_by_name(mock_session, "Amanda Nunes")
            
            # Then: 올바른 DTO 반환
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.fighter.name == "Amanda Nunes"
            assert result.rankings["Bantamweight"] == 1
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_name_not_found(self):
        """이름으로 파이터를 찾지 못한 경우"""
        # Given: None 반환
        mock_session = AsyncMock()
        
        with patch('fighter.repositories.get_fighter_by_name', return_value=None):
            # When & Then: 예외 발생 확인
            with pytest.raises(fighter_exc.FighterNotFoundError) as exc_info:
                await fighter_services.get_fighter_by_name(mock_session, "Nonexistent Fighter")
            
            assert "Fighter not found: Nonexistent Fighter" in str(exc_info.value)


class TestGetFighterByNickname:
    """get_fighter_by_nickname 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_nickname_success(self):
        """정상적으로 닉네임으로 파이터를 찾은 경우"""
        # Given: 모킹된 데이터
        mock_session = AsyncMock()
        fighter_data = FighterSchema(
            id=4,
            name="Conor McGregor",
            nickname="The Notorious",
            wins=22,
            losses=6,
            draws=0
        )
        
        with patch('fighter.repositories.get_fighter_by_nickname', return_value=fighter_data), \
             patch('fighter.repositories.get_ranking_by_fighter_id', return_value=[]):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_by_nickname(mock_session, "The Notorious")
            
            # Then: 올바른 DTO 반환
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.fighter.nickname == "The Notorious"
    
    @pytest.mark.asyncio
    async def test_get_fighter_by_nickname_not_found(self):
        """닉네임으로 파이터를 찾지 못한 경우"""
        # Given: None 반환
        mock_session = AsyncMock()
        
        with patch('fighter.repositories.get_fighter_by_nickname', return_value=None):
            # When & Then: 예외 발생 확인
            with pytest.raises(fighter_exc.FighterNotFoundError) as exc_info:
                await fighter_services.get_fighter_by_nickname(mock_session, "Unknown Nickname")
            
            assert "Fighter not found: Unknown Nickname" in str(exc_info.value)


class TestGetFighterRankingByWeightClass:
    """get_fighter_ranking_by_weight_class 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_ranking_by_weight_class_success(self):
        """정상적으로 체급별 랭킹을 조회한 경우"""
        # Given: 모킹된 데이터
        mock_session = AsyncMock()
        fighters_data = [
            FighterSchema(id=1, name="Fighter 1", wins=20, losses=1, draws=0),
            FighterSchema(id=2, name="Fighter 2", wins=18, losses=2, draws=0),
            FighterSchema(id=3, name="Fighter 3", wins=15, losses=3, draws=0)
        ]
        
        with patch('common.models.WeightClassSchema.get_id_by_name', return_value=5), \
             patch('fighter.repositories.get_fighters_by_weight_class_ranking', return_value=fighters_data):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_ranking_by_weight_class(mock_session, "Lightweight")
            
            # Then: 올바른 WeightClassRankingsDTO 반환
            assert isinstance(result, WeightClassRankingsDTO)
            assert result.weight_class_name == "Lightweight"
            assert len(result.rankings) == 3
            
            # 랭킹 순서 확인
            assert result.rankings[0].ranking == 1
            assert result.rankings[0].fighter.name == "Fighter 1"
            assert result.rankings[1].ranking == 2
            assert result.rankings[1].fighter.name == "Fighter 2"
            assert result.rankings[2].ranking == 3
            assert result.rankings[2].fighter.name == "Fighter 3"
    
    @pytest.mark.asyncio
    async def test_get_fighter_ranking_by_weight_class_invalid_weight_class(self):
        """잘못된 체급명인 경우 예외 발생"""
        # Given: 잘못된 체급명
        mock_session = AsyncMock()
        
        with patch('common.models.WeightClassSchema.get_id_by_name', return_value=None):
            # When & Then: InvalidWeightClassError 예외 발생 확인
            with pytest.raises(fighter_exc.InvalidWeightClassError) as exc_info:
                await fighter_services.get_fighter_ranking_by_weight_class(mock_session, "Invalid Weight Class")
            
            assert "Invalid weight class: Invalid Weight Class" in str(exc_info.value)
            assert exc_info.value.weight_class_name == "Invalid Weight Class"
    
    @pytest.mark.asyncio
    async def test_get_fighter_ranking_by_weight_class_empty_result(self):
        """해당 체급에 파이터가 없는 경우"""
        # Given: 빈 결과
        mock_session = AsyncMock()
        
        with patch('common.models.WeightClassSchema.get_id_by_name', return_value=7), \
             patch('fighter.repositories.get_fighters_by_weight_class_ranking', return_value=[]):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_fighter_ranking_by_weight_class(mock_session, "Heavyweight")
            
            # Then: 빈 랭킹 리스트와 함께 DTO 반환
            assert isinstance(result, WeightClassRankingsDTO)
            assert result.weight_class_name == "Heavyweight"
            assert len(result.rankings) == 0


class TestGetTopFightersByRecord:
    """get_top_fighters_by_record 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_top_fighters_by_record_success(self):
        """정상적으로 기록 기준 상위 파이터들을 조회한 경우"""
        # Given: 모킹된 데이터
        mock_session = AsyncMock()
        fighter_with_rank_data = [
            {
                "ranking": 1,
                "fighter": FighterSchema(id=1, name="Fighter 1", wins=25, losses=0, draws=0)
            },
            {
                "ranking": 2,
                "fighter": FighterSchema(id=2, name="Fighter 2", wins=23, losses=1, draws=0)
            }
        ]
        
        with patch('fighter.repositories.get_top_fighter_by_record', return_value=fighter_with_rank_data), \
             patch('common.models.WeightClassSchema.get_name_by_id', return_value="Welterweight"):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_top_fighters_by_record(
                mock_session, "win", weight_class_id=3, limit=5
            )
            
            # Then: 올바른 WeightClassRankingsDTO 반환
            assert isinstance(result, WeightClassRankingsDTO)
            assert result.weight_class_name == "Welterweight"
            assert len(result.rankings) == 2
            assert result.rankings[0].ranking == 1
            assert result.rankings[0].fighter.name == "Fighter 1"
    
    @pytest.mark.asyncio
    async def test_get_top_fighters_by_record_no_weight_class(self):
        """체급 지정 없이 전체 파이터 조회"""
        # Given: weight_class_id가 None인 경우
        mock_session = AsyncMock()
        fighter_with_rank_data = [
            {
                "ranking": 1,
                "fighter": FighterSchema(id=1, name="Global Fighter 1", wins=30, losses=0, draws=0)
            }
        ]
        
        with patch('fighter.repositories.get_top_fighter_by_record', return_value=fighter_with_rank_data):
            
            # When: 서비스 함수 호출
            result = await fighter_services.get_top_fighters_by_record(
                mock_session, "win", weight_class_id=None, limit=10
            )
            
            # Then: weight_class_name이 None인 DTO 반환
            assert isinstance(result, WeightClassRankingsDTO)
            assert result.weight_class_name is None
            assert len(result.rankings) == 1
    
    @pytest.mark.asyncio
    async def test_get_top_fighters_by_record_different_records(self):
        """다양한 기록 타입(win, loss, draw) 테스트"""
        # Given: 각 기록 타입별 데이터
        mock_session = AsyncMock()
        
        test_cases = [
            ("win", "최다 승수"),
            ("loss", "최다 패수"),
            ("draw", "최다 무승부")
        ]
        
        for record_type, description in test_cases:
            fighter_data = [{
                "ranking": 1,
                "fighter": FighterSchema(id=1, name=f"Fighter for {description}", wins=10, losses=5, draws=2)
            }]
            
            with patch('fighter.repositories.get_top_fighter_by_record', return_value=fighter_data):
                # When: 서비스 함수 호출
                result = await fighter_services.get_top_fighters_by_record(
                    mock_session, record_type, limit=5
                )
                
                # Then: 올바른 결과 반환
                assert isinstance(result, WeightClassRankingsDTO)
                assert len(result.rankings) == 1


class TestBuildFighterWithRankings:
    """_build_fighter_with_rankings 헬퍼 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_build_fighter_with_rankings_multiple_weight_classes(self):
        """여러 체급에서 랭킹을 가진 파이터"""
        # Given: 여러 체급 랭킹 데이터
        mock_session = AsyncMock()
        fighter_data = FighterSchema(
            id=5,
            name="Multi-Division Champion",
            wins=20,
            losses=0,
            draws=0
        )
        ranking_data = [
            RankingSchema(id=1, fighter_id=5, weight_class_id=1, ranking=1),
            RankingSchema(id=2, fighter_id=5, weight_class_id=2, ranking=1),
            RankingSchema(id=3, fighter_id=5, weight_class_id=3, ranking=2)
        ]
        
        with patch('fighter.repositories.get_ranking_by_fighter_id', return_value=ranking_data), \
             patch('common.models.WeightClassSchema.get_name_by_id', side_effect=lambda x: f"Division_{x}"):
            
            # When: 헬퍼 함수 호출
            result = await fighter_services._build_fighter_with_rankings(mock_session, fighter_data)
            
            # Then: 모든 체급의 랭킹이 포함된 DTO 반환
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.fighter.id == 5
            assert len(result.rankings) == 3
            assert result.rankings["Division_1"] == 1
            assert result.rankings["Division_2"] == 1
            assert result.rankings["Division_3"] == 2
    
    @pytest.mark.asyncio
    async def test_build_fighter_with_rankings_weight_class_name_none(self):
        """체급명이 None인 경우 처리"""
        # Given: 체급명이 None을 반환하는 경우
        mock_session = AsyncMock()
        fighter_data = FighterSchema(id=6, name="Test Fighter", wins=10, losses=2, draws=0)
        ranking_data = [RankingSchema(id=1, fighter_id=6, weight_class_id=999, ranking=5)]
        
        with patch('fighter.repositories.get_ranking_by_fighter_id', return_value=ranking_data), \
             patch('common.models.WeightClassSchema.get_name_by_id', return_value=None):
            
            # When: 헬퍼 함수 호출
            result = await fighter_services._build_fighter_with_rankings(mock_session, fighter_data)
            
            # Then: None 키가 제외된 빈 랭킹 딕셔너리
            assert isinstance(result, FighterWithRankingsDTO)
            assert result.rankings == {}  # None 값은 제외되어야 함


class TestServiceLayerIntegration:
    """서비스 레이어 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_service_functions_call_correct_repositories(self):
        """서비스 함수들이 올바른 repository 함수를 호출하는지 확인"""
        # Given: 모든 repository 함수 모킹
        mock_session = AsyncMock()
        fighter_data = FighterSchema(id=1, name="Test Fighter", wins=10, losses=1, draws=0)
        
        with patch('fighter.repositories.get_fighter_by_id') as mock_get_by_id, \
             patch('fighter.repositories.get_fighter_by_name') as mock_get_by_name, \
             patch('fighter.repositories.get_fighter_by_nickname') as mock_get_by_nickname, \
             patch('fighter.repositories.get_ranking_by_fighter_id', return_value=[]), \
             patch('fighter.repositories.get_fighters_by_weight_class_ranking', return_value=[]), \
             patch('fighter.repositories.get_top_fighter_by_record', return_value=[]), \
             patch('common.models.WeightClassSchema.get_id_by_name', return_value=1), \
             patch('common.models.WeightClassSchema.get_name_by_id', return_value="TestClass"):
            
            # ID로 조회 테스트
            mock_get_by_id.return_value = fighter_data
            await fighter_services.get_fighter_by_id(mock_session, 1)
            mock_get_by_id.assert_called_once_with(mock_session, 1)
            
            # 이름으로 조회 테스트
            mock_get_by_name.return_value = fighter_data
            await fighter_services.get_fighter_by_name(mock_session, "Test Fighter")
            mock_get_by_name.assert_called_once_with(mock_session, "Test Fighter")
            
            # 닉네임으로 조회 테스트
            mock_get_by_nickname.return_value = fighter_data
            await fighter_services.get_fighter_by_nickname(mock_session, "Test Nickname")
            mock_get_by_nickname.assert_called_once_with(mock_session, "Test Nickname")


class TestReturnTypeBug:
    """수정된 반환 타입 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_top_fighters_by_record_return_type_fixed(self):
        """
        get_top_fighters_by_record 함수의 반환 타입이 올바르게 수정되었는지 확인
        함수 시그니처: -> WeightClassRankingsDTO
        실제 반환: WeightClassRankingsDTO
        """
        # Given: 모킹된 데이터
        mock_session = AsyncMock()
        fighter_data = [{
            "ranking": 1,
            "fighter": FighterSchema(id=1, name="Test Fighter", wins=20, losses=0, draws=0)
        }]
        
        with patch('fighter.repositories.get_top_fighter_by_record', return_value=fighter_data):
            # When: 함수 호출
            result = await fighter_services.get_top_fighters_by_record(mock_session, "win")
            
            # Then: WeightClassRankingsDTO가 반환됨 (수정됨)
            assert isinstance(result, WeightClassRankingsDTO)
            assert result.weight_class_name is None  # weight_class_id가 None인 경우
            assert len(result.rankings) == 1


if __name__ == "__main__":
    # 간단한 실행 테스트
    print("Fighter Services 테스트 실행...")
    print("✅ 테스트 파일 생성 완료!")
    print("\n전체 테스트 실행: pytest src/fighter/test/test_services.py -v")
    print("특정 테스트 클래스 실행: pytest src/fighter/test/test_services.py::TestGetFighterById -v")