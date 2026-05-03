"""WSErrorPayload / ErrorCode 단위 테스트"""
import pytest
from common.ws_types import ErrorCode, WSErrorPayload


class TestErrorCode:
    def test_all_codes_are_strings(self):
        for code in ErrorCode:
            assert isinstance(code.value, str)

    def test_known_codes_exist(self):
        assert ErrorCode.USAGE_LIMIT == "USAGE_LIMIT"
        assert ErrorCode.LLM_TIMEOUT == "LLM_TIMEOUT"
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


class TestWSErrorPayload:
    def test_minimal_payload(self):
        payload = WSErrorPayload(error="something broke")
        msg = payload.to_ws_message()
        assert msg["type"] == "error"
        assert msg["error"] == "something broke"
        assert msg["recoverable"] is True
        assert "timestamp" not in msg  # None 제외

    def test_full_payload(self):
        payload = WSErrorPayload(
            error="limit exceeded",
            error_code=ErrorCode.USAGE_LIMIT,
            recoverable=False,
            timestamp="2025-01-01T00:00:00Z",
            message_id="msg-1",
            conversation_id=42,
        )
        msg = payload.to_ws_message()
        assert msg["error_code"] == "USAGE_LIMIT"
        assert msg["recoverable"] is False
        assert msg["timestamp"] == "2025-01-01T00:00:00Z"
        assert msg["message_id"] == "msg-1"
        assert msg["conversation_id"] == 42

    def test_warning_type(self):
        payload = WSErrorPayload(
            type="warning",
            error="save failed",
            error_code=ErrorCode.SAVE_FAILED,
        )
        msg = payload.to_ws_message()
        assert msg["type"] == "warning"
        assert msg["error_code"] == "SAVE_FAILED"

    def test_none_fields_excluded(self):
        payload = WSErrorPayload(error="oops")
        msg = payload.to_ws_message()
        assert "timestamp" not in msg
        assert "message_id" not in msg
        assert "conversation_id" not in msg
        assert "error_code" not in msg

    def test_extra_kwargs_merged(self):
        payload = WSErrorPayload(error="err")
        msg = payload.to_ws_message(extra_field="hello", count=3)
        assert msg["extra_field"] == "hello"
        assert msg["count"] == 3

    def test_recoverable_false_not_excluded(self):
        """recoverable=False는 falsy지만 None이 아니므로 포함되어야 함"""
        payload = WSErrorPayload(error="err", recoverable=False)
        msg = payload.to_ws_message()
        assert msg["recoverable"] is False
