from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from contextlib import contextmanager

DATABASE_URL = get_database_url()

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