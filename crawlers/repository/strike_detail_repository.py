from sqlalchemy.orm import Session
from typing import Optional, List

from models.match_model import StrikeDetailModel
from schemas.match import StrikeDetail

class StrikeDetailRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def upsert(self, strike_detail: StrikeDetail) -> StrikeDetail:
        """스트라이크 상세 정보를 업서트합니다."""
        # 이미 존재하는 스트라이크 상세 정보인지 확인
        existing_detail = self.find_by_fighter_match_id(strike_detail.fighter_match_id)
        
        if existing_detail:
            # 기존 스트라이크 상세 정보 업데이트
            detail_model = self.session.query(StrikeDetailModel).filter(
                StrikeDetailModel.fighter_match_id == strike_detail.fighter_match_id
            ).first()
            
            # 필드 업데이트
            detail_model.head_strikes_landed = strike_detail.head_strikes_landed
            detail_model.head_strikes_attempts = strike_detail.head_strikes_attempts
            detail_model.body_strikes_landed = strike_detail.body_strikes_landed
            detail_model.body_strikes_attempts = strike_detail.body_strikes_attempts
            detail_model.leg_strikes_landed = strike_detail.leg_strikes_landed
            detail_model.leg_strikes_attempts = strike_detail.leg_strikes_attempts
            detail_model.clinch_strikes_landed = strike_detail.clinch_strikes_landed
            detail_model.clinch_strikes_attempts = strike_detail.clinch_strikes_attempts
            detail_model.ground_strikes_landed = strike_detail.ground_strikes_landed
            detail_model.ground_strikes_attempts = strike_detail.ground_strikes_attempts
            
            self.session.commit()
            return detail_model.to_schema()
        else:
            # 새 스트라이크 상세 정보 생성
            detail_model = StrikeDetailModel.from_schema(strike_detail)
            self.session.add(detail_model)
            self.session.commit()
            return detail_model.to_schema()
    
    def bulk_upsert(self, strike_details: List[StrikeDetail]) -> List[StrikeDetail]:
        """여러 스트라이크 상세 정보를 업서트합니다."""
        result = []
        for strike_detail in strike_details:
            result.append(self.upsert(strike_detail))
        return result
    
    def find_by_fighter_match_id(self, fighter_match_id: int) -> Optional[StrikeDetail]:
        """파이터 매치 ID로 스트라이크 상세 정보를 조회합니다."""
        detail_model = self.session.query(StrikeDetailModel).filter(
            StrikeDetailModel.fighter_match_id == fighter_match_id
        ).first()
        
        if detail_model:
            return detail_model.to_schema()
        return None
    
    def find_all_by_fighter_match_id(self, fighter_match_id: int) -> List[StrikeDetail]:
        """파이터 매치 ID로 모든 스트라이크 상세 정보를 조회합니다."""
        detail_models = self.session.query(StrikeDetailModel).filter(
            StrikeDetailModel.fighter_match_id == fighter_match_id
        ).all()
        
        return [detail_model.to_schema() for detail_model in detail_models]
