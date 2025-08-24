"""
성능 모니터링 및 메트릭 수집
LangSmith 트레이싱, 실행 시간 측정, 에러 로깅을 담당
"""
import time
import functools
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field

from config import Config
from common.logging_config import get_logger
from common.utils import kr_time_now

LOGGER = get_logger(__name__)


@dataclass
class TimingMetric:
    """실행 시간 메트릭"""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self) -> float:
        """메트릭 종료 및 시간 계산"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
        return self.duration


@dataclass
class PerformanceSession:
    """성능 측정 세션"""
    session_id: str
    message_id: str
    user_id: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    metrics: List[TimingMetric] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_metric(self, operation: str, duration: float, **metadata) -> None:
        """메트릭 추가"""
        metric = TimingMetric(
            operation=operation,
            start_time=self.start_time,
            end_time=self.start_time + duration,
            duration=duration,
            metadata=metadata
        )
        self.metrics.append(metric)
    
    def get_total_duration(self) -> float:
        """총 실행 시간"""
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """성능 요약"""
        total_duration = self.get_total_duration()
        
        return {
            "session_id": self.session_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "total_duration": total_duration,
            "metrics_count": len(self.metrics),
            "operations": [m.operation for m in self.metrics],
            "slowest_operation": self._get_slowest_operation(),
            "metadata": self.metadata
        }
    
    def _get_slowest_operation(self) -> Optional[Dict[str, Any]]:
        """가장 느린 작업 찾기"""
        if not self.metrics:
            return None
        
        slowest = max(self.metrics, key=lambda m: m.duration or 0)
        return {
            "operation": slowest.operation,
            "duration": slowest.duration,
            "metadata": slowest.metadata
        }


# 글로벌 성능 세션 저장소
_performance_sessions: Dict[str, PerformanceSession] = {}


def setup_langsmith_tracing():
    """LangSmith 추적 설정 및 로깅"""
    try:
        if Config.LANGCHAIN_TRACING_V2:
            LOGGER.info(f"✅ LangSmith tracing enabled for project: {Config.LANGCHAIN_PROJECT}")
            
            # API 키 확인
            if not Config.LANGCHAIN_API_KEY:
                LOGGER.warning("⚠️ LANGCHAIN_API_KEY is not set - tracing may not work properly")
            else:
                LOGGER.debug("🔑 LangSmith API key configured")
            
            # 엔드포인트 확인
            LOGGER.debug(f"🌐 LangSmith endpoint: {Config.LANGCHAIN_ENDPOINT}")
            
            return True
        else:
            LOGGER.info("❌ LangSmith tracing disabled")
            return False
            
    except Exception as e:
        LOGGER.error(f"❌ Error setting up LangSmith tracing: {e}")
        return False


def create_langsmith_metadata(
    user_id: int,
    session_id: str,
    message_id: str,
    **additional_metadata
) -> Dict[str, Any]:
    """
    LangSmith 메타데이터 생성
    
    Args:
        user_id: 사용자 ID
        session_id: 세션 ID
        message_id: 메시지 ID
        **additional_metadata: 추가 메타데이터
        
    Returns:
        Dict: LangSmith 메타데이터
    """
    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "message_id": message_id,
        "service": "mma-savant",
        "version": "1.0",
        "timestamp": kr_time_now().isoformat(),
        "langsmith_enabled": Config.LANGCHAIN_TRACING_V2,
        **additional_metadata
    }
    
    LOGGER.debug(f"📊 LangSmith metadata created: {list(metadata.keys())}")
    return metadata


def log_performance_metrics(
    execution_time: float,
    tools_used: int,
    response_length: int,
    session_id: str,
    message_id: str,
    **additional_metrics
):
    """
    성능 메트릭 로깅
    
    Args:
        execution_time: 실행 시간 (초)
        tools_used: 사용된 도구 수
        response_length: 응답 길이 (문자 수)
        session_id: 세션 ID
        message_id: 메시지 ID
        **additional_metrics: 추가 메트릭
    """
    try:
        metrics = {
            "execution_time": execution_time,
            "tools_used_count": tools_used,
            "response_length": response_length,
            "session_id": session_id,
            "message_id": message_id,
            "timestamp": kr_time_now().isoformat(),
            **additional_metrics
        }
        
        # 성능 임계값 체크
        if execution_time > 30.0:  # 30초 이상
            LOGGER.warning(f"⚠️ Slow execution detected: {execution_time:.2f}s")
        
        if tools_used > 5:  # 도구 5개 이상 사용
            LOGGER.info(f"🔧 High tool usage: {tools_used} tools used")
        
        # LangSmith가 활성화된 경우 상세 로깅
        if Config.LANGCHAIN_TRACING_V2:
            LOGGER.info(f"📊 LangSmith performance metrics: {metrics}")
        else:
            LOGGER.info(f"📊 Performance - Time: {execution_time:.2f}s, Tools: {tools_used}, Length: {response_length}")
        
        # 성능 세션에 메트릭 추가
        session_key = f"{session_id}_{message_id}"
        if session_key in _performance_sessions:
            _performance_sessions[session_key].add_metric(
                "total_execution",
                execution_time,
                tools_used=tools_used,
                response_length=response_length,
                **additional_metrics
            )
    
    except Exception as e:
        LOGGER.error(f"❌ Error logging performance metrics: {e}")


def log_error_details(
    error: Exception,
    context: Dict[str, Any],
    session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    langsmith_metadata: Optional[Dict[str, Any]] = None
):
    """
    에러 상세 정보 로깅
    
    Args:
        error: 발생한 에러
        context: 에러 발생 컨텍스트
        session_id: 세션 ID
        message_id: 메시지 ID
        langsmith_metadata: LangSmith 메타데이터
    """
    try:
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": kr_time_now().isoformat()
        }
        
        if session_id:
            error_details["session_id"] = session_id
        if message_id:
            error_details["message_id"] = message_id
        
        # 특별한 에러 타입 처리
        error_message = str(error).lower()
        if "rate_limit" in error_message or "429" in error_message:
            LOGGER.warning("🚫 Rate limit error detected")
            error_details["error_category"] = "rate_limit"
        elif "timeout" in error_message:
            LOGGER.warning("⏰ Timeout error detected")
            error_details["error_category"] = "timeout"
        elif "connection" in error_message:
            LOGGER.warning("🔌 Connection error detected")
            error_details["error_category"] = "connection"
        else:
            error_details["error_category"] = "unknown"
        
        # LangSmith 에러 로깅
        if Config.LANGCHAIN_TRACING_V2:
            if langsmith_metadata:
                error_details["langsmith_metadata"] = langsmith_metadata
            LOGGER.error(f"❌ LangSmith error details: {error_details}")
        else:
            LOGGER.error(f"❌ Error details: {error_details}")
    
    except Exception as e:
        LOGGER.error(f"❌ Error logging error details: {e}")


@contextmanager
def measure_execution_time(operation_name: str, **metadata):
    """
    실행 시간 측정 컨텍스트 매니저
    
    Args:
        operation_name: 작업 이름
        **metadata: 추가 메타데이터
        
    Yields:
        TimingMetric: 측정 중인 메트릭 객체
    """
    metric = TimingMetric(
        operation=operation_name,
        start_time=time.time(),
        metadata=metadata
    )
    
    LOGGER.debug(f"⏱️ Started measuring: {operation_name}")
    
    try:
        yield metric
    finally:
        duration = metric.finish()
        LOGGER.debug(f"⏱️ {operation_name} took: {duration:.3f}s")


def timing_decorator(operation_name: Optional[str] = None):
    """
    함수 실행 시간 측정 데코레이터
    
    Args:
        operation_name: 작업 이름 (None이면 함수명 사용)
        
    Returns:
        Callable: 데코레이터
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            with measure_execution_time(op_name):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            with measure_execution_time(op_name):
                return func(*args, **kwargs)
        
        # 비동기 함수 여부 확인
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def create_performance_session(
    session_id: str,
    message_id: str,
    user_id: Optional[int] = None,
    **metadata
) -> PerformanceSession:
    """
    성능 측정 세션 생성
    
    Args:
        session_id: 세션 ID
        message_id: 메시지 ID
        user_id: 사용자 ID
        **metadata: 추가 메타데이터
        
    Returns:
        PerformanceSession: 생성된 성능 세션
    """
    session = PerformanceSession(
        session_id=session_id,
        message_id=message_id,
        user_id=user_id,
        metadata=metadata
    )
    
    session_key = f"{session_id}_{message_id}"
    _performance_sessions[session_key] = session
    
    LOGGER.debug(f"📊 Performance session created: {session_key}")
    return session


def get_performance_session(session_id: str, message_id: str) -> Optional[PerformanceSession]:
    """
    성능 세션 조회
    
    Args:
        session_id: 세션 ID
        message_id: 메시지 ID
        
    Returns:
        Optional[PerformanceSession]: 성능 세션 (없으면 None)
    """
    session_key = f"{session_id}_{message_id}"
    return _performance_sessions.get(session_key)


def finish_performance_session(
    session_id: str,
    message_id: str
) -> Optional[Dict[str, Any]]:
    """
    성능 세션 완료 및 요약 반환
    
    Args:
        session_id: 세션 ID
        message_id: 메시지 ID
        
    Returns:
        Optional[Dict]: 성능 요약 (세션이 없으면 None)
    """
    session_key = f"{session_id}_{message_id}"
    session = _performance_sessions.pop(session_key, None)
    
    if session:
        summary = session.get_summary()
        LOGGER.info(f"📊 Performance session completed: {summary['total_duration']:.3f}s")
        return summary
    
    return None


def get_timing_summary() -> Dict[str, Any]:
    """
    전체 타이밍 요약 정보 반환
    
    Returns:
        Dict: 전체 성능 요약
    """
    try:
        active_sessions = len(_performance_sessions)
        
        if not _performance_sessions:
            return {
                "active_sessions": 0,
                "summary": "No active performance sessions"
            }
        
        # 활성 세션 통계
        total_operations = 0
        slowest_session = None
        slowest_duration = 0
        
        for session in _performance_sessions.values():
            total_operations += len(session.metrics)
            duration = session.get_total_duration()
            
            if duration > slowest_duration:
                slowest_duration = duration
                slowest_session = session.session_id
        
        return {
            "active_sessions": active_sessions,
            "total_operations": total_operations,
            "slowest_session": slowest_session,
            "slowest_duration": slowest_duration,
            "langsmith_enabled": Config.LANGCHAIN_TRACING_V2
        }
    
    except Exception as e:
        LOGGER.error(f"❌ Error getting timing summary: {e}")
        return {"error": str(e)}


def cleanup_old_sessions(max_age_seconds: int = 3600):
    """
    오래된 성능 세션 정리
    
    Args:
        max_age_seconds: 최대 보관 시간 (초)
    """
    try:
        current_time = time.time()
        old_sessions = []
        
        for key, session in _performance_sessions.items():
            if current_time - session.start_time > max_age_seconds:
                old_sessions.append(key)
        
        for key in old_sessions:
            del _performance_sessions[key]
        
        if old_sessions:
            LOGGER.info(f"🗑️ Cleaned up {len(old_sessions)} old performance sessions")
    
    except Exception as e:
        LOGGER.error(f"❌ Error cleaning up old sessions: {e}")


# 편의 함수들
def log_langsmith_final_metrics(
    total_time: float,
    message_id: str,
    session_id: str,
    user_id: Optional[int] = None,
    **additional_metrics
):
    """LangSmith 최종 메트릭 로깅 편의 함수"""
    if Config.LANGCHAIN_TRACING_V2:
        final_metrics = {
            "total_streaming_time": total_time,
            "message_id": message_id,
            "session_id": session_id,
            "completion_status": "success",
            **additional_metrics
        }
        
        if user_id:
            final_metrics["user_id"] = user_id
        
        LOGGER.info(f"📊 LangSmith final metrics: {final_metrics}")


def is_langsmith_enabled() -> bool:
    """LangSmith 활성화 상태 확인"""
    return bool(Config.LANGCHAIN_TRACING_V2)


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    import asyncio
    
    def test_performance_monitor():
        print("📊 Performance Monitor Test")
        print("=" * 50)
        
        # LangSmith 설정 확인
        print("\n🔍 LangSmith Configuration:")
        print(f"  Enabled: {setup_langsmith_tracing()}")
        print(f"  Project: {Config.LANGCHAIN_PROJECT}")
        print(f"  API Key Set: {bool(Config.LANGCHAIN_API_KEY)}")
        
        # 메타데이터 생성 테스트
        print("\n📋 Metadata Creation:")
        metadata = create_langsmith_metadata(
            user_id=123,
            session_id="test_session",
            message_id="test_message"
        )
        print(f"  Keys: {list(metadata.keys())}")
        
        # 성능 세션 테스트
        print("\n⏱️ Performance Session:")
        session = create_performance_session(
            session_id="test_session",
            message_id="test_message",
            user_id=123
        )
        
        # 실행 시간 측정 테스트
        with measure_execution_time("test_operation") as metric:
            time.sleep(0.1)  # 시뮬레이션
        
        session.add_metric("test_operation", metric.duration)
        
        # 세션 요약
        summary = finish_performance_session("test_session", "test_message")
        print(f"  Duration: {summary['total_duration']:.3f}s")
        print(f"  Operations: {summary['metrics_count']}")
        
        # 전체 요약
        print("\n📈 System Summary:")
        system_summary = get_timing_summary()
        for key, value in system_summary.items():
            print(f"  {key}: {value}")
    
    # 데코레이터 테스트
    @timing_decorator("test_decorated_function")
    def test_function():
        time.sleep(0.05)
        return "test result"
    
    print("\n🎭 Decorator Test:")
    result = test_function()
    print(f"  Result: {result}")
    
    # 메인 테스트 실행
    test_performance_monitor()