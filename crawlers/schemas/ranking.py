from pydantic import ConfigDict

from schemas.base import BaseSchema

class Ranking(BaseSchema):
    fighter_id: int
    ranking: int = None
    weight_class: str = None
    
    model_config = ConfigDict(from_attributes=True)