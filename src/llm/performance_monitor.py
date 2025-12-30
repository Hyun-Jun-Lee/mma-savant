"""
성능 모니터링 및 메트릭 수집
LangSmith 트레이싱 설정을 담당
"""
from config import Config
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


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
