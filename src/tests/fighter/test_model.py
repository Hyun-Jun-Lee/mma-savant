import pytest
from datetime import date, datetime

import database

from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema


class TestFighterModelTransformers:
    """FighterModel의 from_schema, to_schema 메서드 테스트"""
    
    def test_fighter_from_schema_basic(self):
        """기본적인 FighterSchema -> FighterModel 변환 테스트"""
        # Given: 테스트용 FighterSchema 생성
        fighter_schema = FighterSchema(
            name="Jon Jones",
            nickname="Bones",
            height=76.0,
            height_cm=193.0,
            weight=205.0,
            weight_kg=93.0,
            reach=84.5,
            reach_cm=214.6,
            stance="Orthodox",
            belt=True,
            birthdate=date(1987, 7, 19),
            detail_url="http://example.com/jon-jones",
            wins=26,
            losses=1,
            draws=0
        )
        
        # When: 모델의 from_schema 메서드 사용
        fighter_model = FighterModel.from_schema(fighter_schema)
        
        # Then: 모든 필드가 올바르게 변환되었는지 확인
        assert fighter_model.name == "Jon Jones"
        assert fighter_model.nickname == "Bones"
        assert fighter_model.height == 76.0
        assert fighter_model.height_cm == 193.0
        assert fighter_model.weight == 205.0
        assert fighter_model.weight_kg == 93.0
        assert fighter_model.reach == 84.5
        assert fighter_model.reach_cm == 214.6
        assert fighter_model.stance == "Orthodox"
        assert fighter_model.belt is True
        assert fighter_model.birthdate == date(1987, 7, 19)
        assert fighter_model.detail_url == "http://example.com/jon-jones"
        assert fighter_model.wins == 26
        assert fighter_model.losses == 1
        assert fighter_model.draws == 0
        
        # 제외된 필드들은 기본값이어야 함
        assert fighter_model.id is None
        assert fighter_model.created_at is None
        assert fighter_model.updated_at is None
    
    def test_fighter_from_schema_with_none_values(self):
        """None 값이 포함된 FighterSchema 변환 테스트"""
        # Given: 일부 필드가 None인 FighterSchema
        fighter_schema = FighterSchema(
            name="Unknown Fighter",
            nickname=None,
            height=None,
            stance=None,
            belt=False,
            wins=5,
            losses=2,
            draws=0
        )
        
        # When: 변환 실행
        fighter_model = FighterModel.from_schema(fighter_schema)
        
        # Then: None 값들이 올바르게 처리되었는지 확인
        assert fighter_model.name == "Unknown Fighter"
        assert fighter_model.nickname is None
        assert fighter_model.height is None
        assert fighter_model.stance is None
        assert fighter_model.belt is False
        assert fighter_model.wins == 5
        assert fighter_model.losses == 2
        assert fighter_model.draws == 0
    
    def test_fighter_to_schema_basic(self):
        """기본적인 FighterModel -> FighterSchema 변환 테스트"""
        # Given: 테스트용 FighterModel 생성 (DB에서 조회한 것처럼)
        fighter_model = FighterModel(
            id=1,
            name="Amanda Nunes",
            nickname="The Lioness",
            height=68.0,
            height_cm=173.0,
            weight=135.0,
            weight_kg=61.2,
            reach=69.0,
            reach_cm=175.3,
            stance="Orthodox",
            belt=True,
            birthdate=date(1988, 5, 30),
            detail_url="http://example.com/amanda-nunes",
            wins=22,
            losses=5,
            draws=0,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 2, 15, 30, 0)
        )
        
        # When: FighterModel의 to_schema 메서드 사용
        fighter_schema = fighter_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환되었는지 확인
        assert fighter_schema.id == 1
        assert fighter_schema.name == "Amanda Nunes"
        assert fighter_schema.nickname == "The Lioness"
        assert fighter_schema.height == 68.0
        assert fighter_schema.height_cm == 173.0
        assert fighter_schema.weight == 135.0
        assert fighter_schema.weight_kg == 61.2
        assert fighter_schema.reach == 69.0
        assert fighter_schema.reach_cm == 175.3
        assert fighter_schema.stance == "Orthodox"
        assert fighter_schema.belt is True
        assert fighter_schema.birthdate == date(1988, 5, 30)
        assert fighter_schema.detail_url == "http://example.com/amanda-nunes"
        assert fighter_schema.wins == 22
        assert fighter_schema.losses == 5
        assert fighter_schema.draws == 0
        assert fighter_schema.created_at == datetime(2024, 1, 1, 10, 0, 0)
        assert fighter_schema.updated_at == datetime(2024, 1, 2, 15, 30, 0)
    
    def test_round_trip_conversion(self):
        """Schema -> Model -> Schema 왕복 변환 테스트"""
        # Given: 원본 FighterSchema
        original_schema = FighterSchema(
            name="Conor McGregor",
            nickname="The Notorious",
            height=69.0,
            height_cm=175.3,
            weight=155.0,
            weight_kg=70.3,
            reach=74.0,
            reach_cm=188.0,
            stance="Southpaw",
            belt=False,
            wins=22,
            losses=6,
            draws=0
        )
        
        # When: Schema -> Model -> Schema 변환
        fighter_model = FighterModel.from_schema(original_schema)
        # DB 저장 시뮬레이션 (id와 timestamp 추가)
        fighter_model.id = 99
        fighter_model.created_at = datetime.now()
        fighter_model.updated_at = datetime.now()
        
        converted_schema = fighter_model.to_schema()
        
        # Then: 원본과 변환된 스키마의 비즈니스 데이터가 일치해야 함
        assert converted_schema.name == original_schema.name
        assert converted_schema.nickname == original_schema.nickname
        assert converted_schema.height == original_schema.height
        assert converted_schema.height_cm == original_schema.height_cm
        assert converted_schema.weight == original_schema.weight
        assert converted_schema.weight_kg == original_schema.weight_kg
        assert converted_schema.reach == original_schema.reach
        assert converted_schema.reach_cm == original_schema.reach_cm
        assert converted_schema.stance == original_schema.stance
        assert converted_schema.belt == original_schema.belt
        assert converted_schema.wins == original_schema.wins
        assert converted_schema.losses == original_schema.losses
        assert converted_schema.draws == original_schema.draws
        
        # 추가된 메타데이터 확인
        assert converted_schema.id == 99
        assert converted_schema.created_at is not None
        assert converted_schema.updated_at is not None


class TestRankingModelTransformers:
    """RankingModel의 from_schema, to_schema 메서드 테스트"""
    
    def test_ranking_from_schema_basic(self):
        """기본적인 RankingSchema -> RankingModel 변환 테스트"""
        # Given: 테스트용 RankingSchema 생성
        ranking_schema = RankingSchema(
            fighter_id=1,
            weight_class_id=5,
            ranking=3
        )
        
        # When: 모델의 from_schema 메서드 사용
        ranking_model = RankingModel.from_schema(ranking_schema)
        
        # Then: 모든 필드가 올바르게 변환되었는지 확인
        assert ranking_model.fighter_id == 1
        assert ranking_model.weight_class_id == 5
        assert ranking_model.ranking == 3
        
        # 제외된 필드들은 기본값이어야 함
        assert ranking_model.id is None
        assert ranking_model.created_at is None
        assert ranking_model.updated_at is None
    
    def test_ranking_to_schema_basic(self):
        """기본적인 RankingModel -> RankingSchema 변환 테스트"""
        # Given: 테스트용 RankingModel 생성
        ranking_model = RankingModel(
            id=10,
            fighter_id=2,
            weight_class_id=3,
            ranking=1,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        # When: RankingModel의 to_schema 메서드 사용
        ranking_schema = ranking_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환되었는지 확인
        assert ranking_schema.id == 10
        assert ranking_schema.fighter_id == 2
        assert ranking_schema.weight_class_id == 3
        assert ranking_schema.ranking == 1
        assert ranking_schema.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert ranking_schema.updated_at == datetime(2024, 1, 1, 12, 0, 0)
    
    def test_ranking_round_trip_conversion(self):
        """Ranking Schema -> Model -> Schema 왕복 변환 테스트"""
        # Given: 원본 RankingSchema
        original_schema = RankingSchema(
            fighter_id=5,
            weight_class_id=2,
            ranking=8
        )
        
        # When: Schema -> Model -> Schema 변환
        ranking_model = RankingModel.from_schema(original_schema)
        # DB 저장 시뮬레이션
        ranking_model.id = 25
        ranking_model.created_at = datetime.now()
        ranking_model.updated_at = datetime.now()
        
        converted_schema = ranking_model.to_schema()
        
        # Then: 원본과 변환된 스키마의 비즈니스 데이터가 일치해야 함
        assert converted_schema.fighter_id == original_schema.fighter_id
        assert converted_schema.weight_class_id == original_schema.weight_class_id
        assert converted_schema.ranking == original_schema.ranking
        
        # 추가된 메타데이터 확인
        assert converted_schema.id == 25
        assert converted_schema.created_at is not None
        assert converted_schema.updated_at is not None


class TestEdgeCases:
    """엣지 케이스 및 오류 상황 테스트"""
    
    def test_fighter_schema_with_default_values(self):
        """기본값이 있는 필드들의 처리 테스트"""
        # Given: 기본값을 가진 필드들만 설정한 스키마
        fighter_schema = FighterSchema(
            name="Test Fighter",
            # 나머지 필드들은 기본값 사용
        )
        
        # When: from_schema 메서드 사용
        fighter_model = FighterModel.from_schema(fighter_schema)
        
        # Then: 기본값들이 올바르게 설정되어야 함
        assert fighter_model.name == "Test Fighter"
        assert fighter_model.wins == 0  # 기본값
        assert fighter_model.losses == 0  # 기본값
        assert fighter_model.draws == 0  # 기본값
        assert fighter_model.belt is False  # 기본값
        assert fighter_model.height == 0  # 기본값
    
    def test_schema_validation_error(self):
        """잘못된 데이터로 스키마 생성 시 오류 테스트"""
        # Given & When & Then: 필수 필드 누락 시 Pydantic 검증 오류 발생
        with pytest.raises(Exception):  # Pydantic ValidationError
            FighterSchema()  # name 필드 누락
    
    def test_model_with_none_values(self):
        """None 값이 포함된 모델의 to_schema 변환 테스트"""
        # Given: 일부 필드가 None인 모델
        fighter_model = FighterModel(
            id=1,
            name="Test Fighter",
            nickname=None,  # None 값
            height=None,    # None 값
            stance=None,    # None 값
            wins=3,
            losses=1,
            draws=0,
            belt=False,
            detail_url=None,
            birthdate=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # When: to_schema 메서드 사용
        fighter_schema = fighter_model.to_schema()
        
        # Then: None 값들이 올바르게 변환되어야 함
        assert fighter_schema.name == "Test Fighter"
        assert fighter_schema.nickname is None
        assert fighter_schema.height is None
        assert fighter_schema.stance is None
        assert fighter_schema.wins == 3
        assert fighter_schema.losses == 1
        assert fighter_schema.draws == 0


if __name__ == "__main__":
    # 간단한 실행 테스트
    print("Fighter Model Transformers 테스트 실행...")
    
    # 기본 변환 테스트
    test_fighter = TestFighterModelTransformers()
    test_fighter.test_fighter_from_schema_basic()
    test_fighter.test_fighter_to_schema_basic()
    test_fighter.test_round_trip_conversion()
    
    test_ranking = TestRankingModelTransformers()
    test_ranking.test_ranking_from_schema_basic()
    test_ranking.test_ranking_to_schema_basic()
    test_ranking.test_ranking_round_trip_conversion()
    
    print("✅ 모든 기본 테스트 통과!")
    print("\n전체 테스트 실행: pytest src/fighter/test/test_model_transformers.py")