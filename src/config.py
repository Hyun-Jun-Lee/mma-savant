import os

class DatabaseConfig:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "ufc_stats")

class RedisConfig:
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")

def get_redis_config() -> RedisConfig:
    return RedisConfig()

def get_database_url() -> str:
    database_config = DatabaseConfig()
    return f"postgresql+psycopg2://postgres:{database_config.DB_PASSWORD}@{database_config.DB_HOST}:{database_config.DB_PORT}/{database_config.DB_NAME}"