"""
User Services 테스트
user/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
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


class TestUserSignup:
    """사용자 회원가입 테스트"""
    
    @pytest.mark.asyncio
    async def test_signup_user_success(self):
        """정상적인 회원가입 테스트"""
        # Given: 회원가입 데이터
        mock_session = AsyncMock()
        signup_data = UserCreateDTO(username="testuser", password="password123")
        
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
    async def test_signup_user_duplicate_username(self):
        """중복 사용자명으로 회원가입 시도 테스트"""
        # Given: 이미 존재하는 사용자명
        mock_session = AsyncMock()
        signup_data = UserCreateDTO(username="existinguser", password="password123")
        
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
    async def test_signup_user_invalid_username(self):
        """잘못된 사용자명으로 회원가입 테스트"""
        mock_session = AsyncMock()
        
        # 너무 짧은 사용자명
        with pytest.raises(UserValidationError, match="must be at least 3 characters"):
            await user_service.signup_user(mock_session, UserCreateDTO(username="ab", password="password123"))
        
        # 빈 사용자명
        with pytest.raises(UserValidationError, match="cannot be empty"):
            await user_service.signup_user(mock_session, UserCreateDTO(username="", password="password123"))
        
        # 특수문자 포함
        with pytest.raises(UserValidationError, match="letters, numbers, and underscores"):
            await user_service.signup_user(mock_session, UserCreateDTO(username="user@name", password="password123"))
    
    @pytest.mark.asyncio
    async def test_signup_user_invalid_password(self):
        """잘못된 비밀번호로 회원가입 테스트"""
        mock_session = AsyncMock()
        
        # 너무 짧은 비밀번호
        with pytest.raises(UserValidationError, match="must be at least 6 characters"):
            await user_service.signup_user(mock_session, UserCreateDTO(username="testuser", password="12345"))
        
        # 빈 비밀번호
        with pytest.raises(UserValidationError, match="cannot be empty"):
            await user_service.signup_user(mock_session, UserCreateDTO(username="testuser", password=""))


class TestUserLogin:
    """사용자 로그인 테스트"""
    
    @pytest.mark.asyncio
    async def test_login_user_success(self):
        """정상적인 로그인 테스트"""
        # Given: 로그인 데이터
        mock_session = AsyncMock()
        login_data = UserLoginDTO(username="testuser", password="password123")
        
        # Mock existing user with correct password hash
        existing_user = UserSchema(
            id=1,
            username="testuser",
            password_hash=user_service._hash_password("password123"),
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
    async def test_login_user_not_found(self):
        """존재하지 않는 사용자 로그인 테스트"""
        # Given: 존재하지 않는 사용자
        mock_session = AsyncMock()
        login_data = UserLoginDTO(username="nonexistentuser", password="password123")
        
        with patch('user.services.user_repo.get_user_by_username', return_value=None):
            # When & Then: UserAuthenticationError 발생
            with pytest.raises(UserAuthenticationError, match="User not found"):
                await user_service.login_user(mock_session, login_data)
    
    @pytest.mark.asyncio
    async def test_login_user_wrong_password(self):
        """잘못된 비밀번호로 로그인 테스트"""
        # Given: 잘못된 비밀번호
        mock_session = AsyncMock()
        login_data = UserLoginDTO(username="testuser", password="wrongpassword")
        
        existing_user = UserSchema(
            id=1,
            username="testuser",
            password_hash=user_service._hash_password("correctpassword"),
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
    async def test_login_user_inactive_account(self):
        """비활성화된 계정으로 로그인 테스트"""
        # Given: 비활성화된 사용자
        mock_session = AsyncMock()
        login_data = UserLoginDTO(username="testuser", password="password123")
        
        inactive_user = UserSchema(
            id=1,
            username="testuser",
            password_hash=user_service._hash_password("password123"),
            total_requests=0,
            daily_requests=0,
            last_request_date=None,
            is_active=False
        )
        
        with patch('user.services.user_repo.get_user_by_username', return_value=inactive_user):
            # When & Then: UserAuthenticationError 발생
            with pytest.raises(UserAuthenticationError, match="account is deactivated"):
                await user_service.login_user(mock_session, login_data)


class TestUserProfile:
    """사용자 프로필 조회 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self):
        """정상적인 프로필 조회 테스트"""
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
    async def test_get_user_profile_not_found(self):
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
    async def test_get_user_profile_invalid_id(self):
        """잘못된 사용자 ID로 프로필 조회 테스트"""
        mock_session = AsyncMock()
        
        # When & Then: UserValidationError 발생
        with pytest.raises(UserValidationError, match="must be a positive integer"):
            await user_service.get_user_profile(mock_session, -1)
        
        with pytest.raises(UserValidationError, match="must be a positive integer"):
            await user_service.get_user_profile(mock_session, 0)


class TestUserUsage:
    """사용자 사용량 관리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_user_usage_success(self):
        """정상적인 사용량 조회 테스트"""
        # Given: 사용자 ID
        mock_session = AsyncMock()
        user_id = 1
        
        usage_stats = {
            "user_id": 1,
            "username": "testuser",
            "total_requests": 50,
            "daily_requests": 10,
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
    async def test_update_user_usage_success(self):
        """정상적인 사용량 업데이트 테스트"""
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
    async def test_update_user_usage_limit_exceeded(self):
        """사용량 제한 초과 테스트"""
        # Given: 제한에 근접한 사용량
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
    async def test_check_usage_limit_within_limit(self):
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
    async def test_check_usage_limit_exceeded(self):
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


class TestUserStats:
    """사용자 통계 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_user_stats_success(self):
        """정상적인 통계 조회 테스트"""
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


class TestUserAccountManagement:
    """사용자 계정 관리 테스트"""
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self):
        """정상적인 계정 비활성화 테스트"""
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
    async def test_activate_user_success(self):
        """정상적인 계정 활성화 테스트"""
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


class TestPasswordUtils:
    """비밀번호 유틸리티 함수 테스트"""
    
    def test_hash_password(self):
        """비밀번호 해싱 테스트"""
        # Given: 평문 비밀번호
        password = "testpassword123"
        
        # When: 비밀번호 해싱
        hashed1 = user_service._hash_password(password)
        hashed2 = user_service._hash_password(password)
        
        # Then: 같은 결과 반환
        assert hashed1 == hashed2
        assert hashed1 != password
        assert len(hashed1) == 64  # SHA256 해시 길이
    
    def test_verify_password(self):
        """비밀번호 검증 테스트"""
        # Given: 평문 비밀번호와 해시
        password = "testpassword123"
        correct_hash = user_service._hash_password(password)
        wrong_hash = user_service._hash_password("wrongpassword")
        
        # When & Then: 검증 결과
        assert user_service._verify_password(password, correct_hash) is True
        assert user_service._verify_password(password, wrong_hash) is False
        assert user_service._verify_password("wrongpassword", correct_hash) is False


class TestUserServicesErrorHandling:
    """User Services 예외 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self):
        """Repository 에러 처리 테스트"""
        mock_session = AsyncMock()
        
        # Given: repository에서 예외 발생하도록 설정
        with patch('user.services.user_repo.get_user_by_id', side_effect=Exception("Database error")):
            
            # When & Then: UserQueryError로 래핑되어 발생
            with pytest.raises(UserQueryError, match="User query 'get_user_profile' failed"):
                await user_service.get_user_profile(mock_session, 1)


if __name__ == "__main__":
    print("User Services 테스트 실행...")
    print("✅ 사용자 인증 및 사용량 관리 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/user/test_user_services.py -v")