from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import Optional, List, Dict

from models.match_model import MatchModel, FighterMatchModel
from schemas.match import Match
from schemas.fighter import FighterMatch
from schemas.weight import WeightClass

class MatchRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def upsert(self, match: Match) -> Match:
        """매치 정보를 업서트합니다."""
        # 이미 존재하는 매치인지 확인
        if match.id:
            existing_match = self.find_by_id(match.id)
            if existing_match:
                # 기존 매치 업데이트
                match_model = self.session.query(MatchModel).filter(
                    MatchModel.id == match.id
                ).first()
                
                # 필드 업데이트
                match_model.event_id = match.event_id
                match_model.weight_class_id = match.weight_class_id
                match_model.method = match.method
                match_model.result_round = match.result_round
                match_model.time = match.time
                match_model.order = match.order
                match_model.is_main_event = match.is_main_event
                
                self.session.flush()
                return match_model.to_schema()
        
        # 새 매치 생성
        match_model = MatchModel.from_schema(match)
        self.session.add(match_model)
        self.session.flush()
        
        return match_model.to_schema()
    
    def bulk_upsert(self, matches: List[Match]) -> List[Match]:
        """여러 매치 정보를 업서트합니다."""
        result = []
        for match in matches:
            result.append(self.upsert(match))
        return result
    
    def find_by_id(self, id: int) -> Optional[Match]:
        """ID로 매치 정보를 조회합니다."""
        match = self.session.query(MatchModel).filter(
            MatchModel.id == id
        ).first()
        
        if match:
            return match.to_schema()
        
        return None
    
    def find_by_event_id(self, event_id: int) -> List[Match]:
        """이벤트 ID로 매치 정보를 조회합니다."""
        matches = self.session.query(MatchModel).filter(
            MatchModel.event_id == event_id
        ).all()
        
        return [match.to_schema() for match in matches]
    
    def find_all(self) -> List[Match]:
        """모든 매치 정보를 조회합니다."""
        matches = self.session.query(MatchModel).all()
        return [match.to_schema() for match in matches]


class FighterMatchRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def upsert(self, fighter_match: FighterMatch) -> FighterMatch:
        """파이터 매치 정보를 업서트합니다."""
        # 이미 존재하는 파이터 매치인지 확인
        existing_fighter_match = self.find_by_fighter_and_match(
            fighter_match.fighter_id, fighter_match.match_id
        )
        
        if existing_fighter_match:
            # 기존 파이터 매치 업데이트
            fighter_match_model = self.session.query(FighterMatchModel).filter(
                FighterMatchModel.fighter_id == fighter_match.fighter_id,
                FighterMatchModel.match_id == fighter_match.match_id
            ).first()
            
            # 필드 업데이트
            fighter_match_model.result = fighter_match.result
            
            self.session.flush()
            return fighter_match_model.to_schema()
        
        # 새 파이터 매치 생성
        fighter_match_model = FighterMatchModel(
            fighter_id=fighter_match.fighter_id,
            match_id=fighter_match.match_id,
            result=fighter_match.result
        )
        self.session.add(fighter_match_model)
        self.session.flush()
        
        return fighter_match_model.to_schema()
    
    def bulk_upsert(self, fighter_matches: List[FighterMatch]) -> List[FighterMatch]:
        """여러 파이터 매치 정보를 업서트합니다."""
        result = []
        for fighter_match in fighter_matches:
            result.append(self.upsert(fighter_match))
        return result
    
    def find_by_fighter_and_match(self, fighter_id: int, match_id: int) -> Optional[FighterMatch]:
        """파이터 ID와 매치 ID로 파이터 매치 정보를 조회합니다."""
        fighter_match = self.session.query(FighterMatchModel).filter(
            FighterMatchModel.fighter_id == fighter_id,
            FighterMatchModel.match_id == match_id
        ).first()
        
        if fighter_match:
            return fighter_match.to_schema()
        
        return None
    
    def find_by_fighter_id(self, fighter_id: int) -> List[FighterMatch]:
        """파이터 ID로 파이터 매치 정보를 조회합니다."""
        fighter_matches = self.session.query(FighterMatchModel).filter(
            FighterMatchModel.fighter_id == fighter_id
        ).all()
        
        return [fighter_match.to_schema() for fighter_match in fighter_matches]
    
    def find_by_match_id(self, match_id: int) -> List[FighterMatch]:
        """매치 ID로 파이터 매치 정보를 조회합니다."""
        fighter_matches = self.session.query(FighterMatchModel).filter(
            FighterMatchModel.match_id == match_id
        ).all()
        
        return [fighter_match.to_schema() for fighter_match in fighter_matches]

    def find_all(self)-> List[FighterMatch]:
        fighter_matches = self.session.query(FighterMatchModel).all()
        return [fighter_match.to_schema() for fighter_match in fighter_matches]
    
    def find_match_fighter_mapping(self) -> Dict[str, Dict[int, FighterMatch]]:
        """detail_url을 키로 하고 fighter_id를 서브키로 하는 딕셔너리 반환"""
        result_dict = {}
        
        # Match와 FighterMatch 조인하여 한 번에 가져오기
        stmt = (
            select(MatchModel, FighterMatchModel)
            .join(FighterMatchModel, FighterMatchModel.match_id == MatchModel.id)
            .where(MatchModel.detail_url.is_not(None))
        )
        
        rows = self.session.execute(stmt).all()
        
        for match, fighter_match in rows:
            detail_url = match.detail_url
            fighter_id = fighter_match.fighter_id
            
            if detail_url not in result_dict:
                result_dict[detail_url] = {}
            result_dict[detail_url][fighter_id] = fighter_match.to_schema()
        
        return result_dict