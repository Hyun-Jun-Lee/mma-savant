"""
WebSocket Routes 테스트
api/websocket/routes.py의 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from fastapi import HTTPException

from api.websocket.routes import get_user_from_token


class TestGetUserFromToken:
    """get_user_from_token 함수 단위 테스트"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock AsyncSession"""
        return AsyncMock()

    @pytest.fixture
    def mock_user_schema(self):
        """Mock UserSchema"""
        schema = MagicMock()
        schema.id = 1
        schema.email = "test@example.com"
        schema.name = "Test User"
        schema.is_active = True
        return schema

    @pytest.fixture
    def mock_user_model(self):
        """Mock UserModel"""
        model = MagicMock()
        model.id = 1
        model.email = "test@example.com"
        model.name = "Test User"
        model.is_active = True
        return model

    @pytest.fixture
    def mock_token_data_with_user_id(self):
        """user_id가 있는 토큰 데이터 (일반 로그인)"""
        token_data = MagicMock()
        token_data.user_id = 1
        token_data.email = None
        token_data.sub = None
        token_data.name = None
        token_data.picture = None
        return token_data

    @pytest.fixture
    def mock_token_data_with_email(self):
        """email이 있는 토큰 데이터 (OAuth 로그인)"""
        token_data = MagicMock()
        token_data.user_id = None
        token_data.email = "oauth@example.com"
        token_data.sub = "google-oauth-id-123"
        token_data.name = "OAuth User"
        token_data.picture = "https://example.com/picture.jpg"
        return token_data

    @pytest.fixture
    def mock_token_data_with_sub_only(self):
        """sub만 있는 토큰 데이터 (fallback)"""
        token_data = MagicMock()
        token_data.user_id = None
        token_data.email = None
        token_data.sub = "provider-id-456"
        token_data.name = None
        token_data.picture = None
        return token_data

    @pytest.mark.asyncio
    async def test_valid_token_with_user_id_returns_user(
        self, mock_db_session, mock_user_schema, mock_user_model, mock_token_data_with_user_id
    ):
        """유효한 토큰 + user_id → UserModel 반환"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                with patch('api.websocket.routes.UserModel') as mock_user_class:
                    # Mock 설정
                    mock_jwt.decode_token.return_value = mock_token_data_with_user_id
                    mock_jwt.verify_token_expiry.return_value = True
                    mock_repo.get_user_by_id = AsyncMock(return_value=mock_user_schema)
                    mock_user_class.from_schema.return_value = mock_user_model

                    # 실행
                    result = await get_user_from_token("valid_token", mock_db_session)

                    # 검증
                    assert result == mock_user_model
                    mock_jwt.decode_token.assert_called_once_with("valid_token")
                    mock_jwt.verify_token_expiry.assert_called_once()
                    mock_repo.get_user_by_id.assert_called_once_with(mock_db_session, 1)

    @pytest.mark.asyncio
    async def test_valid_token_with_email_existing_user(
        self, mock_db_session, mock_user_schema, mock_user_model, mock_token_data_with_email
    ):
        """유효한 토큰 + email (기존 OAuth 사용자) → UserModel 반환"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                with patch('api.websocket.routes.UserModel') as mock_user_class:
                    mock_jwt.decode_token.return_value = mock_token_data_with_email
                    mock_jwt.verify_token_expiry.return_value = True
                    mock_repo.get_user_by_email = AsyncMock(return_value=mock_user_schema)
                    mock_user_class.from_schema.return_value = mock_user_model

                    result = await get_user_from_token("oauth_token", mock_db_session)

                    assert result == mock_user_model
                    mock_repo.get_user_by_email.assert_called_once_with(
                        mock_db_session, "oauth@example.com"
                    )

    @pytest.mark.asyncio
    async def test_valid_token_with_email_new_user_creates_user(
        self, mock_db_session, mock_user_schema, mock_user_model, mock_token_data_with_email
    ):
        """유효한 토큰 + email (신규 OAuth 사용자) → 사용자 생성 후 반환"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                with patch('api.websocket.routes.UserModel') as mock_user_class:
                    mock_jwt.decode_token.return_value = mock_token_data_with_email
                    mock_jwt.verify_token_expiry.return_value = True
                    # 기존 사용자 없음 → 새로 생성
                    mock_repo.get_user_by_email = AsyncMock(return_value=None)
                    mock_repo.create_oauth_user = AsyncMock(return_value=mock_user_schema)
                    mock_user_class.from_schema.return_value = mock_user_model

                    result = await get_user_from_token("new_oauth_token", mock_db_session)

                    assert result == mock_user_model
                    mock_repo.create_oauth_user.assert_called_once_with(
                        session=mock_db_session,
                        email="oauth@example.com",
                        name="OAuth User",
                        picture="https://example.com/picture.jpg",
                        provider_id="google-oauth-id-123"
                    )

    @pytest.mark.asyncio
    async def test_valid_token_with_sub_only_fallback(
        self, mock_db_session, mock_user_schema, mock_user_model, mock_token_data_with_sub_only
    ):
        """유효한 토큰 + sub만 있음 (fallback) → provider_id로 조회"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                with patch('api.websocket.routes.UserModel') as mock_user_class:
                    mock_jwt.decode_token.return_value = mock_token_data_with_sub_only
                    mock_jwt.verify_token_expiry.return_value = True
                    mock_repo.get_user_by_provider_id = AsyncMock(return_value=mock_user_schema)
                    mock_user_class.from_schema.return_value = mock_user_model

                    result = await get_user_from_token("sub_only_token", mock_db_session)

                    assert result == mock_user_model
                    mock_repo.get_user_by_provider_id.assert_called_once_with(
                        mock_db_session, "provider-id-456"
                    )

    @pytest.mark.asyncio
    async def test_expired_token_raises_http_exception(
        self, mock_db_session, mock_token_data_with_user_id
    ):
        """만료된 토큰 → HTTPException 발생"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            mock_jwt.decode_token.return_value = mock_token_data_with_user_id
            mock_jwt.verify_token_expiry.return_value = False  # 만료됨

            with pytest.raises(HTTPException) as exc_info:
                await get_user_from_token("expired_token", mock_db_session)

            assert exc_info.value.status_code == 401
            assert "Token has expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_not_found_by_user_id_raises_http_exception(
        self, mock_db_session, mock_token_data_with_user_id
    ):
        """user_id로 사용자 조회 실패 → HTTPException 발생"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                mock_jwt.decode_token.return_value = mock_token_data_with_user_id
                mock_jwt.verify_token_expiry.return_value = True
                mock_repo.get_user_by_id = AsyncMock(return_value=None)

                with pytest.raises(HTTPException) as exc_info:
                    await get_user_from_token("valid_token", mock_db_session)

                assert exc_info.value.status_code == 401
                assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_not_found_by_provider_id_raises_http_exception(
        self, mock_db_session, mock_token_data_with_sub_only
    ):
        """provider_id로 사용자 조회 실패 → HTTPException 발생"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                mock_jwt.decode_token.return_value = mock_token_data_with_sub_only
                mock_jwt.verify_token_expiry.return_value = True
                mock_repo.get_user_by_provider_id = AsyncMock(return_value=None)

                with pytest.raises(HTTPException) as exc_info:
                    await get_user_from_token("sub_token", mock_db_session)

                assert exc_info.value.status_code == 401
                assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_inactive_user_raises_http_exception(
        self, mock_db_session, mock_user_schema, mock_token_data_with_user_id
    ):
        """비활성 사용자 → HTTPException 발생"""
        inactive_user_model = MagicMock()
        inactive_user_model.is_active = False

        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                with patch('api.websocket.routes.UserModel') as mock_user_class:
                    mock_jwt.decode_token.return_value = mock_token_data_with_user_id
                    mock_jwt.verify_token_expiry.return_value = True
                    mock_repo.get_user_by_id = AsyncMock(return_value=mock_user_schema)
                    mock_user_class.from_schema.return_value = inactive_user_model

                    with pytest.raises(HTTPException) as exc_info:
                        await get_user_from_token("valid_token", mock_db_session)

                    assert exc_info.value.status_code == 401
                    assert "Inactive user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_jwt_decode_error_raises_http_exception(self, mock_db_session):
        """JWT 디코딩 에러 → HTTPException 발생"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            mock_jwt.decode_token.side_effect = Exception("Invalid token format")

            with pytest.raises(HTTPException) as exc_info:
                await get_user_from_token("invalid_token", mock_db_session)

            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_database_error_raises_http_exception(
        self, mock_db_session, mock_token_data_with_user_id
    ):
        """데이터베이스 에러 → HTTPException 발생"""
        with patch('api.websocket.routes.jwt_handler') as mock_jwt:
            with patch('api.websocket.routes.user_repo') as mock_repo:
                mock_jwt.decode_token.return_value = mock_token_data_with_user_id
                mock_jwt.verify_token_expiry.return_value = True
                mock_repo.get_user_by_id = AsyncMock(
                    side_effect=Exception("Database connection error")
                )

                with pytest.raises(HTTPException) as exc_info:
                    await get_user_from_token("valid_token", mock_db_session)

                assert exc_info.value.status_code == 401
                assert "Authentication failed" in exc_info.value.detail


if __name__ == "__main__":
    print("WebSocket Routes 테스트 실행...")
    print("uv run pytest tests/api/websocket/test_websocket_routes.py -v")
