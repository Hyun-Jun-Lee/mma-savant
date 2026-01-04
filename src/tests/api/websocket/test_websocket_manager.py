"""
WebSocket Manager 테스트
api/websocket/manager.py의 단위 테스트
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from api.websocket.manager import ConnectionManager


class TestProcessToolResult:
    """_process_tool_result 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()

    def test_process_string_input_short(self):
        """짧은 문자열 입력 처리"""
        result = self.manager._process_tool_result("hello world")
        assert result == "hello world"

    def test_process_string_input_long_truncates(self):
        """긴 문자열 입력 시 500자로 제한"""
        long_string = "a" * 600
        result = self.manager._process_tool_result(long_string)

        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")

    def test_process_json_string_to_dict(self):
        """JSON 문자열 → 딕셔너리 파싱"""
        json_str = '{"name": "test", "value": 123}'
        result = self.manager._process_tool_result(json_str)

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_process_dict_removes_timestamp_fields(self):
        """딕셔너리에서 created_at, updated_at 필드 제거"""
        input_dict = {
            "id": 1,
            "name": "Fighter",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00"
        }
        result = self.manager._process_tool_result(input_dict)

        assert "id" in result
        assert "name" in result
        assert "created_at" not in result
        assert "updated_at" not in result

    def test_process_list_removes_timestamp_fields_from_items(self):
        """리스트 내 딕셔너리에서 timestamp 필드 제거"""
        input_list = [
            {"id": 1, "name": "A", "created_at": "2024-01-01"},
            {"id": 2, "name": "B", "updated_at": "2024-01-02"},
            {"id": 3, "name": "C", "created_at": "2024-01-03", "updated_at": "2024-01-04"}
        ]
        result = self.manager._process_tool_result(input_list)

        assert len(result) == 3
        for item in result:
            assert "created_at" not in item
            assert "updated_at" not in item
            assert "id" in item
            assert "name" in item

    def test_process_list_with_non_dict_items(self):
        """리스트 내 비-딕셔너리 항목 유지"""
        input_list = [1, "string", {"key": "value"}, None]
        result = self.manager._process_tool_result(input_list)

        assert result[0] == 1
        assert result[1] == "string"
        assert result[2] == {"key": "value"}
        assert result[3] is None

    def test_process_json_string_to_list(self):
        """JSON 문자열 → 리스트 파싱 및 timestamp 제거"""
        json_str = '[{"id": 1, "created_at": "2024-01-01"}, {"id": 2}]'
        result = self.manager._process_tool_result(json_str)

        assert isinstance(result, list)
        assert len(result) == 2
        assert "created_at" not in result[0]
        assert result[1] == {"id": 2}

    def test_process_invalid_json_returns_original_string(self):
        """유효하지 않은 JSON 문자열 → 원본 문자열 반환"""
        invalid_json = "not a json {string"
        result = self.manager._process_tool_result(invalid_json)

        assert result == invalid_json

    def test_process_invalid_json_long_string_truncates(self):
        """유효하지 않은 긴 JSON 문자열 → 500자 제한"""
        invalid_json = "not a json " + "x" * 600
        result = self.manager._process_tool_result(invalid_json)

        assert len(result) == 503
        assert result.endswith("...")

    def test_process_other_types_returns_string_representation(self):
        """기타 타입 → 문자열 변환"""
        result_int = self.manager._process_tool_result(12345)
        result_float = self.manager._process_tool_result(123.45)
        result_bool = self.manager._process_tool_result(True)

        assert result_int == "12345"
        assert result_float == "123.45"
        assert result_bool == "True"

    def test_process_none_returns_string(self):
        """None 입력 → 'None' 문자열 반환"""
        result = self.manager._process_tool_result(None)
        assert result == "None"

    def test_process_empty_dict(self):
        """빈 딕셔너리 처리"""
        result = self.manager._process_tool_result({})
        assert result == {}

    def test_process_empty_list(self):
        """빈 리스트 처리"""
        result = self.manager._process_tool_result([])
        assert result == []

    def test_process_nested_dict_only_removes_top_level_timestamps(self):
        """중첩 딕셔너리에서 최상위 timestamp만 제거"""
        input_dict = {
            "id": 1,
            "created_at": "2024-01-01",
            "nested": {
                "created_at": "2024-01-02",  # 중첩된 created_at은 유지됨
                "value": "test"
            }
        }
        result = self.manager._process_tool_result(input_dict)

        assert "created_at" not in result  # 최상위 제거
        assert "created_at" in result["nested"]  # 중첩은 유지


class TestValidateMessageData:
    """_validate_message_data 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()
        self.connection_id = "test-connection-id"

    @pytest.mark.asyncio
    async def test_validate_valid_message_with_conversation_id(self):
        """유효한 메시지 데이터 (conversation_id 포함)"""
        message_data = {
            "content": "Hello, world!",
            "conversation_id": 123
        }

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            content, conversation_id = await self.manager._validate_message_data(
                self.connection_id, message_data
            )

        assert content == "Hello, world!"
        assert conversation_id == 123

    @pytest.mark.asyncio
    async def test_validate_valid_message_without_conversation_id(self):
        """유효한 메시지 데이터 (conversation_id 없음)"""
        message_data = {"content": "Hello, world!"}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            content, conversation_id = await self.manager._validate_message_data(
                self.connection_id, message_data
            )

        assert content == "Hello, world!"
        assert conversation_id is None

    @pytest.mark.asyncio
    async def test_validate_empty_content_raises_error(self):
        """빈 content → ValueError 발생"""
        message_data = {"content": ""}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock) as mock_send:
            with pytest.raises(ValueError, match="Message content is required"):
                await self.manager._validate_message_data(self.connection_id, message_data)

            # 에러 메시지가 전송되었는지 확인
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[1]["type"] == "error"
            assert "Message content is required" in call_args[1]["error"]

    @pytest.mark.asyncio
    async def test_validate_whitespace_only_content_raises_error(self):
        """공백만 있는 content → ValueError 발생"""
        message_data = {"content": "   \t\n   "}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock) as mock_send:
            with pytest.raises(ValueError, match="Message content is required"):
                await self.manager._validate_message_data(self.connection_id, message_data)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_missing_content_key_raises_error(self):
        """content 키 없음 → ValueError 발생"""
        message_data = {"other_key": "value"}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            with pytest.raises(ValueError, match="Message content is required"):
                await self.manager._validate_message_data(self.connection_id, message_data)

    @pytest.mark.asyncio
    async def test_validate_content_with_leading_trailing_whitespace_stripped(self):
        """앞뒤 공백이 있는 content → strip 처리"""
        message_data = {"content": "  Hello  "}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            content, _ = await self.manager._validate_message_data(
                self.connection_id, message_data
            )

        assert content == "Hello"

    @pytest.mark.asyncio
    async def test_validate_conversation_id_none_vs_missing(self):
        """conversation_id가 None vs 키 없음 → 둘 다 None 반환"""
        message_data_none = {"content": "test", "conversation_id": None}
        message_data_missing = {"content": "test"}

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            _, conv_id_none = await self.manager._validate_message_data(
                self.connection_id, message_data_none
            )
            _, conv_id_missing = await self.manager._validate_message_data(
                self.connection_id, message_data_missing
            )

        assert conv_id_none is None
        assert conv_id_missing is None


class TestConnect:
    """connect 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()

    def _create_mock_websocket(self, state: str = "CONNECTED"):
        """Mock WebSocket 생성"""
        mock_ws = MagicMock()
        mock_ws.client_state.name = state
        mock_ws.send_text = AsyncMock()
        return mock_ws

    def _create_mock_user(self, user_id: int = 1):
        """Mock UserModel 생성"""
        mock_user = MagicMock()
        mock_user.id = user_id
        return mock_user

    @pytest.mark.asyncio
    async def test_connect_success_returns_connection_id(self):
        """연결 성공 시 connection_id 반환"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()

        connection_id = await self.manager.connect(mock_ws, mock_user)

        assert connection_id is not None
        assert isinstance(connection_id, str)
        assert len(connection_id) == 36  # UUID 형식

    @pytest.mark.asyncio
    async def test_connect_registers_in_active_connections(self):
        """연결 성공 시 active_connections에 등록"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()

        connection_id = await self.manager.connect(mock_ws, mock_user)

        assert connection_id in self.manager.active_connections
        assert self.manager.active_connections[connection_id] == mock_ws

    @pytest.mark.asyncio
    async def test_connect_registers_in_connection_users(self):
        """연결 성공 시 connection_users에 사용자 등록"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user(user_id=42)

        connection_id = await self.manager.connect(mock_ws, mock_user)

        assert connection_id in self.manager.connection_users
        assert self.manager.connection_users[connection_id] == mock_user

    @pytest.mark.asyncio
    async def test_connect_registers_in_user_connections(self):
        """연결 성공 시 user_connections에 연결 ID 등록"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user(user_id=42)

        connection_id = await self.manager.connect(mock_ws, mock_user)

        assert 42 in self.manager.user_connections
        assert connection_id in self.manager.user_connections[42]

    @pytest.mark.asyncio
    async def test_connect_with_conversation_id_registers_in_conversation_connections(self):
        """conversation_id가 있으면 conversation_connections에 등록"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()

        connection_id = await self.manager.connect(mock_ws, mock_user, conversation_id=100)

        assert 100 in self.manager.conversation_connections
        assert connection_id in self.manager.conversation_connections[100]

    @pytest.mark.asyncio
    async def test_connect_without_conversation_id_does_not_register_conversation(self):
        """conversation_id가 없으면 conversation_connections에 등록 안 함"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()

        await self.manager.connect(mock_ws, mock_user, conversation_id=None)

        assert len(self.manager.conversation_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_multiple_connections_same_user(self):
        """같은 사용자가 여러 번 연결"""
        mock_user = self._create_mock_user(user_id=42)

        conn_id_1 = await self.manager.connect(self._create_mock_websocket(), mock_user)
        conn_id_2 = await self.manager.connect(self._create_mock_websocket(), mock_user)

        assert conn_id_1 != conn_id_2
        assert len(self.manager.user_connections[42]) == 2
        assert conn_id_1 in self.manager.user_connections[42]
        assert conn_id_2 in self.manager.user_connections[42]

    @pytest.mark.asyncio
    async def test_connect_websocket_not_connected_raises_error(self):
        """WebSocket 상태가 CONNECTED가 아니면 ConnectionError 발생"""
        mock_ws = self._create_mock_websocket(state="DISCONNECTED")
        mock_user = self._create_mock_user()

        with pytest.raises(ConnectionError, match="WebSocket connection failed"):
            await self.manager.connect(mock_ws, mock_user)


class TestDisconnect:
    """disconnect 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()

    def _create_mock_websocket(self):
        """Mock WebSocket 생성"""
        mock_ws = MagicMock()
        mock_ws.client_state.name = "CONNECTED"
        mock_ws.send_text = AsyncMock()
        return mock_ws

    def _create_mock_user(self, user_id: int = 1):
        """Mock UserModel 생성"""
        mock_user = MagicMock()
        mock_user.id = user_id
        return mock_user

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_active_connections(self):
        """연결 해제 시 active_connections에서 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()
        connection_id = await self.manager.connect(mock_ws, mock_user)

        await self.manager.disconnect(connection_id)

        assert connection_id not in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_connection_users(self):
        """연결 해제 시 connection_users에서 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()
        connection_id = await self.manager.connect(mock_ws, mock_user)

        await self.manager.disconnect(connection_id)

        assert connection_id not in self.manager.connection_users

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_user_connections(self):
        """연결 해제 시 user_connections에서 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user(user_id=42)
        connection_id = await self.manager.connect(mock_ws, mock_user)

        await self.manager.disconnect(connection_id)

        assert connection_id not in self.manager.user_connections.get(42, set())

    @pytest.mark.asyncio
    async def test_disconnect_removes_user_id_when_last_connection(self):
        """사용자의 마지막 연결 해제 시 user_connections에서 user_id 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user(user_id=42)
        connection_id = await self.manager.connect(mock_ws, mock_user)

        await self.manager.disconnect(connection_id)

        assert 42 not in self.manager.user_connections

    @pytest.mark.asyncio
    async def test_disconnect_keeps_user_id_when_other_connections_exist(self):
        """다른 연결이 남아있으면 user_id 유지"""
        mock_user = self._create_mock_user(user_id=42)
        conn_id_1 = await self.manager.connect(self._create_mock_websocket(), mock_user)
        conn_id_2 = await self.manager.connect(self._create_mock_websocket(), mock_user)

        await self.manager.disconnect(conn_id_1)

        assert 42 in self.manager.user_connections
        assert conn_id_2 in self.manager.user_connections[42]
        assert conn_id_1 not in self.manager.user_connections[42]

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_conversation_connections(self):
        """연결 해제 시 conversation_connections에서 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()
        connection_id = await self.manager.connect(mock_ws, mock_user, conversation_id=100)

        await self.manager.disconnect(connection_id)

        assert connection_id not in self.manager.conversation_connections.get(100, set())

    @pytest.mark.asyncio
    async def test_disconnect_removes_conversation_id_when_last_connection(self):
        """대화의 마지막 연결 해제 시 conversation_connections에서 conversation_id 제거"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user()
        connection_id = await self.manager.connect(mock_ws, mock_user, conversation_id=100)

        await self.manager.disconnect(connection_id)

        assert 100 not in self.manager.conversation_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection_does_nothing(self):
        """존재하지 않는 connection_id로 disconnect 시 아무 동작 없음"""
        initial_active = len(self.manager.active_connections)

        await self.manager.disconnect("nonexistent-connection-id")

        assert len(self.manager.active_connections) == initial_active

    @pytest.mark.asyncio
    async def test_disconnect_clears_all_related_state(self):
        """연결 해제 시 관련된 모든 상태 정리 확인"""
        mock_ws = self._create_mock_websocket()
        mock_user = self._create_mock_user(user_id=42)
        connection_id = await self.manager.connect(mock_ws, mock_user, conversation_id=100)

        # 연결 전 상태 확인
        assert connection_id in self.manager.active_connections
        assert connection_id in self.manager.connection_users
        assert 42 in self.manager.user_connections
        assert 100 in self.manager.conversation_connections

        await self.manager.disconnect(connection_id)

        # 연결 후 모든 상태 정리 확인
        assert connection_id not in self.manager.active_connections
        assert connection_id not in self.manager.connection_users
        assert 42 not in self.manager.user_connections
        assert 100 not in self.manager.conversation_connections


class TestValidateUserConnection:
    """_validate_user_connection 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()

    def _create_mock_user(self, user_id: int = 1):
        """Mock UserModel 생성"""
        mock_user = MagicMock()
        mock_user.id = user_id
        return mock_user

    @pytest.mark.asyncio
    async def test_validate_existing_user_returns_user(self):
        """등록된 connection_id로 검증 시 UserModel 반환"""
        mock_user = self._create_mock_user(user_id=42)
        connection_id = "test-connection-id"
        self.manager.connection_users[connection_id] = mock_user

        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
            result = await self.manager._validate_user_connection(connection_id)

        assert result == mock_user
        assert result.id == 42

    @pytest.mark.asyncio
    async def test_validate_nonexistent_user_raises_error(self):
        """등록되지 않은 connection_id로 검증 시 ValueError 발생"""
        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock) as mock_send:
            with pytest.raises(ValueError, match="User not found for connection"):
                await self.manager._validate_user_connection("nonexistent-connection")

            # 에러 메시지가 전송되었는지 확인
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[1]["type"] == "error"
            assert "User not found" in call_args[1]["error"]

    @pytest.mark.asyncio
    async def test_validate_sends_error_message_with_timestamp(self):
        """사용자 없을 때 전송되는 에러 메시지에 timestamp 포함"""
        with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock) as mock_send:
            with pytest.raises(ValueError):
                await self.manager._validate_user_connection("nonexistent")

            call_args = mock_send.call_args[0]
            assert "timestamp" in call_args[1]


class TestCheckUsageLimit:
    """_check_usage_limit 메서드 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 ConnectionManager 인스턴스 생성"""
        self.manager = ConnectionManager()
        self.connection_id = "test-connection-id"

    @pytest.fixture
    def mock_db_session(self):
        """Mock AsyncSession"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_check_usage_within_limit_returns_true(self, mock_db_session):
        """사용량 제한 내 → True 반환"""
        with patch('api.websocket.manager.check_usage_limit', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True

            with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
                result = await self.manager._check_usage_limit(
                    self.connection_id, mock_db_session, user_id=1
                )

            assert result is True
            mock_check.assert_called_once_with(mock_db_session, 1)

    @pytest.mark.asyncio
    async def test_check_usage_exceeded_returns_false_and_sends_message(self, mock_db_session):
        """사용량 초과 시 False 반환 및 클라이언트에 제한 메시지 전송"""
        mock_usage = MagicMock()
        mock_usage.daily_requests = 50
        mock_usage.daily_limit = 50

        with patch('api.websocket.manager.check_usage_limit', new_callable=AsyncMock) as mock_check:
            with patch('api.websocket.manager.get_user_usage', new_callable=AsyncMock) as mock_get_usage:
                mock_check.return_value = False
                mock_get_usage.return_value = mock_usage

                with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock) as mock_send:
                    result = await self.manager._check_usage_limit(
                        self.connection_id, mock_db_session, user_id=1
                    )

                    # 반환값 검증
                    assert result is False

                    # get_user_usage 호출 검증
                    mock_get_usage.assert_called_once_with(mock_db_session, 1)

                    # 클라이언트 메시지 전송 검증
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args[0]
                    assert call_args[1]["type"] == "usage_limit_exceeded"
                    assert call_args[1]["daily_requests"] == 50
                    assert call_args[1]["daily_limit"] == 50
                    assert call_args[1]["remaining_requests"] == 0

    @pytest.mark.asyncio
    async def test_check_usage_error_returns_true_for_service_continuity(self, mock_db_session):
        """사용량 체크 에러 시 서비스 중단 방지를 위해 True 반환"""
        with patch('api.websocket.manager.check_usage_limit', new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = Exception("Database error")

            with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
                result = await self.manager._check_usage_limit(
                    self.connection_id, mock_db_session, user_id=1
                )

            # 에러 발생 시에도 True 반환 (서비스 중단 방지)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_usage_calls_get_user_usage_only_when_exceeded(self, mock_db_session):
        """사용량 초과 시에만 get_user_usage 호출"""
        with patch('api.websocket.manager.check_usage_limit', new_callable=AsyncMock) as mock_check:
            with patch('api.websocket.manager.get_user_usage', new_callable=AsyncMock) as mock_get_usage:
                mock_check.return_value = True  # 제한 내

                with patch.object(self.manager, 'send_to_connection', new_callable=AsyncMock):
                    await self.manager._check_usage_limit(
                        self.connection_id, mock_db_session, user_id=1
                    )

                # 제한 내이면 get_user_usage 호출 안 함
                mock_get_usage.assert_not_called()


if __name__ == "__main__":
    print("WebSocket Manager 테스트 실행...")
    print("uv run pytest tests/api/websocket/test_websocket_manager.py -v")
