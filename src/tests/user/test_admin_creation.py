"""
Admin 사용자 생성 테스트
user/services.py의 create_admin_user_if_needed 함수 테스트
"""
import pytest
from unittest.mock import patch
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel
from user.services import create_admin_user_if_needed, _hash_password, _verify_password


# =============================================================================
# Admin 사용자 생성 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_create_admin_user_success(clean_test_session: AsyncSession):
    """ADMIN_USERNAME, ADMIN_PW 설정 시 admin 계정 생성 성공 테스트"""
    # Given
    admin_username = "test_admin_success"
    admin_password = "AdminPass123!@#"

    @asynccontextmanager
    async def mock_db_context():
        yield clean_test_session

    with patch('database.connection.postgres_conn.get_async_db_context', mock_db_context):
        # When
        result = await create_admin_user_if_needed(admin_username, admin_password)

    # Then
    assert result is True

    query_result = await clean_test_session.execute(
        select(UserModel).where(UserModel.username == admin_username)
    )
    admin_user = query_result.scalar_one_or_none()

    assert admin_user is not None
    assert admin_user.username == admin_username
    assert admin_user.is_admin is True
    assert admin_user.is_active is True
    assert admin_user.daily_request_limit == 10000
    assert _verify_password(admin_password, admin_user.password_hash) is True


@pytest.mark.asyncio
async def test_create_admin_user_skipped_when_no_credentials():
    """ADMIN_USERNAME, ADMIN_PW 미설정 시 생성 건너뜀 테스트"""
    # When
    result = await create_admin_user_if_needed(None, None)

    # Then
    assert result is False


@pytest.mark.asyncio
async def test_create_admin_user_skipped_when_only_username():
    """ADMIN_USERNAME만 설정되고 ADMIN_PW 없을 때 건너뜀 테스트"""
    # When
    result = await create_admin_user_if_needed("test_admin", None)

    # Then
    assert result is False


@pytest.mark.asyncio
async def test_create_admin_user_skipped_when_only_password():
    """ADMIN_PW만 설정되고 ADMIN_USERNAME 없을 때 건너뜀 테스트"""
    # When
    result = await create_admin_user_if_needed(None, "AdminPass123!@#")

    # Then
    assert result is False


@pytest.mark.asyncio
async def test_create_admin_user_skipped_when_already_exists(clean_test_session: AsyncSession):
    """이미 admin 계정이 존재할 때 생성 건너뜀 테스트"""
    # Given: 이미 존재하는 사용자
    existing_username = "existing_admin_user"
    existing_admin = UserModel(
        username=existing_username,
        password_hash=_hash_password("OldPass123!@#"),
        is_active=True,
        is_admin=False,
        daily_request_limit=100
    )
    clean_test_session.add(existing_admin)
    await clean_test_session.flush()

    original_password_hash = existing_admin.password_hash
    original_id = existing_admin.id

    @asynccontextmanager
    async def mock_db_context():
        yield clean_test_session

    # When: 같은 username으로 admin 생성 시도
    with patch('database.connection.postgres_conn.get_async_db_context', mock_db_context):
        result = await create_admin_user_if_needed(existing_username, "NewPass123!@#")

    # Then
    assert result is False

    query_result = await clean_test_session.execute(
        select(UserModel).where(UserModel.username == existing_username)
    )
    admin_user = query_result.scalar_one_or_none()

    assert admin_user is not None
    assert admin_user.id == original_id
    assert admin_user.password_hash == original_password_hash
    assert admin_user.is_admin is False
    assert admin_user.daily_request_limit == 100


@pytest.mark.asyncio
async def test_create_admin_user_with_empty_strings():
    """빈 문자열로 설정 시 건너뜀 테스트"""
    # When
    result = await create_admin_user_if_needed("", "")

    # Then
    assert result is False


@pytest.mark.asyncio
async def test_create_admin_user_handles_db_error():
    """DB 에러 발생 시 False 반환 테스트"""
    # Given: DB 에러 발생하는 mock
    @asynccontextmanager
    async def mock_db_context_error():
        raise Exception("DB connection error")
        yield  # unreachable but needed for generator

    with patch('database.connection.postgres_conn.get_async_db_context', mock_db_context_error):
        # When
        result = await create_admin_user_if_needed("test_admin", "AdminPass123!@#")

    # Then: 에러 처리되어 False 반환
    assert result is False


if __name__ == "__main__":
    print("Admin 사용자 생성 테스트")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/user/test_admin_creation.py -v")
