"""
테스트용 공통 fixture 정의
모든 테스트에서 사용될 공통 fixture들을 정의
"""
import pytest
import pytest_asyncio
from datetime import date, datetime
from typing import List

import database
from database.connection.test_postgres_conn import test_db_session, cleanup_test_db, reset_test_db_sequences
from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from common.utils import normalize_name


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    테스트 세션 시작시 한번만 DB 정리
    """
    from database.connection.test_postgres_conn import cleanup_test_db, reset_test_db_sequences
    # 세션 시작 시 한번만 정리
    await cleanup_test_db()
    await reset_test_db_sequences()
    
    yield


@pytest_asyncio.fixture
async def clean_test_session():
    """
    각 테스트용 깨끗한 세션 제공
    테스트 완료 후 자동으로 롤백하여 테스트 격리 보장
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from config import get_database_url
    
    # 각 테스트마다 새로운 엔진과 세션 생성
    engine = create_async_engine(get_database_url(is_test=True), echo=False)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    session = session_factory()
    try:
        yield session
        await session.rollback()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def sample_fighter(clean_test_session):
    """
    기본적인 테스트용 파이터 생성
    다양한 테스트에서 재사용할 수 있는 기본 파이터
    """
    fighter = FighterModel(
        name="Sample Fighter",
        nickname="The Sample",
        wins=10,
        losses=2,
        draws=0,
        stance="Orthodox",
        height=72.0,
        weight=185.0
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()
    return fighter


@pytest_asyncio.fixture
async def multiple_fighters(clean_test_session):
    """
    여러 파이터를 생성하는 fixture
    리스트 관련 테스트용
    """
    fighters = [
        FighterModel(name="Fighter Alpha", wins=15, losses=2, draws=0),
        FighterModel(name="Fighter Beta", wins=12, losses=3, draws=1),
        FighterModel(name="Fighter Gamma", wins=20, losses=1, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()
    return fighters


@pytest_asyncio.fixture
async def champion_fighter(clean_test_session):
    """
    챔피언 파이터 생성
    벨트 관련 테스트용
    """
    fighter = FighterModel(
        name="Championship Fighter",
        nickname="The Champion",
        wins=25,
        losses=0,
        draws=0,
        belt=True,
        stance="Switch"
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()
    return fighter


@pytest_asyncio.fixture
async def fighter_with_rankings(clean_test_session):
    """
    랭킹을 가진 파이터 생성
    랭킹 관련 테스트용
    """
    # 파이터 생성
    fighter = FighterModel(
        name="Ranked Fighter",
        nickname="The Ranked",
        wins=18,
        losses=2,
        draws=0
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()
    
    # 랭킹 정보 추가
    rankings = [
        RankingModel(fighter_id=fighter.id, weight_class_id=4, ranking=3),  # Lightweight
        RankingModel(fighter_id=fighter.id, weight_class_id=5, ranking=5)   # Welterweight
    ]
    clean_test_session.add_all(rankings)
    await clean_test_session.flush()
    
    return fighter, rankings


@pytest_asyncio.fixture
async def weight_class_fighters(clean_test_session):
    """
    특정 체급에 속한 파이터들 생성
    체급별 테스트용
    """
    # 파이터들 생성
    fighters = [
        FighterModel(name="LW Champion", wins=22, losses=1, draws=0, belt=True),
        FighterModel(name="LW Contender 1", wins=18, losses=2, draws=0),
        FighterModel(name="LW Contender 2", wins=15, losses=3, draws=0)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()
    
    # Lightweight(4) 체급 랭킹 추가
    rankings = [
        RankingModel(fighter_id=fighters[0].id, weight_class_id=4, ranking=1),
        RankingModel(fighter_id=fighters[1].id, weight_class_id=4, ranking=2),
        RankingModel(fighter_id=fighters[2].id, weight_class_id=4, ranking=3)
    ]
    clean_test_session.add_all(rankings)
    await clean_test_session.flush()
    
    return fighters, rankings


@pytest.fixture
def normalized_name_test_cases():
    """
    이름 정규화 테스트 케이스들
    이름 정규화 관련 테스트용
    """
    return [
        ("José Aldó", "jose aldo"),
        ("Khabib Nurmagomedov", "khabib nurmagomedov"),
        ("Conor McGregor", "conor mcgregor"),
        ("ANDERSON SILVA", "anderson silva"),
        ("Fédor Emelianenko", "fedor emelianenko"),
        ("Israel Adesanya", "israel adesanya")
    ]


@pytest_asyncio.fixture
async def complete_fighter_data(clean_test_session):
    """
    모든 필드가 채워진 완전한 파이터 데이터
    스키마 변환 테스트용
    """
    fighter = FighterModel(
        name="Complete Fighter",
        nickname="The Complete",
        height=74.0,
        height_cm=188.0,
        weight=205.0,
        weight_kg=93.0,
        reach=80.0,
        reach_cm=203.0,
        stance="Southpaw",
        belt=True,
        birthdate="1990-01-15",
        detail_url="http://example.com/complete-fighter",
        wins=30,
        losses=2,
        draws=1
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()
    return fighter


@pytest_asyncio.fixture
async def fighters_for_record_test(clean_test_session):
    """
    기록(승/패/무승부) 기준 테스트용 파이터들
    top fighters by record 테스트용
    """
    fighters = [
        FighterModel(name="High Wins Fighter", wins=30, losses=1, draws=0),
        FighterModel(name="High Losses Fighter", wins=10, losses=15, draws=0),
        FighterModel(name="High Draws Fighter", wins=15, losses=10, draws=5),
        FighterModel(name="Balanced Fighter", wins=20, losses=5, draws=2)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()
    return fighters