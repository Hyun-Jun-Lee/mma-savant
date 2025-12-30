"""
User Services 테스트
user/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
Mock을 사용한 서비스 레이어 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, date

from user import services as user_service
from user.dto import (
    UserCreateDTO, UserLoginDTO, UserProfileDTO, UserUsageDTO,
    UserAuthResponseDTO, UserUsageUpdateDTO, UserStatsDTO
)
from user.models import UserSchema
from user.exceptions import (
    UserNotFoundError, UserValidationError, UserAuthenticationError,
    UserDuplicateError, UserPasswordError, UserUsageLimitError, UserQueryError
)


# ===== 회원가입 테스트 =====

@pytest.mark.asyncio
async def test_signup_user_success():
    """정상적인 회원가입 성공 테스트"""
    # Given: 회원가입 데이터
    mock_session = AsyncMock()
    signup_data = UserCreateDTO(username="testuser", password="Pass123!@#")

    # Mock repository functions
    with patch('user.services.user_repo.get_user_by_username', return_value=None), \
         patch('user.services.user_repo.create_user') as mock_create:

        # Mock created user
        created_user = UserSchema(
            id=1,
            username="testuser",
            password_hash="hashed_password",
            total_requests=0,
            daily_requests=0,
            last_request_date=None,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_create.return_value = created_user

        # When: 회원가입 서비스 호출
        result = await user_service.signup_user(mock_session, signup_data)

        # Then: 성공적인 응답 반환
        assert isinstance(result, UserAuthResponseDTO)
        assert result.success is True
        assert "registered successfully" in result.message
        assert result.user is not None
        assert result.user.username == "testuser"
        assert result.user.total_requests == 0
        assert result.user.daily_requests == 0


@pytest.mark.asyncio
async def test_signup_user_duplicate_username():
    """중복 사용자명으로 회원가입 시도 테스트"""
    # Given: 이미 존재하는 사용자명
    mock_session = AsyncMock()
    signup_data = UserCreateDTO(username="existinguser", password="Pass123!@#")

    existing_user = UserSchema(
        id=1,
        username="existinguser",
        password_hash="existing_hash",
        total_requests=0,
        daily_requests=0,
        last_request_date=None,
        is_active=True
    )

    with patch('user.services.user_repo.get_user_by_username', return_value=existing_user):
        # When & Then: UserDuplicateError 발생
        with pytest.raises(UserDuplicateError) as exc_info:
            await user_service.signup_user(mock_session, signup_data)

        assert "existinguser" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_username_too_short():
    """너무 짧은 사용자명으로 회원가입 테스트 (Pydantic DTO 레벨 검증)"""
    from pydantic import ValidationError

    # When & Then: 너무 짧은 사용자명 - Pydantic DTO에서 검증
    with pytest.raises(ValidationError) as exc_info:
        UserCreateDTO(username="ab", password="Pass123!@#")

    assert "username" in str(exc_info.value)
    assert "at least 3 characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_username_empty():
    """빈 사용자명으로 회원가입 테스트 (Pydantic DTO 레벨 검증)"""
    from pydantic import ValidationError

    # When & Then: 빈 사용자명 - Pydantic DTO에서 검증
    with pytest.raises(ValidationError) as exc_info:
        UserCreateDTO(username="", password="Pass123!@#")

    assert "username" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_username_special_chars():
    """특수문자 포함 사용자명으로 회원가입 테스트"""
    mock_session = AsyncMock()

    # When & Then: 특수문자 포함
    with pytest.raises(UserValidationError, match="letters, numbers, and underscores"):
        await user_service.signup_user(
            mock_session,
            UserCreateDTO(username="user@name", password="Pass123!@#")
        )


@pytest.mark.asyncio
async def test_signup_user_invalid_password_too_short():
    """너무 짧은 비밀번호로 회원가입 테스트"""
    mock_session = AsyncMock()

    # When & Then: 너무 짧은 비밀번호 (8자 미만)
    with pytest.raises(UserValidationError, match="must be at least 8 characters"):
        await user_service.signup_user(
            mock_session,
            UserCreateDTO(username="testuser", password="Pass1!")
        )


@pytest.mark.asyncio
async def test_signup_user_invalid_password_empty():
    """빈 비밀번호로 회원가입 테스트 (Pydantic DTO 레벨 검증)"""
    from pydantic import ValidationError

    # When & Then: 빈 비밀번호 - Pydantic DTO에서 검증
    with pytest.raises(ValidationError) as exc_info:
        UserCreateDTO(username="testuser", password="")

    assert "password" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signup_user_invalid_password_complexity():
    """비밀번호 복잡도 요구사항 미충족 테스트"""
    mock_session = AsyncMock()

    # 8자 이상이지만 복잡도 부족 (소문자만)
    with pytest.raises(UserValidationError, match="at least 3 of"):
        await user_service.signup_user(
            mock_session,
            UserCreateDTO(username="testuser", password="onlylowercase")
        )

    # 대문자와 소문자만 (숫자, 특수문자 없음)
    with pytest.raises(UserValidationError, match="at least 3 of"):
        await user_service.signup_user(
            mock_session,
            UserCreateDTO(username="testuser", password="OnlyLetters")
        )


# ===== 로그인 테스트 =====

@pytest.mark.asyncio
async def test_login_user_success():
    """정상적인 로그인 성공 테스트"""
    # Given: 로그인 데이터
    mock_session = AsyncMock()
    password = "Pass123!@#"
    login_data = UserLoginDTO(username="testuser", password=password)

    # bcrypt로 실제 해시 생성
    hashed_password = user_service._hash_password(password)

    # Mock existing user with correct password hash
    existing_user = UserSchema(
        id=1,
        username="testuser",
        password_hash=hashed_password,
        total_requests=10,
        daily_requests=5,
        last_request_date=datetime.now(),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    with patch('user.services.user_repo.get_user_by_username', return_value=existing_user):
        # When: 로그인 서비스 호출
        result = await user_service.login_user(mock_session, login_data)

        # Then: 성공적인 로그인 응답
        assert isinstance(result, UserAuthResponseDTO)
        assert result.success is True
        assert "logged in successfully" in result.message
        assert result.user.username == "testuser"


@pytest.mark.asyncio
async def test_login_user_not_found():
    """존재하지 않는 사용자 로그인 테스트"""
    # Given: 존재하지 않는 사용자
    mock_session = AsyncMock()
    login_data = UserLoginDTO(username="nonexistentuser", password="Pass123!@#")

    with patch('user.services.user_repo.get_user_by_username', return_value=None):
        # When & Then: UserAuthenticationError 발생
        with pytest.raises(UserAuthenticationError, match="User not found"):
            await user_service.login_user(mock_session, login_data)


@pytest.mark.asyncio
async def test_login_user_wrong_password():
    """잘못된 비밀번호로 로그인 테스트"""
    # Given: 잘못된 비밀번호
    mock_session = AsyncMock()
    correct_password = "CorrectPass123!@#"
    wrong_password = "WrongPass123!@#"

    login_data = UserLoginDTO(username="testuser", password=wrong_password)

    existing_user = UserSchema(
        id=1,
        username="testuser",
        password_hash=user_service._hash_password(correct_password),
        total_requests=0,
        daily_requests=0,
        last_request_date=None,
        is_active=True
    )

    with patch('user.services.user_repo.get_user_by_username', return_value=existing_user):
        # When & Then: UserAuthenticationError 발생
        with pytest.raises(UserAuthenticationError, match="Invalid password"):
            await user_service.login_user(mock_session, login_data)


@pytest.mark.asyncio
async def test_login_user_inactive_account():
    """비활성화된 계정으로 로그인 테스트"""
    # Given: 비활성화된 사용자
    mock_session = AsyncMock()
    password = "Pass123!@#"
    login_data = UserLoginDTO(username="testuser", password=password)

    inactive_user = UserSchema(
        id=1,
        username="testuser",
        password_hash=user_service._hash_password(password),
        total_requests=0,
        daily_requests=0,
        last_request_date=None,
        is_active=False
    )

    with patch('user.services.user_repo.get_user_by_username', return_value=inactive_user):
        # When & Then: UserAuthenticationError 발생
        with pytest.raises(UserAuthenticationError, match="account is deactivated"):
            await user_service.login_user(mock_session, login_data)


# ===== 사용자 프로필 조회 테스트 =====

@pytest.mark.asyncio
async def test_get_user_profile_success():
    """정상적인 프로필 조회 성공 테스트"""
    # Given: 사용자 ID
    mock_session = AsyncMock()
    user_id = 1

    user_data = UserSchema(
        id=1,
        username="testuser",
        password_hash="hashed_password",
        total_requests=25,
        daily_requests=3,
        last_request_date=datetime.now(),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    with patch('user.services.user_repo.get_user_by_id', return_value=user_data):
        # When: 프로필 조회
        result = await user_service.get_user_profile(mock_session, user_id)

        # Then: 프로필 DTO 반환
        assert isinstance(result, UserProfileDTO)
        assert result.id == 1
        assert result.username == "testuser"
        assert result.total_requests == 25
        assert result.daily_requests == 3


@pytest.mark.asyncio
async def test_get_user_profile_not_found():
    """존재하지 않는 사용자 프로필 조회 테스트"""
    # Given: 존재하지 않는 사용자 ID
    mock_session = AsyncMock()
    user_id = 999

    with patch('user.services.user_repo.get_user_by_id', return_value=None):
        # When & Then: UserNotFoundError 발생
        with pytest.raises(UserNotFoundError) as exc_info:
            await user_service.get_user_profile(mock_session, user_id)

        assert "User not found with id: 999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_profile_invalid_id_negative():
    """음수 사용자 ID로 프로필 조회 테스트"""
    mock_session = AsyncMock()

    # When & Then: UserValidationError 발생
    with pytest.raises(UserValidationError, match="must be a positive integer"):
        await user_service.get_user_profile(mock_session, -1)


@pytest.mark.asyncio
async def test_get_user_profile_invalid_id_zero():
    """0으로 프로필 조회 테스트"""
    mock_session = AsyncMock()

    # When & Then: UserValidationError 발생
    with pytest.raises(UserValidationError, match="must be a positive integer"):
        await user_service.get_user_profile(mock_session, 0)


# ===== 사용자 사용량 관리 테스트 =====

@pytest.mark.asyncio
async def test_get_user_usage_success():
    """정상적인 사용량 조회 성공 테스트"""
    # Given: 사용자 ID
    mock_session = AsyncMock()
    user_id = 1

    usage_stats = {
        "user_id": 1,
        "username": "testuser",
        "total_requests": 50,
        "daily_requests": 10,
        "daily_request_limit": 100,
        "last_request_date": datetime.now()
    }

    with patch('user.services.user_repo.get_user_usage_stats', return_value=usage_stats):
        # When: 사용량 조회
        result = await user_service.get_user_usage(mock_session, user_id)

        # Then: 사용량 DTO 반환
        assert isinstance(result, UserUsageDTO)
        assert result.user_id == 1
        assert result.username == "testuser"
        assert result.total_requests == 50
        assert result.daily_requests == 10
        assert result.daily_limit == 100
        assert result.remaining_requests == 90


@pytest.mark.asyncio
async def test_update_user_usage_success():
    """정상적인 사용량 업데이트 성공 테스트"""
    # Given: 사용량 업데이트 데이터
    mock_session = AsyncMock()
    usage_data = UserUsageUpdateDTO(user_id=1, increment_requests=1)

    # Mock current usage (within limit)
    current_usage = UserUsageDTO(
        user_id=1,
        username="testuser",
        total_requests=50,
        daily_requests=10,
        last_request_date=datetime.now(),
        daily_limit=100,
        remaining_requests=90
    )

    updated_user = UserSchema(
        id=1,
        username="testuser",
        password_hash="hash",
        total_requests=51,
        daily_requests=11,
        last_request_date=datetime.now(),
        is_active=True
    )

    with patch('user.services.get_user_usage', side_effect=[current_usage, current_usage]), \
         patch('user.services.user_repo.update_user_usage', return_value=updated_user):

        # When: 사용량 업데이트
        result = await user_service.update_user_usage(mock_session, usage_data)

        # Then: 업데이트된 사용량 반환
        assert isinstance(result, UserUsageDTO)


@pytest.mark.asyncio
async def test_update_user_usage_limit_exceeded():
    """사용량 제한 초과 테스트"""
    # Given: 제한에 도달한 사용량
    mock_session = AsyncMock()
    usage_data = UserUsageUpdateDTO(user_id=1, increment_requests=1)

    # Mock current usage (at limit)
    current_usage = UserUsageDTO(
        user_id=1,
        username="testuser",
        total_requests=150,
        daily_requests=100,
        last_request_date=datetime.now(),
        daily_limit=100,
        remaining_requests=0
    )

    with patch('user.services.get_user_usage', return_value=current_usage):
        # When & Then: UserUsageLimitError 발생
        with pytest.raises(UserUsageLimitError) as exc_info:
            await user_service.update_user_usage(mock_session, usage_data)

        assert "Usage limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_usage_limit_within_limit():
    """사용량 제한 내 확인 테스트"""
    # Given: 제한 내 사용량
    mock_session = AsyncMock()
    user_id = 1

    usage = UserUsageDTO(
        user_id=1,
        username="testuser",
        total_requests=50,
        daily_requests=10,
        last_request_date=datetime.now(),
        daily_limit=100,
        remaining_requests=90
    )

    with patch('user.services.get_user_usage', return_value=usage):
        # When: 제한 확인
        result = await user_service.check_usage_limit(mock_session, user_id)

        # Then: True 반환 (사용 가능)
        assert result is True


@pytest.mark.asyncio
async def test_check_usage_limit_exceeded():
    """사용량 제한 초과 확인 테스트"""
    # Given: 제한 초과 사용량
    mock_session = AsyncMock()
    user_id = 1

    usage = UserUsageDTO(
        user_id=1,
        username="testuser",
        total_requests=150,
        daily_requests=100,
        last_request_date=datetime.now(),
        daily_limit=100,
        remaining_requests=0
    )

    with patch('user.services.get_user_usage', return_value=usage):
        # When: 제한 확인
        result = await user_service.check_usage_limit(mock_session, user_id)

        # Then: False 반환 (사용 불가)
        assert result is False


# ===== 사용자 통계 테스트 =====

@pytest.mark.asyncio
async def test_get_user_stats_success():
    """정상적인 통계 조회 성공 테스트"""
    # Given: Mock 통계 데이터
    mock_session = AsyncMock()

    with patch('user.services.user_repo.get_total_users_count', return_value=100), \
         patch('user.services.user_repo.get_active_users_count', return_value=80), \
         patch('user.services.user_repo.get_today_total_requests', return_value=400):

        # When: 통계 조회
        result = await user_service.get_user_stats(mock_session)

        # Then: 통계 DTO 반환
        assert isinstance(result, UserStatsDTO)
        assert result.total_users == 100
        assert result.active_users == 80
        assert result.total_requests_today == 400
        assert result.average_requests_per_user == 5.0  # 400 / 80


@pytest.mark.asyncio
async def test_get_user_stats_no_active_users():
    """활성 사용자 0명일 때 통계 조회 테스트"""
    # Given: 활성 사용자 없음
    mock_session = AsyncMock()

    with patch('user.services.user_repo.get_total_users_count', return_value=10), \
         patch('user.services.user_repo.get_active_users_count', return_value=0), \
         patch('user.services.user_repo.get_today_total_requests', return_value=0):

        # When: 통계 조회
        result = await user_service.get_user_stats(mock_session)

        # Then: 평균은 0
        assert result.average_requests_per_user == 0.0


# ===== 사용자 계정 관리 테스트 =====

@pytest.mark.asyncio
async def test_deactivate_user_success():
    """정상적인 계정 비활성화 성공 테스트"""
    # Given: 활성 사용자
    mock_session = AsyncMock()
    user_id = 1

    user_data = UserSchema(
        id=1,
        username="testuser",
        password_hash="hash",
        total_requests=0,
        daily_requests=0,
        last_request_date=None,
        is_active=True
    )

    with patch('user.services.user_repo.get_user_by_id', return_value=user_data), \
         patch('user.services.user_repo.deactivate_user', return_value=True):

        # When: 계정 비활성화
        result = await user_service.deactivate_user(mock_session, user_id)

        # Then: True 반환
        assert result is True


@pytest.mark.asyncio
async def test_activate_user_success():
    """정상적인 계정 활성화 성공 테스트"""
    # Given: 비활성 사용자
    mock_session = AsyncMock()
    user_id = 1

    user_data = UserSchema(
        id=1,
        username="testuser",
        password_hash="hash",
        total_requests=0,
        daily_requests=0,
        last_request_date=None,
        is_active=False
    )

    with patch('user.services.user_repo.get_user_by_id', return_value=user_data), \
         patch('user.services.user_repo.activate_user', return_value=True):

        # When: 계정 활성화
        result = await user_service.activate_user(mock_session, user_id)

        # Then: True 반환
        assert result is True


# ===== 비밀번호 유틸리티 함수 테스트 =====

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


# ===== 예외 처리 테스트 =====

@pytest.mark.asyncio
async def test_repository_error_handling():
    """Repository 에러 처리 테스트"""
    mock_session = AsyncMock()

    # Given: repository에서 예외 발생하도록 설정
    with patch('user.services.user_repo.get_user_by_id', side_effect=Exception("Database error")):

        # When & Then: UserQueryError로 래핑되어 발생
        with pytest.raises(UserQueryError, match="User query 'get_user_profile' failed"):
            await user_service.get_user_profile(mock_session, 1)


# ===== 비밀번호 검증 세부 테스트 =====

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


if __name__ == "__main__":
    print("User Services 테스트 실행...")
    print("✅ 사용자 인증 및 사용량 관리 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/user/test_user_services.py -v")
