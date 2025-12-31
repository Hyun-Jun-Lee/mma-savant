"""
User Services 통합 테스트
user/services.py의 비즈니스 로직 레이어에 대한 통합 테스트
실제 테스트 DB를 사용하여 서비스 레이어 검증
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from user import services as user_service
from user import repositories as user_repo
from user.dto import (
    UserCreateDTO, UserLoginDTO, UserProfileDTO, UserUsageDTO,
    UserAuthResponseDTO, UserUsageUpdateDTO, UserStatsDTO
)
from user.models import UserSchema
from user.exceptions import (
    UserNotFoundError, UserValidationError, UserAuthenticationError,
    UserDuplicateError, UserUsageLimitError
)


# =============================================================================
# 헬퍼 함수: 테스트용 사용자 생성
# =============================================================================

def generate_unique_username(prefix: str = "test") -> str:
    """유니크한 사용자명 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    return f"{prefix}_{timestamp}"


async def create_test_user_directly(
    session: AsyncSession,
    username: str = None,
    password: str = "TestPass123!@#",
    is_active: bool = True,
    total_requests: int = 0,
    daily_requests: int = 0,
    last_request_date: datetime = None
) -> object:
    """테스트용 사용자 직접 생성 (repository 사용)"""
    if username is None:
        username = generate_unique_username()

    password_hash = user_service._hash_password(password)
    user_schema = UserSchema(
        username=username,
        password_hash=password_hash,
        total_requests=total_requests,
        daily_requests=daily_requests,
        last_request_date=last_request_date,
        is_active=is_active
    )
    return await user_repo.create_user(session, user_schema)


# =============================================================================
# 회원가입 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_signup_user_success(clean_test_session: AsyncSession):
    """정상적인 회원가입 성공 테스트"""
    # Given: 회원가입 데이터
    username = generate_unique_username("signup")
    signup_data = UserCreateDTO(username=username, password="Pass123!@#")

    # When: 회원가입 서비스 호출
    result = await user_service.signup_user(clean_test_session, signup_data)

    # Then: 성공적인 응답 반환
    assert isinstance(result, UserAuthResponseDTO)
    assert result.success is True
    assert "registered successfully" in result.message
    assert result.user is not None
    assert result.user.username == username
    assert result.user.total_requests == 0
    assert result.user.daily_requests == 0

    # DB에서 생성 확인
    found_user = await user_repo.get_user_by_username(clean_test_session, username)
    assert found_user is not None
    assert found_user.username == username


@pytest.mark.asyncio
async def test_signup_user_duplicate_username(clean_test_session: AsyncSession):
    """중복 사용자명으로 회원가입 시도 테스트"""
    # Given: 이미 존재하는 사용자
    username = generate_unique_username("duplicate")
    await create_test_user_directly(clean_test_session, username=username)

    # When & Then: 같은 사용자명으로 회원가입 시 UserDuplicateError 발생
    signup_data = UserCreateDTO(username=username, password="Pass123!@#")
    with pytest.raises(UserDuplicateError) as exc_info:
        await user_service.signup_user(clean_test_session, signup_data)

    assert username in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_username_too_short(clean_test_session: AsyncSession):
    """너무 짧은 사용자명으로 회원가입 테스트 (Pydantic DTO 레벨 검증)"""
    from pydantic import ValidationError

    # When & Then: 너무 짧은 사용자명 - Pydantic DTO에서 검증
    with pytest.raises(ValidationError) as exc_info:
        UserCreateDTO(username="ab", password="Pass123!@#")

    assert "username" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_username_special_chars(clean_test_session: AsyncSession):
    """특수문자 포함 사용자명으로 회원가입 테스트"""
    # When & Then: 특수문자 포함
    with pytest.raises(UserValidationError, match="letters, numbers, and underscores"):
        await user_service.signup_user(
            clean_test_session,
            UserCreateDTO(username="user@name", password="Pass123!@#")
        )


@pytest.mark.asyncio
async def test_signup_user_invalid_password_too_short(clean_test_session: AsyncSession):
    """너무 짧은 비밀번호로 회원가입 테스트"""
    # When & Then: 너무 짧은 비밀번호 (8자 미만)
    with pytest.raises(UserValidationError, match="must be at least 8 characters"):
        await user_service.signup_user(
            clean_test_session,
            UserCreateDTO(username="testuser", password="Pass1!")
        )


@pytest.mark.asyncio
async def test_signup_user_invalid_password_complexity(clean_test_session: AsyncSession):
    """비밀번호 복잡도 요구사항 미충족 테스트"""
    # 8자 이상이지만 복잡도 부족 (소문자만)
    with pytest.raises(UserValidationError, match="at least 3 of"):
        await user_service.signup_user(
            clean_test_session,
            UserCreateDTO(username="testuser", password="onlylowercase")
        )


# =============================================================================
# 로그인 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_login_user_success(clean_test_session: AsyncSession):
    """정상적인 로그인 성공 테스트"""
    # Given: 사용자 생성
    username = generate_unique_username("login")
    password = "Pass123!@#"
    await create_test_user_directly(clean_test_session, username=username, password=password)

    # When: 로그인 서비스 호출
    login_data = UserLoginDTO(username=username, password=password)
    result = await user_service.login_user(clean_test_session, login_data)

    # Then: 성공적인 로그인 응답
    assert isinstance(result, UserAuthResponseDTO)
    assert result.success is True
    assert "logged in successfully" in result.message
    assert result.user.username == username


@pytest.mark.asyncio
async def test_login_user_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 로그인 테스트"""
    # Given: 존재하지 않는 사용자명
    login_data = UserLoginDTO(username="nonexistentuser", password="Pass123!@#")

    # When & Then: UserAuthenticationError 발생
    with pytest.raises(UserAuthenticationError, match="User not found"):
        await user_service.login_user(clean_test_session, login_data)


@pytest.mark.asyncio
async def test_login_user_wrong_password(clean_test_session: AsyncSession):
    """잘못된 비밀번호로 로그인 테스트"""
    # Given: 사용자 생성
    username = generate_unique_username("wrongpw")
    await create_test_user_directly(clean_test_session, username=username, password="CorrectPass123!@#")

    # When & Then: 잘못된 비밀번호로 로그인 시 UserAuthenticationError 발생
    login_data = UserLoginDTO(username=username, password="WrongPass123!@#")
    with pytest.raises(UserAuthenticationError, match="Invalid password"):
        await user_service.login_user(clean_test_session, login_data)


@pytest.mark.asyncio
async def test_login_user_inactive_account(clean_test_session: AsyncSession):
    """비활성화된 계정으로 로그인 테스트"""
    # Given: 비활성화된 사용자
    username = generate_unique_username("inactive")
    password = "Pass123!@#"
    await create_test_user_directly(clean_test_session, username=username, password=password, is_active=False)

    # When & Then: 비활성화된 계정 로그인 시 UserAuthenticationError 발생
    login_data = UserLoginDTO(username=username, password=password)
    with pytest.raises(UserAuthenticationError, match="account is deactivated"):
        await user_service.login_user(clean_test_session, login_data)


# =============================================================================
# 사용자 프로필 조회 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_profile_success(clean_test_session: AsyncSession):
    """정상적인 프로필 조회 성공 테스트"""
    # Given: 사용자 생성
    username = generate_unique_username("profile")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=25,
        daily_requests=3
    )

    # When: 프로필 조회
    result = await user_service.get_user_profile(clean_test_session, user.id)

    # Then: 프로필 DTO 반환
    assert isinstance(result, UserProfileDTO)
    assert result.id == user.id
    assert result.username == username
    assert result.total_requests == 25
    assert result.daily_requests == 3


@pytest.mark.asyncio
async def test_get_user_profile_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 프로필 조회 테스트"""
    # When & Then: UserNotFoundError 발생
    with pytest.raises(UserNotFoundError) as exc_info:
        await user_service.get_user_profile(clean_test_session, 99999)

    assert "User not found with id: 99999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_profile_invalid_id_negative(clean_test_session: AsyncSession):
    """음수 사용자 ID로 프로필 조회 테스트"""
    # When & Then: UserValidationError 발생
    with pytest.raises(UserValidationError, match="must be a positive integer"):
        await user_service.get_user_profile(clean_test_session, -1)


@pytest.mark.asyncio
async def test_get_user_profile_invalid_id_zero(clean_test_session: AsyncSession):
    """0으로 프로필 조회 테스트"""
    # When & Then: UserValidationError 발생
    with pytest.raises(UserValidationError, match="must be a positive integer"):
        await user_service.get_user_profile(clean_test_session, 0)


# =============================================================================
# 사용자 사용량 관리 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_usage_success(clean_test_session: AsyncSession):
    """정상적인 사용량 조회 성공 테스트"""
    # Given: 사용자 생성 (오늘 날짜로 마지막 요청)
    username = generate_unique_username("usage")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=50,
        daily_requests=10,
        last_request_date=datetime.now()
    )

    # When: 사용량 조회
    result = await user_service.get_user_usage(clean_test_session, user.id)

    # Then: 사용량 DTO 반환
    assert isinstance(result, UserUsageDTO)
    assert result.user_id == user.id
    assert result.username == username
    assert result.total_requests == 50
    assert result.daily_requests == 10
    assert result.daily_limit == 100  # 기본 제한
    assert result.remaining_requests == 90  # 100 - 10


@pytest.mark.asyncio
async def test_update_user_usage_success(clean_test_session: AsyncSession):
    """정상적인 사용량 업데이트 성공 테스트"""
    # Given: 사용자 생성
    username = generate_unique_username("update_usage")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=50,
        daily_requests=10,
        last_request_date=datetime.now()
    )

    # When: 사용량 업데이트
    usage_data = UserUsageUpdateDTO(user_id=user.id, increment_requests=5)
    result = await user_service.update_user_usage(clean_test_session, usage_data)

    # Then: 업데이트된 사용량 반환
    assert isinstance(result, UserUsageDTO)
    assert result.total_requests == 55  # 50 + 5
    assert result.daily_requests == 15  # 10 + 5


@pytest.mark.asyncio
async def test_update_user_usage_limit_exceeded(clean_test_session: AsyncSession):
    """사용량 제한 초과 테스트"""
    # Given: 제한에 가까운 사용량을 가진 사용자
    username = generate_unique_username("limit_exceed")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=150,
        daily_requests=99,  # 기본 제한 100에서 1 남음
        last_request_date=datetime.now()
    )

    # When & Then: 제한 초과 시 UserUsageLimitError 발생
    usage_data = UserUsageUpdateDTO(user_id=user.id, increment_requests=5)  # 99 + 5 = 104 > 100
    with pytest.raises(UserUsageLimitError) as exc_info:
        await user_service.update_user_usage(clean_test_session, usage_data)

    assert "Usage limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_usage_limit_within_limit(clean_test_session: AsyncSession):
    """사용량 제한 내 확인 테스트"""
    # Given: 제한 내 사용량을 가진 사용자
    username = generate_unique_username("within_limit")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=50,
        daily_requests=10,
        last_request_date=datetime.now()
    )

    # When: 제한 확인
    result = await user_service.check_usage_limit(clean_test_session, user.id)

    # Then: True 반환 (사용 가능)
    assert result is True


@pytest.mark.asyncio
async def test_check_usage_limit_exceeded(clean_test_session: AsyncSession):
    """사용량 제한 초과 확인 테스트"""
    # Given: 제한 초과 사용량을 가진 사용자
    username = generate_unique_username("exceeded_limit")
    user = await create_test_user_directly(
        clean_test_session,
        username=username,
        total_requests=150,
        daily_requests=100,  # 기본 제한 도달
        last_request_date=datetime.now()
    )

    # When: 제한 확인
    result = await user_service.check_usage_limit(clean_test_session, user.id)

    # Then: False 반환 (사용 불가)
    assert result is False


# =============================================================================
# 사용자 통계 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_stats_success(clean_test_session: AsyncSession):
    """정상적인 통계 조회 성공 테스트"""
    # Given: 여러 사용자 생성
    for i in range(3):
        await create_test_user_directly(
            clean_test_session,
            username=generate_unique_username(f"stats{i}"),
            is_active=True
        )

    # When: 통계 조회
    result = await user_service.get_user_stats(clean_test_session)

    # Then: 통계 DTO 반환
    assert isinstance(result, UserStatsDTO)
    assert result.total_users >= 3
    assert result.active_users >= 3


# =============================================================================
# 사용자 계정 관리 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_deactivate_user_success(clean_test_session: AsyncSession):
    """정상적인 계정 비활성화 성공 테스트"""
    # Given: 활성 사용자
    username = generate_unique_username("deactivate")
    user = await create_test_user_directly(clean_test_session, username=username, is_active=True)

    # When: 계정 비활성화
    result = await user_service.deactivate_user(clean_test_session, user.id)

    # Then: True 반환
    assert result is True

    # 검증: 실제로 비활성화됨
    updated_user = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert updated_user.is_active is False


@pytest.mark.asyncio
async def test_activate_user_success(clean_test_session: AsyncSession):
    """정상적인 계정 활성화 성공 테스트"""
    # Given: 비활성 사용자
    username = generate_unique_username("activate")
    user = await create_test_user_directly(clean_test_session, username=username, is_active=False)

    # When: 계정 활성화
    result = await user_service.activate_user(clean_test_session, user.id)

    # Then: True 반환
    assert result is True

    # 검증: 실제로 활성화됨
    updated_user = await user_repo.get_user_by_id(clean_test_session, user.id)
    assert updated_user.is_active is True


@pytest.mark.asyncio
async def test_deactivate_nonexistent_user(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 비활성화 테스트"""
    # When & Then: UserNotFoundError 발생
    with pytest.raises(UserNotFoundError):
        await user_service.deactivate_user(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_activate_nonexistent_user(clean_test_session: AsyncSession):
    """존재하지 않는 사용자 활성화 테스트"""
    # When & Then: UserNotFoundError 발생
    with pytest.raises(UserNotFoundError):
        await user_service.activate_user(clean_test_session, 99999)


# =============================================================================
# 비밀번호 유틸리티 함수 테스트 (순수 함수, Mock 불필요)
# =============================================================================

def test_hash_password_creates_different_hashes():
    """같은 비밀번호도 bcrypt는 매번 다른 해시 생성"""
    # Given: 평문 비밀번호
    password = "TestPassword123!@#"

    # When: 같은 비밀번호를 두 번 해싱
    hashed1 = user_service._hash_password(password)
    hashed2 = user_service._hash_password(password)

    # Then: 다른 해시값 생성 (bcrypt의 salt 때문)
    assert hashed1 != hashed2
    assert hashed1 != password
    assert hashed2 != password


def test_verify_password_with_correct_password():
    """올바른 비밀번호 검증 성공 테스트"""
    # Given: 평문 비밀번호와 해시
    password = "TestPassword123!@#"
    correct_hash = user_service._hash_password(password)

    # When & Then: 검증 성공
    assert user_service._verify_password(password, correct_hash) is True


def test_verify_password_with_wrong_password():
    """잘못된 비밀번호 검증 실패 테스트"""
    # Given: 평문 비밀번호와 다른 비밀번호의 해시
    password = "CorrectPassword123!@#"
    wrong_password = "WrongPassword123!@#"
    password_hash = user_service._hash_password(password)

    # When & Then: 검증 실패
    assert user_service._verify_password(wrong_password, password_hash) is False


def test_verify_password_with_different_hash():
    """같은 비밀번호지만 다른 해시로 검증 테스트"""
    # Given: 같은 비밀번호의 두 개 해시
    password = "SamePassword123!@#"
    hash1 = user_service._hash_password(password)
    hash2 = user_service._hash_password(password)

    # Then: 두 해시 모두 같은 비밀번호 검증 성공
    assert user_service._verify_password(password, hash1) is True
    assert user_service._verify_password(password, hash2) is True


# =============================================================================
# 비밀번호 검증 세부 테스트 (순수 함수)
# =============================================================================

def test_validate_password_length_requirements():
    """비밀번호 길이 요구사항 테스트"""
    # 8자 미만 - 실패
    with pytest.raises(UserValidationError, match="at least 8 characters"):
        user_service._validate_password("Pass1!")

    # 8자 정확히 (복잡도 충족) - 성공
    user_service._validate_password("Pass123!")  # 대소문자, 숫자, 특수문자

    # 100자 초과 - 실패
    with pytest.raises(UserValidationError, match="not exceed 100 characters"):
        user_service._validate_password("P" + "a" * 100 + "1!")


def test_validate_password_complexity_requirements():
    """비밀번호 복잡도 요구사항 테스트 (3가지 이상)"""
    # 소문자 + 대문자 + 숫자 (3가지) - 성공
    user_service._validate_password("Password123")

    # 소문자 + 대문자 + 특수문자 (3가지) - 성공
    user_service._validate_password("Password!@#")

    # 소문자 + 숫자 + 특수문자 (3가지) - 성공
    user_service._validate_password("password123!@#")

    # 대문자 + 숫자 + 특수문자 (3가지) - 성공
    user_service._validate_password("PASSWORD123!@#")

    # 모두 포함 (4가지) - 성공
    user_service._validate_password("Password123!@#")

    # 소문자만 - 실패
    with pytest.raises(UserValidationError, match="at least 3 of"):
        user_service._validate_password("onlylowercase")

    # 소문자 + 대문자 (2가지) - 실패
    with pytest.raises(UserValidationError, match="at least 3 of"):
        user_service._validate_password("OnlyLetters")

    # 소문자 + 숫자 (2가지) - 실패
    with pytest.raises(UserValidationError, match="at least 3 of"):
        user_service._validate_password("lowercase123")


def test_validate_username_requirements():
    """사용자명 검증 요구사항 테스트"""
    # 3자 이상 - 성공
    user_service._validate_username("abc")

    # 50자 이하 - 성공
    user_service._validate_username("a" * 50)

    # 영문, 숫자, 언더스코어만 - 성공
    user_service._validate_username("valid_user_123")

    # 2자 이하 - 실패
    with pytest.raises(UserValidationError, match="at least 3 characters"):
        user_service._validate_username("ab")

    # 51자 이상 - 실패
    with pytest.raises(UserValidationError, match="not exceed 50 characters"):
        user_service._validate_username("a" * 51)

    # 특수문자 포함 - 실패
    with pytest.raises(UserValidationError, match="letters, numbers, and underscores"):
        user_service._validate_username("user@name")

    # 공백 - 실패
    with pytest.raises(UserValidationError, match="cannot be empty"):
        user_service._validate_username("   ")


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_full_user_lifecycle(clean_test_session: AsyncSession):
    """사용자 전체 생명주기 통합 테스트"""
    # 1. 회원가입
    username = generate_unique_username("lifecycle")
    signup_data = UserCreateDTO(username=username, password="TestPass123!@#")
    signup_result = await user_service.signup_user(clean_test_session, signup_data)
    assert signup_result.success is True
    user_id = signup_result.user.id

    # 2. 로그인
    login_data = UserLoginDTO(username=username, password="TestPass123!@#")
    login_result = await user_service.login_user(clean_test_session, login_data)
    assert login_result.success is True

    # 3. 프로필 조회
    profile = await user_service.get_user_profile(clean_test_session, user_id)
    assert profile.username == username
    assert profile.total_requests == 0

    # 4. 사용량 업데이트
    usage_update = UserUsageUpdateDTO(user_id=user_id, increment_requests=5)
    updated_usage = await user_service.update_user_usage(clean_test_session, usage_update)
    assert updated_usage.total_requests == 5
    assert updated_usage.daily_requests == 5

    # 5. 사용량 제한 확인
    can_use = await user_service.check_usage_limit(clean_test_session, user_id)
    assert can_use is True

    # 6. 계정 비활성화
    await user_service.deactivate_user(clean_test_session, user_id)

    # 7. 비활성화된 계정으로 로그인 시도 실패
    with pytest.raises(UserAuthenticationError, match="account is deactivated"):
        await user_service.login_user(clean_test_session, login_data)

    # 8. 계정 활성화
    await user_service.activate_user(clean_test_session, user_id)

    # 9. 다시 로그인 성공
    relogin_result = await user_service.login_user(clean_test_session, login_data)
    assert relogin_result.success is True


@pytest.mark.asyncio
async def test_signup_and_login_workflow(clean_test_session: AsyncSession):
    """회원가입 후 로그인 워크플로우 테스트"""
    # Given: 회원가입
    username = generate_unique_username("workflow")
    password = "WorkflowPass123!@#"
    signup_data = UserCreateDTO(username=username, password=password)
    await user_service.signup_user(clean_test_session, signup_data)

    # When: 같은 비밀번호로 로그인
    login_data = UserLoginDTO(username=username, password=password)
    result = await user_service.login_user(clean_test_session, login_data)

    # Then: 로그인 성공
    assert result.success is True
    assert result.user.username == username


if __name__ == "__main__":
    print("User Services 통합 테스트")
    print("실제 테스트 DB를 사용한 서비스 레이어 검증")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/user/test_user_services.py -v")
