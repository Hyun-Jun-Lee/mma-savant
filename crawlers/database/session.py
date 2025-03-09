from typing import Generator
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from core.config import database_config
from contextlib import contextmanager

DATABASE_URL = f"postgresql+psycopg2://postgres:{database_config.DB_PASSWORD}@{database_config.DB_HOST}:{database_config.DB_PORT}/{database_config.DB_NAME}"

engine = create_engine(
    DATABASE_URL, pool_size=20, max_overflow=40, connect_args={"connect_timeout": 30}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()