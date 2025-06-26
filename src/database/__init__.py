"""
모든 모델을 올바른 순서로 임포트하여 SQLAlchemy 레지스트리에 등록
"""

# 1. BaseModel 먼저
from common.base_model import BaseModel

# 2. 의존성이 적은 모델부터 (Foreign Key 관계 고려)
from common.models import WeightClassModel
from event.models import EventModel
from fighter.models import FighterModel, RankingModel

from match.models import MatchModel
