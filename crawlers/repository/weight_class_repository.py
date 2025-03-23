from sqlalchemy.orm import Session
from typing import Optional, List

from models.weight_class_model import WeightClassModel
from schemas.weight import WeightClass

class WeightClassRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def find_by_id(self, id: int) -> Optional[WeightClass]:
        """ID로 체급 정보를 조회합니다."""
        weight_class = self.session.query(WeightClassModel).filter(
            WeightClassModel.id == id
        ).first()
        
        if weight_class:
            return weight_class.to_schema()
        
        return None
    
    def find_by_name(self, name: str) -> Optional[WeightClass]:
        """이름으로 체급 정보를 조회합니다."""
        weight_class = self.session.query(WeightClassModel).filter(
            WeightClassModel.name == name
        ).first()
        
        if weight_class:
            return weight_class.to_schema()
        
        return None
    
    def find_all(self) -> List[WeightClass]:
        """모든 체급 정보를 조회합니다."""
        weight_classes = self.session.query(WeightClassModel).all()
        return [weight_class.to_schema() for weight_class in weight_classes]
