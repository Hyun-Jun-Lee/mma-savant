"""WebSocket 에러 응답 표준 타입"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    USAGE_LIMIT = "USAGE_LIMIT"
    USAGE_CHECK_FAILED = "USAGE_CHECK_FAILED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    COMPRESSION_FAILED = "COMPRESSION_FAILED"
    SAVE_FAILED = "SAVE_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WSErrorPayload(BaseModel):
    type: str = "error"
    error: str
    error_code: Optional[str] = None
    recoverable: bool = True
    timestamp: Optional[str] = None
    message_id: Optional[str] = None
    conversation_id: Optional[int] = None

    def to_ws_message(self, **extra) -> dict:
        """프론트엔드 호환 dict 생성. None 값 제외, extra kwargs 병합."""
        data = {k: v for k, v in self.model_dump().items() if v is not None}
        if extra:
            data.update(extra)
        return data
