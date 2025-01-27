from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

@dataclass
class FighterRecord:
    win_count: int
    loss_count: int
    draw_count: int
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict):
        """크롤링된 데이터를 FighterRecord 객체로 변환"""
        return cls(
            win_count=data.get("win_count", 0),
            loss_count=data.get("loss_count", 0),
            draw_count=data.get("draw_count", 0),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict:
        """FighterRecord 객체를 dictionary로 변환"""
        return {
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "draw_count": self.draw_count,
            "weight_classes": self.weight_classes,
            "rankings": self.rankings,
            "updated_at": self.updated_at
        }

@dataclass
class Fighter:
    name: str
    nickname: Optional[str]
    birthdate: Optional[date]
    height: Optional[float]
    height_cm: Optional[float]
    reach: Optional[float]
    reach_cm: Optional[float]
    record: Optional[FighterRecord] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def age(self) -> Optional[int]:
        if not self.birthdate:
            return None
        today = date.today()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
    
    @classmethod
    def from_dict(cls, data: Dict):
        """크롤링된 데이터를 Fighter 객체로 변환"""
        record_data = data.get("record", {})
        return cls(
            name=data["name"],
            nickname=data.get("nickname"),
            birthdate=data.get("birthdate"),
            height=data.get("height"),
            height_cm=data.get("height_cm"),
            reach=data.get("reach"),
            reach_cm=data.get("reach_cm"),
            record=FighterRecord.from_dict(record_data) if record_data else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict:
        """Fighter 객체를 MongoDB document로 변환"""
        doc = {
            "_id": self.document_id,
            "name": self.name,
            "nickname": self.nickname,
            "birthdate": self.birthdate,
            "height": self.height,
            "height_cm": self.height_cm,
            "reach": self.reach,
            "reach_cm": self.reach_cm,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if self.record:
            doc["record"] = self.record.to_dict()
            
        return doc