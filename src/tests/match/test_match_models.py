"""
Match Models 테스트
match/models.py의 모든 모델과 스키마에 대한 포괄적인 테스트
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from common.utils import utc_now
from match.models import (
    MatchModel, MatchSchema,
    FighterMatchModel, FighterMatchSchema,
    SigStrMatchStatModel, SigStrMatchStatSchema,
    BasicMatchStatModel, BasicMatchStatSchema
)


class TestMatchSchema:
    """MatchSchema 스키마 검증 테스트"""
    
    def test_match_schema_creation_with_required_fields(self):
        """필수 필드로만 MatchSchema 생성 테스트"""
        # Given: 필수 필드만 있는 데이터
        match_data = {
            "event_id": 1,
            "weight_class_id": 5,
            "method": "Decision - Unanimous",
            "result_round": 3,
            "time": "15:00",
            "order": 1
        }
        
        # When: 스키마 생성
        match_schema = MatchSchema(**match_data)
        
        # Then: 올바르게 생성됨
        assert match_schema.event_id == 1
        assert match_schema.weight_class_id == 5
        assert match_schema.method == "Decision - Unanimous"
        assert match_schema.result_round == 3
        assert match_schema.time == "15:00"
        assert match_schema.order == 1
        assert match_schema.is_main_event is False  # 기본값
        assert match_schema.detail_url is None  # 선택적 필드
    
    def test_match_schema_creation_with_all_fields(self):
        """모든 필드를 포함한 MatchSchema 생성 테스트"""
        # Given: 모든 필드를 포함한 데이터
        match_data = {
            "id": 123,
            "event_id": 1,
            "weight_class_id": 5,
            "method": "KO/TKO",
            "result_round": 2,
            "time": "3:24",
            "order": 8,
            "is_main_event": True,
            "detail_url": "http://example.com/match/123",
            "created_at": utc_now(),
            "updated_at": utc_now()
        }

        # When: 스키마 생성
        match_schema = MatchSchema(**match_data)
        
        # Then: 모든 필드가 올바르게 설정됨
        assert match_schema.id == 123
        assert match_schema.is_main_event is True
        assert match_schema.detail_url == "http://example.com/match/123"
        assert match_schema.created_at is not None
        assert match_schema.updated_at is not None
    
    def test_match_schema_validation_errors(self):
        """MatchSchema 유효성 검증 실패 테스트"""
        # Given: 필수 필드 누락 (event_id 누락)
        invalid_data = {
            "weight_class_id": 5,
            "method": "Decision"
            # event_id 누락 (필수 필드)
        }
        
        # When & Then: ValidationError 발생
        with pytest.raises(ValidationError):
            MatchSchema(**invalid_data)


class TestFighterMatchSchema:
    """FighterMatchSchema 스키마 검증 테스트"""
    
    def test_fighter_match_schema_creation(self):
        """FighterMatchSchema 생성 테스트"""
        # Given: 파이터 매치 데이터
        fighter_match_data = {
            "fighter_id": 10,
            "match_id": 5,
            "result": "win"
        }
        
        # When: 스키마 생성
        fighter_match_schema = FighterMatchSchema(**fighter_match_data)
        
        # Then: 올바르게 생성됨
        assert fighter_match_schema.fighter_id == 10
        assert fighter_match_schema.match_id == 5
        assert fighter_match_schema.result == "win"
    
    def test_fighter_match_schema_result_values(self):
        """FighterMatchSchema result 필드 값 테스트"""
        # Given: 다양한 result 값들
        results = ["win", "loss", "draw", "no_contest"]
        
        for result in results:
            # When: 각 result 값으로 스키마 생성
            fighter_match_data = {
                "fighter_id": 10,
                "match_id": 5,
                "result": result
            }
            fighter_match_schema = FighterMatchSchema(**fighter_match_data)
            
            # Then: result 값이 올바르게 설정됨
            assert fighter_match_schema.result == result


class TestSigStrMatchStatSchema:
    """SigStrMatchStatSchema 스키마 검증 테스트"""
    
    def test_sig_str_schema_creation_with_defaults(self):
        """기본값으로 SigStrMatchStatSchema 생성 테스트"""
        # Given: fighter_match_id만 있는 데이터
        stat_data = {
            "fighter_match_id": 123
        }
        
        # When: 스키마 생성
        stat_schema = SigStrMatchStatSchema(**stat_data)
        
        # Then: 모든 통계가 기본값 0으로 설정됨
        assert stat_schema.fighter_match_id == 123
        assert stat_schema.head_strikes_landed == 0
        assert stat_schema.head_strikes_attempts == 0
        assert stat_schema.body_strikes_landed == 0
        assert stat_schema.body_strikes_attempts == 0
        assert stat_schema.leg_strikes_landed == 0
        assert stat_schema.leg_strikes_attempts == 0
        assert stat_schema.takedowns_landed == 0
        assert stat_schema.takedowns_attempts == 0
        assert stat_schema.clinch_strikes_landed == 0
        assert stat_schema.clinch_strikes_attempts == 0
        assert stat_schema.ground_strikes_landed == 0
        assert stat_schema.ground_strikes_attempts == 0
        assert stat_schema.round == 0
    
    def test_sig_str_schema_creation_with_values(self):
        """실제 값들로 SigStrMatchStatSchema 생성 테스트"""
        # Given: 실제 통계 데이터
        stat_data = {
            "fighter_match_id": 123,
            "head_strikes_landed": 25,
            "head_strikes_attempts": 45,
            "body_strikes_landed": 15,
            "body_strikes_attempts": 28,
            "leg_strikes_landed": 8,
            "leg_strikes_attempts": 12,
            "takedowns_landed": 5,
            "takedowns_attempts": 10,
            "clinch_strikes_landed": 10,
            "clinch_strikes_attempts": 18,
            "ground_strikes_landed": 3,
            "ground_strikes_attempts": 7,
            "round": 3
        }
        
        # When: 스키마 생성
        stat_schema = SigStrMatchStatSchema(**stat_data)
        
        # Then: 모든 값이 올바르게 설정됨
        assert stat_schema.head_strikes_landed == 25
        assert stat_schema.head_strikes_attempts == 45
        assert stat_schema.body_strikes_landed == 15
        assert stat_schema.leg_strikes_landed == 8
        assert stat_schema.takedowns_landed == 5
        assert stat_schema.round == 3


class TestBasicMatchStatSchema:
    """BasicMatchStatSchema 스키마 검증 테스트"""
    
    def test_basic_stat_schema_creation_with_defaults(self):
        """기본값으로 BasicMatchStatSchema 생성 테스트"""
        # Given: fighter_match_id만 있는 데이터
        stat_data = {
            "fighter_match_id": 456
        }
        
        # When: 스키마 생성
        stat_schema = BasicMatchStatSchema(**stat_data)
        
        # Then: 모든 통계가 기본값 0으로 설정됨
        assert stat_schema.fighter_match_id == 456
        assert stat_schema.knockdowns == 0
        assert stat_schema.control_time_seconds == 0
        assert stat_schema.submission_attempts == 0
        assert stat_schema.sig_str_landed == 0
        assert stat_schema.sig_str_attempted == 0
        assert stat_schema.total_str_landed == 0
        assert stat_schema.total_str_attempted == 0
        assert stat_schema.td_landed == 0
        assert stat_schema.td_attempted == 0
        assert stat_schema.round == 0
    
    def test_basic_stat_schema_creation_with_values(self):
        """실제 값들로 BasicMatchStatSchema 생성 테스트"""
        # Given: 실제 기본 통계 데이터
        stat_data = {
            "fighter_match_id": 456,
            "knockdowns": 2,
            "control_time_seconds": 180,
            "submission_attempts": 3,
            "sig_str_landed": 45,
            "sig_str_attempted": 72,
            "total_str_landed": 65,
            "total_str_attempted": 95,
            "td_landed": 4,
            "td_attempted": 8,
            "round": 5
        }
        
        # When: 스키마 생성
        stat_schema = BasicMatchStatSchema(**stat_data)
        
        # Then: 모든 값이 올바르게 설정됨
        assert stat_schema.knockdowns == 2
        assert stat_schema.control_time_seconds == 180
        assert stat_schema.submission_attempts == 3
        assert stat_schema.sig_str_landed == 45
        assert stat_schema.td_landed == 4
        assert stat_schema.round == 5


class TestMatchModelTransformations:
    """MatchModel 변환 메서드 테스트"""
    
    def test_match_model_from_schema(self):
        """MatchSchema에서 MatchModel로 변환 테스트"""
        # Given: MatchSchema
        match_schema = MatchSchema(
            event_id=1,
            weight_class_id=5,
            method="Decision - Unanimous",
            result_round=3,
            time="15:00",
            order=1,
            is_main_event=True,
            detail_url="http://example.com/match"
        )
        
        # When: Model로 변환
        match_model = MatchModel.from_schema(match_schema)
        
        # Then: 모든 필드가 올바르게 변환됨
        assert match_model.event_id == 1
        assert match_model.weight_class_id == 5
        assert match_model.method == "Decision - Unanimous"
        assert match_model.result_round == 3
        assert match_model.time == "15:00"
        assert match_model.order == 1
        assert match_model.is_main_event is True
        assert match_model.detail_url == "http://example.com/match"
    
    def test_match_model_to_schema(self):
        """MatchModel에서 MatchSchema로 변환 테스트"""
        # Given: MatchModel
        match_model = MatchModel(
            id=123,
            event_id=1,
            weight_class_id=5,
            method="KO/TKO",
            result_round=2,
            time="3:24",
            order=8,
            is_main_event=False,
            detail_url="http://example.com/match/123"
        )
        
        # When: Schema로 변환
        match_schema = match_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환됨
        assert match_schema.id == 123
        assert match_schema.event_id == 1
        assert match_schema.weight_class_id == 5
        assert match_schema.method == "KO/TKO"
        assert match_schema.result_round == 2
        assert match_schema.time == "3:24"
        assert match_schema.order == 8
        assert match_schema.is_main_event is False
        assert match_schema.detail_url == "http://example.com/match/123"


class TestFighterMatchModelTransformations:
    """FighterMatchModel 변환 메서드 테스트"""
    
    def test_fighter_match_model_from_schema(self):
        """FighterMatchModel 생성 테스트 (from_schema 메서드는 복잡한 관계 때문에 직접 테스트)"""
        # Given: FighterMatchModel 직접 생성
        fighter_match_model = FighterMatchModel(
            fighter_id=10,
            match_id=5,
            result="win"
        )
        
        # Then: 모든 필드가 올바르게 설정됨
        assert fighter_match_model.fighter_id == 10
        assert fighter_match_model.match_id == 5
        assert fighter_match_model.result == "win"
    
    def test_fighter_match_model_to_schema(self):
        """FighterMatchModel에서 FighterMatchSchema로 변환 테스트"""
        # Given: FighterMatchModel
        fighter_match_model = FighterMatchModel(
            id=789,
            fighter_id=10,
            match_id=5,
            result="loss"
        )
        
        # When: Schema로 변환
        fighter_match_schema = fighter_match_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환됨
        assert fighter_match_schema.id == 789
        assert fighter_match_schema.fighter_id == 10
        assert fighter_match_schema.match_id == 5
        assert fighter_match_schema.result == "loss"


class TestSigStrMatchStatModelTransformations:
    """SigStrMatchStatModel 변환 메서드 테스트"""
    
    def test_sig_str_stat_model_from_schema(self):
        """SigStrMatchStatSchema에서 SigStrMatchStatModel로 변환 테스트"""
        # Given: SigStrMatchStatSchema
        stat_schema = SigStrMatchStatSchema(
            fighter_match_id=123,
            head_strikes_landed=25,
            head_strikes_attempts=45,
            body_strikes_landed=15,
            leg_strikes_landed=8,
            round=3
        )
        
        # When: Model로 변환
        stat_model = SigStrMatchStatModel.from_schema(stat_schema)
        
        # Then: 모든 필드가 올바르게 변환됨
        assert stat_model.fighter_match_id == 123
        assert stat_model.head_strikes_landed == 25
        assert stat_model.head_strikes_attempts == 45
        assert stat_model.body_strikes_landed == 15
        assert stat_model.leg_strikes_landed == 8
        assert stat_model.round == 3
    
    def test_sig_str_stat_model_to_schema(self):
        """SigStrMatchStatModel에서 SigStrMatchStatSchema로 변환 테스트"""
        # Given: SigStrMatchStatModel
        stat_model = SigStrMatchStatModel(
            id=999,
            fighter_match_id=123,
            head_strikes_landed=30,
            body_strikes_attempts=40,
            leg_strikes_landed=12,
            takedowns_landed=5,
            round=5
        )
        
        # When: Schema로 변환
        stat_schema = stat_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환됨
        assert stat_schema.id == 999
        assert stat_schema.fighter_match_id == 123
        assert stat_schema.head_strikes_landed == 30
        assert stat_schema.body_strikes_attempts == 40
        assert stat_schema.leg_strikes_landed == 12
        assert stat_schema.takedowns_landed == 5
        assert stat_schema.round == 5


class TestBasicMatchStatModelTransformations:
    """BasicMatchStatModel 변환 메서드 테스트"""
    
    def test_basic_stat_model_from_schema(self):
        """BasicMatchStatSchema에서 BasicMatchStatModel로 변환 테스트"""
        # Given: BasicMatchStatSchema
        stat_schema = BasicMatchStatSchema(
            fighter_match_id=456,
            knockdowns=2,
            control_time_seconds=180,
            submission_attempts=3,
            sig_str_landed=45,
            td_landed=4,
            round=5
        )
        
        # When: Model로 변환
        stat_model = BasicMatchStatModel.from_schema(stat_schema)
        
        # Then: 모든 필드가 올바르게 변환됨
        assert stat_model.fighter_match_id == 456
        assert stat_model.knockdowns == 2
        assert stat_model.control_time_seconds == 180
        assert stat_model.submission_attempts == 3
        assert stat_model.sig_str_landed == 45
        assert stat_model.td_landed == 4
        assert stat_model.round == 5
    
    def test_basic_stat_model_to_schema(self):
        """BasicMatchStatModel에서 BasicMatchStatSchema로 변환 테스트"""
        # Given: BasicMatchStatModel
        stat_model = BasicMatchStatModel(
            id=888,
            fighter_match_id=456,
            knockdowns=1,
            control_time_seconds=240,
            submission_attempts=2,
            total_str_landed=80,
            td_attempted=6,
            round=3
        )
        
        # When: Schema로 변환
        stat_schema = stat_model.to_schema()
        
        # Then: 모든 필드가 올바르게 변환됨
        assert stat_schema.id == 888
        assert stat_schema.fighter_match_id == 456
        assert stat_schema.knockdowns == 1
        assert stat_schema.control_time_seconds == 240
        assert stat_schema.submission_attempts == 2
        assert stat_schema.total_str_landed == 80
        assert stat_schema.td_attempted == 6
        assert stat_schema.round == 3


class TestModelFieldConstraints:
    """모델 필드 제약조건 및 엣지 케이스 테스트"""
    
    def test_negative_statistics_handling(self):
        """음수 통계 값 처리 테스트"""
        # Given: 음수 값을 포함한 통계 데이터
        stat_data = {
            "fighter_match_id": 123,
            "head_strikes_landed": -5,  # 음수
            "knockdowns": -1  # 음수
        }
        
        # When & Then: 음수 값도 허용됨 (데이터 검증은 비즈니스 로직 레이어에서)
        sig_str_schema = SigStrMatchStatSchema(**stat_data)
        basic_stat_schema = BasicMatchStatSchema(**stat_data)
        
        assert sig_str_schema.head_strikes_landed == -5
        assert basic_stat_schema.knockdowns == -1
    
    def test_none_values_handling(self):
        """None 값 처리 테스트"""
        # Given: None 값들
        match_data = {
            "event_id": 1,
            "weight_class_id": 5,
            "method": "Decision",
            "result_round": 3,
            "time": "15:00",
            "order": 1,
            "detail_url": None  # None 값
        }
        
        # When: 스키마 생성
        match_schema = MatchSchema(**match_data)
        
        # Then: None 값이 올바르게 처리됨
        assert match_schema.detail_url is None
    
    def test_extremely_large_numbers(self):
        """매우 큰 숫자 값 처리 테스트"""
        # Given: 매우 큰 숫자들
        stat_data = {
            "fighter_match_id": 999999999,
            "control_time_seconds": 99999,
            "sig_str_attempted": 9999
        }
        
        # When: 스키마 생성
        basic_stat_schema = BasicMatchStatSchema(**stat_data)
        
        # Then: 큰 숫자도 올바르게 처리됨
        assert basic_stat_schema.fighter_match_id == 999999999
        assert basic_stat_schema.control_time_seconds == 99999
        assert basic_stat_schema.sig_str_attempted == 9999


if __name__ == "__main__":
    print("Match Models 테스트 실행...")
    print("✅ 모든 모델과 스키마에 대한 포괄적인 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_models.py -v")