from typing import Optional
from contextlib import contextmanager
from traceback import format_exc
import logging

import redis

from config import Config

# 로거 설정
LOGGER = logging.getLogger(__name__)

# Redis 클라이언트 생성
redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWORD,
    decode_responses=True,  # 문자열 응답을 자동으로 디코딩
    socket_timeout=Config.REDIS_SOCKET_TIMEOUT,       # 소켓 타임아웃 (초)
    socket_connect_timeout=Config.REDIS_SOCKET_CONNECT_TIMEOUT,  # 연결 타임아웃 (초)
    retry_on_timeout=Config.REDIS_RETRY_ON_TIMEOUT   # 타임아웃 시 재시도
)

@contextmanager
def redis_connection() -> redis.Redis:
    """
    Redis 연결을 관리하는 컨텍스트 매니저
    
    Returns:
        redis.Redis: Redis 클라이언트 인스턴스
    """
    try:
        # Redis 연결 상태 확인
        redis_client.ping()
        yield redis_client
    except redis.ConnectionError as e:
        # 연결 실패 시 새로운 연결 시도
        LOGGER.warning(f"Redis 연결 실패, 재연결 시도 중: {str(e)}")
        LOGGER.debug(format_exc())
        # Redis 연결 재설정
        new_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            password=Config.REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=Config.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=Config.REDIS_SOCKET_CONNECT_TIMEOUT,
            retry_on_timeout=Config.REDIS_RETRY_ON_TIMEOUT
        )
        yield new_client
    except Exception as e:
        LOGGER.error(f"Redis 오류 발생: {str(e)}")
        LOGGER.error(format_exc())
        raise

# Redis 연결 상태 확인 함수
def check_redis_connection() -> bool:
    """
    Redis 연결 상태를 확인합니다.
    
    Returns:
        bool: 연결 성공 시 True, 실패 시 False
    """
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError as e:
        LOGGER.debug(f"Redis connection check failed: {str(e)}")
        return False
    except Exception as e:
        LOGGER.error(f"Unexpected error checking Redis connection: {str(e)}")
        LOGGER.debug(format_exc())
        return False
