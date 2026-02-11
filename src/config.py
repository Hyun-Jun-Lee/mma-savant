import os
from typing import Dict, Any, List

from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "savant_db")
    TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", "test_savant_db")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME")
    
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL_NAME: str = os.getenv("ANTHROPIC_MODEL_NAME")
    
    # LLM Provider 선택 (anthropic, huggingface)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    
    # Hugging Face API 설정
    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN")
    HUGGINGFACE_MODEL_NAME: str = os.getenv("HUGGINGFACE_MODEL_NAME", "microsoft/DialoGPT-medium")
    HUGGINGFACE_MAX_TOKENS: int = int(os.getenv("HUGGINGFACE_MAX_TOKENS", "4000"))
    HUGGINGFACE_TEMPERATURE: float = float(os.getenv("HUGGINGFACE_TEMPERATURE", "0.7"))

    # 읽기 전용 데이터베이스 설정
    DB_READONLY_USER: str = os.getenv("DB_READONLY_USER")
    DB_READONLY_PASSWORD: str = os.getenv("DB_READONLY_PASSWORD")  # 기본값 없음 - 보안상 필수 설정

    # OpenRouter API 설정
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL_NAME: str = os.getenv("OPENROUTER_MODEL_NAME", "deepseek/deepseek-chat-v3-0324:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    NEXTAUTH_SECRET: str = os.getenv("NEXTAUTH_SECRET")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
    TOKEN_ALGORITHM: str = os.getenv("TOKEN_ALGORITHM")

    # Admin 계정 설정 (필수)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    ADMIN_PW: str = os.getenv("ADMIN_PW")

    # =============================================================================
    # 운영 설정 (Database, Server, Redis)
    # =============================================================================

    # Database Connection Pool Settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    DB_READONLY_POOL_SIZE: int = int(os.getenv("DB_READONLY_POOL_SIZE", "10"))
    DB_READONLY_MAX_OVERFLOW: int = int(os.getenv("DB_READONLY_MAX_OVERFLOW", "20"))

    # Redis Connection Settings
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
    REDIS_RETRY_ON_TIMEOUT: bool = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"

    # API Server Settings
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost").split(",")

    # =============================================================================
    # LLM 및 Agent 설정
    # =============================================================================

    # Default LLM Parameters
    DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4000"))

    # Agent Settings
    AGENT_MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))

def get_database_url(is_test : bool = False) -> str:
    if is_test:
        return f"postgresql+asyncpg://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.TEST_DB_NAME}"
    return f"postgresql+asyncpg://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"

def get_logging_config() -> Dict[str, Any]:
    """환경에 따른 로깅 설정을 반환합니다."""
    
    # 환경변수에서 설정 가져오기
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "logs")
    
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    base_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level
            }
        },
        "loggers": {
            "": {  # 루트 로거
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "WARNING",  # 액세스 로그는 WARNING 이상만
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": False
            },
            # "sqlalchemy.engine": {  # DB 쿼리 로깅
            #     "level": "WARNING" if environment == "production" else "INFO",
            #     "handlers": ["console"],
            #     "propagate": False
            # }
        }
    }
    
    # 환경별 추가 설정
    if environment != "development":
        # 파일 핸들러 추가
        base_config["handlers"].update({
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": f"{log_dir}/app.log",
                "maxBytes": Config.LOG_FILE_MAX_BYTES,
                "backupCount": Config.LOG_FILE_BACKUP_COUNT,
                "formatter": "detailed",
                "level": log_level
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": f"{log_dir}/error.log",
                "maxBytes": Config.LOG_FILE_MAX_BYTES,
                "backupCount": Config.LOG_FILE_BACKUP_COUNT,
                "formatter": "detailed",
                "level": "ERROR"
            }
        })
        
        # 모든 로거에 파일 핸들러 추가
        for logger_name in base_config["loggers"]:
            base_config["loggers"][logger_name]["handlers"].extend(["file"])
            if logger_name in ["", "uvicorn.error"]:  # 에러 로그는 별도 파일에도 저장
                base_config["loggers"][logger_name]["handlers"].append("error_file")
    
    return base_config