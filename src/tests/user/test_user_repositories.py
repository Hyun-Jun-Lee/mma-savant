"""
User Repository 통합 테스트
user/repositories.py의 데이터베이스 레이어 함수들에 대한 통합 테스트
실제 테스트 DB를 사용하여 데이터 저장/조회/수정/삭제 검증
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from user import repositories as user_repo
from user.models import UserSchema, UserProfileUpdate


# ===== 기본 사용자 조회 테스트 =====

@pytest.mark.asyncio
async def test_get_user_by_id_success(clean_test_session: AsyncSession):
    """사용자 ID로 조회 성공 테스트"""
    # Given: 사용자 생성
    user_schema = UserSchema(
        username="testuser123",
        password_hash="hashed_password",
        total_requests=10,
        daily_requests=5,
        is_active=True
    )
    created_user = await user_repo.create_user(clean_test_session, user_schema)

    # When: ID로 조회
    found_user = await user_repo.get_user_by_id(clean_test_session, created_user.id)

    # Then: 사용자 정보 일치
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.username == "testuser123"
    assert found_user.total_requests == 10
    assert found_user.daily_requests == 5


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 ID로 조회 시 None 반환"""
    # When: 존재하지 않는 ID로 조회
    result = await user_repo.get_user_by_id(clean_test_session, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_username_success(clean_test_session: AsyncSession):
    """사용자명으로 조회 성공 테스트"""
    # Given: 사용자 생성
    user_schema = UserSchema(
        username="searchuser",
        password_hash="hashed_password",
        total_requests=0,
        daily_requests=0,
        is_active=True
    )
    await user_repo.create_user(clean_test_session, user_schema)

    # When: 사용자명으로 조회
    found_user = await user_repo.get_user_by_username(clean_test_session, "searchuser")

    # Then: 사용자 정보 일치
    assert found_user is not None
    assert found_user.username == "searchuser"


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 사용자명으로 조회 시 None 반환"""
    # When: 존재하지 않는 사용자명으로 조회
    result = await user_repo.get_user_by_username(clean_test_session, "nonexistentuser")

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(clean_test_session: AsyncSession):
    """이메일로 사용자 조회 성공 테스트"""
    # Given: OAuth 사용자 생성
    oauth_user = await user_repo.create_oauth_user(
        clean_test_session,
        email="oauth@test.com",
        name="OAuth User",
        provider_id="google123",
        provider="google"
    )

    # When: 이메일로 조회
    found_user = await user_repo.get_user_by_email(clean_test_session, "oauth@test.com")

    # Then: 사용자 정보 일치
    assert found_user is not None
    assert found_user.email == "oauth@test.com"
    assert found_user.name == "OAuth User"


@pytest.mark.asyncio
async def test_get_user_by_provider_id_success(clean_test_session: AsyncSession):
    """OAuth provider ID로 사용자 조회 성공 테스트"""
    # Given: OAuth 사용자 생성
    await user_repo.create_oauth_user(
        clean_test_session,
        email="provider@test.com",
        name="Provider User",
        provider_id="unique_provider_123",
        provider="google"
    )

    # When: Provider ID로 조회
    found_user = await user_repo.get_user_by_provider_id(clean_test_session, "unique_provider_123")

    # Then: 사용자 정보 일치
    assert found_user is not None
    assert found_user.provider_id == "unique_provider_123"
    assert found_user.email == "provider@test.com"


# ===== 사용자 생성 테스트 =====

@pytest.mark.asyncio
async def test_create_user_success(clean_test_session: AsyncSession):
    """일반 사용자 생성 성공 테스트"""
    # Given: 사용자 스키마
    user_schema = UserSchema(
        username="newuser",
        password_hash="secure_hashed_password",
        total_requests=0,
        daily_requests=0,
        is_active=True
    )

    # When: 사용자 생성
    created_user = await user_repo.create_user(clean_test_session, user_schema)

    # Then: 생성 성공
    assert created_user is not None
    assert created_user.id is not None
    assert created_user.username == "newuser"
    assert created_user.password_hash == "secure_hashed_password"
    assert created_user.is_active is True
    assert created_user.created_at is not None


@pytest.mark.asyncio
async def test_create_oauth_user_success(clean_test_session: AsyncSession):
    """OAuth 사용자 생성 성공 테스트"""
    # When: OAuth 사용자 생성
    oauth_user = await user_repo.create_oauth_user(
        clean_test_session,
        email="new_oauth@test.com",
        name="New OAuth User",
        picture="https://example.com/pic.jpg",
        provider_id="google_new_123",
        provider="google"
    )

    # Then: 생성 성공
    assert oauth_user is not None
    assert oauth_user.id is not None
    assert oauth_user.email == "new_oauth@test.com"
    assert oauth_user.name == "New OAuth User"
    assert oauth_user.picture == "https://example.com/pic.jpg"
    assert oauth_user.provider_id == "google_new_123"
    assert oauth_user.provider == "google"
    assert oauth_user.is_active is True
    assert oauth_user.total_requests == 0
    assert oauth_user.daily_requests == 0


# ===== 사용자 프로필 업데이트 테스트 =====

@pytest.mark.asyncio
async def test_update_user_profile_success(clean_test_session: AsyncSession):
    """사용자 프로필 업데이트 성공 테스트"""
    # Given: 기존 사용자
    user = await user_repo.create_oauth_user(
        clean_test_session,
        email="profile@test.com",
        name="Old Name",
        picture="old_pic.jpg"
    )

    # When: 프로필 업데이트
    profile_update = UserProfileUpdate(
        name="New Name",
        picture="new_pic.jpg"
    )
    updated_user = await user_repo.update_user_profile(
        clean_test_session,
        user.id,
        profile_update
    )

    # Then: 업데이트 성공
    assert updated_user is not None
    assert updated_user.name == "New Name"
    assert updated_user.picture == "new_pic.jpg"
    assert updated_user.updated_at is not None


@pytest.mark.asyncio
async def test_update_user_profile_partial_update(clean_test_session: AsyncSession):
    """사용자 프로필 부분 업데이트 테스트"""
    # Given: 기존 사용자
    user = await user_repo.create_oauth_user(
        clean_test_session,
        email="partial@test.com",
        name="Original Name",
        picture="original_pic.jpg"
    )

    # When: 이름만 업데이트
    profile_update = UserProfileUpdate(name="Updated Name Only")
    updated_user = await user_repo.update_user_profile(
        clean_test_session,
        user.id,
        profile_update
    )

    # Then: 이름만 변경됨
    assert updated_user.name == "Updated Name Only"
    assert updated_user.picture == "original_pic.jpg"


@pytest.mark.asyncio
async def test_update_user_profile_no_changes(clean_test_session: AsyncSession):
    """변경 사항 없이 프로필 업데이트 시 기존 데이터 반환"""
    # Given: 기존 사용자
    user = await user_repo.create_oauth_user(
        clean_test_session,
        email="nochange@test.com",
        name="Same Name"
    )

    # When: 빈 업데이트
    profile_update = UserProfileUpdate()
    result = await user_repo.update_user_profile(
        clean_test_session,
        user.id,
        profile_update
    )

    # Then: 기존 데이터 반환
    assert result is not None
    assert result.name == "Same Name"


# ===== 사용량 업데이트 및 조회 테스트 =====

@pytest.mark.asyncio
async def test_update_user_usage_increment(clean_test_session: AsyncSession):
    """사용자 사용량 증가 테스트 (같은 날에 요청하는 경우)"""
    # Given: 오늘 날짜로 마지막 요청이 있는 사용자 생성
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(
            username="usage_test_user",
            password_hash="hash",
            total_requests=10,
            daily_requests=5,
            last_request_date=datetime.now(),  # 오늘 날짜로 설정해야 daily_requests 유지
            is_active=True
        )
    )

    # When: 사용량 업데이트
    updated_user = await user_repo.update_user_usage(clean_test_session, user.id, increment=3)

    # Then: 사용량 증가 확인
    assert updated_user is not None
    assert updated_user.total_requests == 13  # 10 + 3
    assert updated_user.daily_requests == 8   # 5 + 3 (같은 날이므로 누적)
    assert updated_user.last_request_date is not None


@pytest.mark.asyncio
async def test_update_user_usage_daily_reset(clean_test_session: AsyncSession):
    """날짜가 바뀌면 일일 사용량 리셋 테스트"""
    # Given: 어제 날짜로 사용량이 있는 사용자
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(
            username="daily_reset_user",
            password_hash="hash",
            total_requests=50,
            daily_requests=30,
            last_request_date=datetime.now(timezone.utc) - timedelta(days=2),  # 2일 전
            is_active=True
        )
    )

    # When: 오늘 사용량 업데이트
    updated_user = await user_repo.update_user_usage(clean_test_session, user.id, increment=5)

    # Then: daily_requests 리셋되고 새로 증가
    assert updated_user.total_requests == 55  # 50 + 5
    assert updated_user.daily_requests == 5   # 리셋 후 5
    assert updated_user.last_request_date.date() == datetime.now(timezone.utc).date()


@pytest.mark.asyncio
async def test_get_user_usage_stats_success(clean_test_session: AsyncSession):
    """사용자 사용량 통계 조회 성공 테스트"""
    # Given: 사용자 생성
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(
            username="stats_user",
            password_hash="hash",
            total_requests=100,
            daily_requests=20,
            last_request_date=datetime.now(),
            is_active=True
        )
    )

    # When: 사용량 통계 조회
    stats = await user_repo.get_user_usage_stats(clean_test_session, user.id)

    # Then: 통계 정보 일치
    assert stats is not None
    assert stats["user_id"] == user.id
    assert stats["username"] == "stats_user"
    assert stats["total_requests"] == 100
    assert stats["daily_requests"] == 20
    assert stats["daily_request_limit"] == 100


@pytest.mark.asyncio
async def test_get_user_usage_stats_old_date_reset(clean_test_session: AsyncSession):
    """오래된 날짜의 daily_requests는 0으로 계산"""
    # Given: 오래 전 사용 기록이 있는 사용자
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(
            username="old_usage_user",
            password_hash="hash",
            total_requests=200,
            daily_requests=50,
            last_request_date=datetime.now() - timedelta(days=5),  # 5일 전
            is_active=True
        )
    )

    # When: 사용량 통계 조회
    stats = await user_repo.get_user_usage_stats(clean_test_session, user.id)

    # Then: daily_requests는 0으로 계산됨
    assert stats["daily_requests"] == 0  # 날짜가 바뀌어서 0


# ===== 사용자 카운트 테스트 =====

@pytest.mark.asyncio
async def test_get_active_users_count(clean_test_session: AsyncSession):
    """활성 사용자 수 조회 테스트"""
    # Given: 활성/비활성 사용자 생성
    await user_repo.create_user(clean_test_session, UserSchema(username="active1", password_hash="h", is_active=True))
    await user_repo.create_user(clean_test_session, UserSchema(username="active2", password_hash="h", is_active=True))
    await user_repo.create_user(clean_test_session, UserSchema(username="inactive1", password_hash="h", is_active=False))

    # When: 활성 사용자 수 조회
    count = await user_repo.get_active_users_count(clean_test_session)

    # Then: 활성 사용자만 카운트
    assert count >= 2  # 최소 2명 이상 (다른 테스트에서 생성한 사용자 포함 가능)


@pytest.mark.asyncio
async def test_get_total_users_count(clean_test_session: AsyncSession):
    """전체 사용자 수 조회 테스트"""
    # Given: 여러 사용자 생성
    initial_count = await user_repo.get_total_users_count(clean_test_session)

    await user_repo.create_user(clean_test_session, UserSchema(username="count_test1", password_hash="h", is_active=True))
    await user_repo.create_user(clean_test_session, UserSchema(username="count_test2", password_hash="h", is_active=False))
    await user_repo.create_user(clean_test_session, UserSchema(username="count_test3", password_hash="h", is_active=True))

    # When: 전체 사용자 수 조회
    final_count = await user_repo.get_total_users_count(clean_test_session)

    # Then: 3명 증가
    assert final_count == initial_count + 3


# ===== 사용자 활성화/비활성화 테스트 =====

@pytest.mark.asyncio
async def test_deactivate_user_success(clean_test_session: AsyncSession):
    """사용자 비활성화 성공 테스트"""
    # Given: 활성 사용자
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(username="deactivate_user", password_hash="h", is_active=True)
    )

    # When: 비활성화
    result = await user_repo.deactivate_user(clean_test_session, user.id)

    # Then: 비활성화 성공
    assert result is True

    # 검증: 실제로 비활성화됨
    updated_user = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert updated_user.is_active is False


@pytest.mark.asyncio
async def test_activate_user_success(clean_test_session: AsyncSession):
    """사용자 활성화 성공 테스트"""
    # Given: 비활성 사용자
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(username="activate_user", password_hash="h", is_active=False)
    )

    # When: 활성화
    result = await user_repo.activate_user(clean_test_session, user.id)

    # Then: 활성화 성공
    assert result is True

    # 검증: 실제로 활성화됨
    updated_user = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert updated_user.is_active is True


@pytest.mark.asyncio
async def test_deactivate_nonexistent_user(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 비활성화 시 False 반환"""
    # When: 존재하지 않는 사용자 비활성화
    result = await user_repo.deactivate_user(clean_test_session, 99999)

    # Then: False 반환
    assert result is False


@pytest.mark.asyncio
async def test_activate_nonexistent_user(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 활성화 시 False 반환"""
    # When: 존재하지 않는 사용자 활성화
    result = await user_repo.activate_user(clean_test_session, 99999)

    # Then: False 반환
    assert result is False


# ===== 통합 시나리오 테스트 =====

@pytest.mark.asyncio
async def test_full_user_lifecycle(clean_test_session: AsyncSession):
    """사용자 전체 생명주기 통합 테스트"""
    # 1. 사용자 생성
    user = await user_repo.create_user(
        clean_test_session,
        UserSchema(
            username="lifecycle_user",
            password_hash="secure_hash",
            total_requests=0,
            daily_requests=0,
            is_active=True
        )
    )
    assert user.id is not None

    # 2. 사용자 조회
    found_user = await user_repo.get_user_by_username(clean_test_session, "lifecycle_user")
    assert found_user is not None
    assert found_user.id == user.id

    # 3. 사용량 업데이트
    await user_repo.update_user_usage(clean_test_session, user.id, increment=5)
    updated = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert updated.total_requests == 5
    assert updated.daily_requests == 5

    # 4. 사용자 비활성화
    await user_repo.deactivate_user(clean_test_session, user.id)
    deactivated = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert deactivated.is_active is False

    # 5. 사용자 활성화
    await user_repo.activate_user(clean_test_session, user.id)
    activated = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert activated.is_active is True


if __name__ == "__main__":
    print("User Repository 통합 테스트")
    print("실제 테스트 DB를 사용한 데이터베이스 레이어 검증")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/user/test_user_repositories.py -v")
