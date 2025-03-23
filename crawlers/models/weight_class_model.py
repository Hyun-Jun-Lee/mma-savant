from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from models.base import BaseModel
from schemas import WeightClass


class WeightClassModel(BaseModel):
    __tablename__ = "weight_class"
    
    name = Column(String, nullable=False, unique=True)
    
    matches = relationship("MatchModel", back_populates="weight_class")

    @classmethod
    def from_schema(cls, weight_class: WeightClass) -> None:
        return cls(
            name=weight_class.name,
        )
    
    def to_schema(self) -> WeightClass:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return WeightClass(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active
        )