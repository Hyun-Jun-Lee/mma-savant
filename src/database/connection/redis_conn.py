from typing import Optional
from contextlib import contextmanager

import redis

from config import Config

# Redis 클라이언트 생성
redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWORD,
    decode_responses=True,  # 문자열 응답을 자동으로 디코딩
    socket_timeout=5,       # 소켓 타임아웃 (초)
    socket_connect_timeout=5,  # 연결 타임아웃 (초)
    retry_on_timeout=True   # 타임아웃 시 재시도
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
        print(f"Redis 연결 실패, 재연결 시도 중: {str(e)}")
        # Redis 연결 재설정
        new_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            password=Config.REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        yield new_client
    except Exception as e:
        print(f"Redis 오류 발생: {str(e)}")
        raise e

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
    except:
        return False
