"""
모든 모델을 올바른 순서로 임포트하여 SQLAlchemy 레지스트리에 등록
"""

# 1. BaseModel 먼저
from common.base_model import BaseModel

# 2. 의존성이 적은 모델부터 (Foreign Key 관계 고려)
from common.models import WeightClassModel
from event.models import EventModel
from fighter.models import FighterModel, RankingModel

# 3. Match 관련 모델들 (의존성 순서 고려)
from match.models import (
    MatchModel, 
    FighterMatchModel, 
    SigStrMatchStatModel, 
    BasicMatchStatModel
)

# 4. User 관련 모델들
from user.models import UserModel

# 5. Conversation 관련 모델들 (있다면)
try:
    from conversation.models import ConversationModel
except ImportError:
    pass  # 존재하지 않으면 무시
