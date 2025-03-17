import os

class DatabaseConfig:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "ufc_stats")


def get_database_url() -> str:
    return f"postgresql+psycopg2://postgres:{database_config.DB_PASSWORD}@{database_config.DB_HOST}:{database_config.DB_PORT}/{database_config.DB_NAME}"