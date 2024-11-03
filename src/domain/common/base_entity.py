from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

@dataclass
class BaseEntity:
    id: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def update_timestamp(self):
        """엔티티가 갱신될 때 호출하여 updated_at 필드를 현재 시간으로 갱신합니다."""
        self.updated_at = datetime.now()