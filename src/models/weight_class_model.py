from typing import Dict
from enum import Enum

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from models.base import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class WeightClassEnum(str, Enum):
    """UFC 체급 Enum"""
    FLYWEIGHT = "flyweight"
    BANTAMWEIGHT = "bantamweight"
    FEATHERWEIGHT = "featherweight"
    LIGHTWEIGHT = "lightweight"
    WELTERWEIGHT = "welterweight"
    MIDDLEWEIGHT = "middleweight"
    LIGHT_HEAVYWEIGHT = "light heavyweight"
    HEAVYWEIGHT = "heavyweight"
    WOMENS_STRAWWEIGHT = "women's strawweight"
    WOMENS_FLYWEIGHT = "women's flyweight"
    WOMENS_BANTAMWEIGHT = "women's bantamweight"
    WOMENS_FEATHERWEIGHT = "women's featherweight"
    CATCH_WEIGHT = "catch weight"
    OPEN_WEIGHT = "open weight"

class WeightClassSchmea(BaseSchema):
    name: str
    
    # 체급별 ID 매핑 (DB에 미리 저장된 ID와 일치해야 함)
    WEIGHT_CLASS_IDS: Dict[str, int] = {
        WeightClassEnum.FLYWEIGHT.value: 1,
        WeightClassEnum.BANTAMWEIGHT.value: 2,
        WeightClassEnum.FEATHERWEIGHT.value: 3,
        WeightClassEnum.LIGHTWEIGHT.value: 4,
        WeightClassEnum.WELTERWEIGHT.value: 5,
        WeightClassEnum.MIDDLEWEIGHT.value: 6,
        WeightClassEnum.LIGHT_HEAVYWEIGHT.value: 7,
        WeightClassEnum.HEAVYWEIGHT.value: 8,
        WeightClassEnum.WOMENS_STRAWWEIGHT.value: 9,
        WeightClassEnum.WOMENS_FLYWEIGHT.value: 10,
        WeightClassEnum.WOMENS_BANTAMWEIGHT.value: 11,
        WeightClassEnum.WOMENS_FEATHERWEIGHT.value: 12,
        WeightClassEnum.CATCH_WEIGHT.value: 13,
        WeightClassEnum.OPEN_WEIGHT.value: 14,
    }
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def get_id_by_name(cls, name: str) -> Optional[int]:
        """체급 이름으로 ID를 조회합니다."""
        return cls.WEIGHT_CLASS_IDS.get(name)

#############################
########## MODEL ###########
#############################

class WeightClassModel(BaseModel):
    __tablename__ = "weight_class"
    
    name = Column(String, nullable=False, unique=True)
    
    matches = relationship("MatchModel", back_populates="weight_class")

    @classmethod
    def from_schema(cls, weight_class: WeightClassSchmea) -> None:
        return cls(
            name=weight_class.name,
        )
    
    def to_schema(self) -> WeightClassSchmea:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return WeightClassSchmea(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active
        )