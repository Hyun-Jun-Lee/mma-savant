from typing import Dict, Optional

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from pydantic import ConfigDict

from common.base_model import BaseModel, BaseSchema
from common.enums import WeightClassEnum

#############################
########## SCHEMA ###########
#############################

class WeightClassSchema(BaseSchema):
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
    
    @classmethod
    def get_name_by_id(cls, weight_class_id: int) -> Optional[str]:
        """체급 ID로 체급 이름을 조회합니다."""
        # 역방향 매핑 (ID -> 이름) - 조회 성능 최적화용
        WEIGHT_CLASS_NAMES = {v: k for k, v in cls.WEIGHT_CLASS_IDS.items()}
        return WEIGHT_CLASS_NAMES.get(weight_class_id)

#############################
########## MODEL ###########
#############################

class WeightClassModel(BaseModel):
    __tablename__ = "weight_class"
    
    name = Column(String, nullable=False, unique=True)
    
    rankings = relationship("RankingModel", back_populates="weight_class")
    matches = relationship("MatchModel", back_populates="weight_class")

    @classmethod
    def from_schema(cls, weight_class: WeightClassSchema) -> None:
        return cls(
            name=weight_class.name,
        )
    
    def to_schema(self) -> WeightClassSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return WeightClassSchema(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active
        )