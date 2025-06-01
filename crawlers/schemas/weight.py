from pydantic import ConfigDict
from typing import Optional, Dict, ClassVar
from enum import Enum

from schemas.base import BaseSchema

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

class WeightClass(BaseSchema):
    name: str
    
    # 체급별 ID 매핑 (DB에 미리 저장된 ID와 일치해야 함)
    WEIGHT_CLASS_IDS: ClassVar[Dict[str, int]] = {
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