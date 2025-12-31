"""
테스트용 공통 fixture 정의
모든 테스트에서 사용될 공통 fixture들을 정의
"""
import pytest
import pytest_asyncio
from datetime import date, datetime
from typing import List

import database
from database.connection.postgres_conn_test import (
    cleanup_test_db, reset_test_db_sequences, sync_test_db_schema
)
from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from match.models import MatchModel, FighterMatchModel, SigStrMatchStatModel, BasicMatchStatModel
from event.models import EventModel
from common.utils import normalize_name


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    테스트 세션 시작시 한번만 DB 스키마 동기화 및 정리
    """
    # 1. 먼저 스키마 동기화 (누락된 테이블 생성)
    await sync_test_db_schema()

    # 2. 세션 시작 시 한번만 데이터 정리
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


# Match 관련 fixtures

@pytest_asyncio.fixture
async def sample_event(clean_test_session):
    """
    기본적인 테스트용 이벤트 생성
    매치 테스트용 이벤트
    """
    event = EventModel(
        name="UFC Test Event",
        event_date=date(2024, 1, 15),
        location="Las Vegas, NV"
    )
    clean_test_session.add(event)
    await clean_test_session.flush()
    return event


@pytest_asyncio.fixture
async def sample_match(sample_event, clean_test_session):
    """
    기본적인 테스트용 매치 생성
    다양한 매치 테스트용
    """
    match = MatchModel(
        event_id=sample_event.id,
        weight_class_id=5,  # Welterweight
        method="Decision - Unanimous",
        result_round=3,
        time="15:00",
        order=1,
        is_main_event=False,
        detail_url="http://example.com/match/test"
    )
    clean_test_session.add(match)
    await clean_test_session.flush()
    return match


@pytest_asyncio.fixture
async def match_with_fighters(sample_match, sample_fighter, clean_test_session):
    """
    파이터들이 포함된 매치 생성
    FighterMatch 관계 테스트용
    """
    # 두 번째 파이터 생성
    fighter2 = FighterModel(
        name="Opponent Fighter",
        nickname="The Opponent",
        wins=8,
        losses=3,
        draws=0
    )
    clean_test_session.add(fighter2)
    await clean_test_session.flush()
    
    # FighterMatch 관계 생성
    fighter_matches = [
        FighterMatchModel(
            fighter_id=sample_fighter.id,
            match_id=sample_match.id,
            result="win"
        ),
        FighterMatchModel(
            fighter_id=fighter2.id,
            match_id=sample_match.id,
            result="loss"
        )
    ]
    clean_test_session.add_all(fighter_matches)
    await clean_test_session.flush()
    
    return sample_match, [sample_fighter, fighter2], fighter_matches


@pytest_asyncio.fixture
async def match_with_statistics(match_with_fighters, clean_test_session):
    """
    통계가 포함된 매치 생성
    매치 통계 테스트용
    """
    match, fighters, fighter_matches = match_with_fighters
    
    # 기본 매치 통계 생성
    basic_stats = [
        BasicMatchStatModel(
            fighter_match_id=fighter_matches[0].id,
            knockdowns=1,
            control_time_seconds=240,
            submission_attempts=2,
            sig_str_landed=45,
            sig_str_attempted=75,
            total_str_landed=65,
            total_str_attempted=95,
            td_landed=3,
            td_attempted=6,
            round=3
        ),
        BasicMatchStatModel(
            fighter_match_id=fighter_matches[1].id,
            knockdowns=0,
            control_time_seconds=120,
            submission_attempts=1,
            sig_str_landed=32,
            sig_str_attempted=58,
            total_str_landed=48,
            total_str_attempted=72,
            td_landed=1,
            td_attempted=4,
            round=3
        )
    ]
    
    # 스트라이크 세부 통계 생성
    strike_stats = [
        SigStrMatchStatModel(
            fighter_match_id=fighter_matches[0].id,
            head_strikes_landed=25,
            head_strikes_attempts=40,
            body_strikes_landed=15,
            body_strikes_attempts=25,
            leg_strikes_landed=5,
            leg_strikes_attempts=10,
            takedowns_landed=3,
            takedowns_attempts=6,
            round=3
        ),
        SigStrMatchStatModel(
            fighter_match_id=fighter_matches[1].id,
            head_strikes_landed=18,
            head_strikes_attempts=35,
            body_strikes_landed=10,
            body_strikes_attempts=18,
            leg_strikes_landed=4,
            leg_strikes_attempts=5,
            takedowns_landed=1,
            takedowns_attempts=4,
            round=3
        )
    ]
    
    clean_test_session.add_all(basic_stats + strike_stats)
    await clean_test_session.flush()
    
    return match, fighters, fighter_matches, basic_stats, strike_stats


@pytest_asyncio.fixture
async def multiple_matches_for_event(sample_event, clean_test_session):
    """
    하나의 이벤트에 여러 매치 생성
    이벤트별 매치 조회 테스트용
    """
    matches = [
        MatchModel(
            event_id=sample_event.id,
            weight_class_id=4,  # Lightweight
            method="KO/TKO",
            result_round=2,
            time="3:24",
            order=1,
            is_main_event=False
        ),
        MatchModel(
            event_id=sample_event.id,
            weight_class_id=5,  # Welterweight  
            method="Submission",
            result_round=1,
            time="4:55",
            order=2,
            is_main_event=False
        ),
        MatchModel(
            event_id=sample_event.id,
            weight_class_id=6,  # Middleweight
            method="Decision - Unanimous",
            result_round=5,
            time="25:00",
            order=3,
            is_main_event=True
        )
    ]
    clean_test_session.add_all(matches)
    await clean_test_session.flush()
    return sample_event, matches


@pytest_asyncio.fixture
async def fighters_with_multiple_matches(clean_test_session):
    """
    여러 매치를 가진 파이터들 생성
    파이터별 매치 기록 조회 테스트용
    """
    # 파이터들 생성
    fighters = [
        FighterModel(name="Multi Match Fighter 1", wins=15, losses=2, draws=0),
        FighterModel(name="Multi Match Fighter 2", wins=12, losses=5, draws=1)
    ]
    clean_test_session.add_all(fighters)
    await clean_test_session.flush()
    
    # 이벤트 생성
    events = [
        EventModel(name="UFC Event 1", event_date=date(2024, 1, 1), location="Vegas"),
        EventModel(name="UFC Event 2", event_date=date(2024, 2, 1), location="New York"),
        EventModel(name="UFC Event 3", event_date=date(2024, 3, 1), location="London")
    ]
    clean_test_session.add_all(events)
    await clean_test_session.flush()
    
    # 매치들 생성
    matches = [
        MatchModel(event_id=events[0].id, weight_class_id=5, method="Decision", result_round=3, time="15:00", order=1, is_main_event=False),
        MatchModel(event_id=events[1].id, weight_class_id=5, method="KO/TKO", result_round=2, time="3:45", order=1, is_main_event=False),
        MatchModel(event_id=events[2].id, weight_class_id=5, method="Submission", result_round=1, time="2:30", order=1, is_main_event=True)
    ]
    clean_test_session.add_all(matches)
    await clean_test_session.flush()
    
    # FighterMatch 관계 생성 (두 파이터가 3번 싸움)
    fighter_matches = []
    for i, match in enumerate(matches):
        # 첫 번째 파이터가 모든 경기에서 승리
        fighter_matches.extend([
            FighterMatchModel(fighter_id=fighters[0].id, match_id=match.id, result="win"),
            FighterMatchModel(fighter_id=fighters[1].id, match_id=match.id, result="loss")
        ])
    
    clean_test_session.add_all(fighter_matches)
    await clean_test_session.flush()
    
    return fighters, matches, fighter_matches


# Event 관련 fixtures (Event Repository 테스트용)

@pytest_asyncio.fixture
async def multiple_events_different_dates(clean_test_session):
    """
    다양한 날짜의 이벤트들 생성
    날짜별 테스트용
    """
    events = [
        EventModel(
            name="UFC 290",
            event_date=date(2024, 1, 15),
            location="Las Vegas, NV"
        ),
        EventModel(
            name="UFC 291", 
            event_date=date(2024, 3, 20),
            location="Miami, FL"
        ),
        EventModel(
            name="UFC 292",
            event_date=date(2024, 6, 10),
            location="Boston, MA"
        ),
        EventModel(
            name="UFC 293",
            event_date=date(2024, 9, 5),
            location="Sydney, Australia"
        )
    ]
    clean_test_session.add_all(events)
    await clean_test_session.flush()
    return events


@pytest_asyncio.fixture  
async def multiple_events_different_names(clean_test_session):
    """
    다양한 이름의 이벤트들 생성
    이름 검색 테스트용
    """
    events = [
        EventModel(
            name="UFC 300: Championship Night",
            event_date=date(2024, 4, 13),
            location="Las Vegas, NV"
        ),
        EventModel(
            name="UFC Fight Night: London",
            event_date=date(2024, 5, 18),
            location="London, UK"
        ),
        EventModel(
            name="Bellator 301",
            event_date=date(2024, 6, 22),
            location="Chicago, IL"
        ),
        EventModel(
            name="ONE Championship: Singapore",
            event_date=date(2024, 7, 15),
            location="Singapore"
        )
    ]
    clean_test_session.add_all(events)
    await clean_test_session.flush()
    return events


@pytest_asyncio.fixture
async def events_past_and_future(clean_test_session):
    """
    과거와 미래 이벤트들 생성
    시간 기반 테스트용
    """
    from datetime import timedelta
    today = date.today()
    
    # 과거 이벤트들
    past_events = [
        EventModel(
            name="UFC Past Event 1",
            event_date=today - timedelta(days=30),
            location="Las Vegas, NV"
        ),
        EventModel(
            name="UFC Past Event 2", 
            event_date=today - timedelta(days=15),
            location="New York, NY"
        ),
        EventModel(
            name="UFC Past Event 3",
            event_date=today - timedelta(days=7),
            location="Los Angeles, CA"
        )
    ]
    
    # 미래 이벤트들
    future_events = [
        EventModel(
            name="UFC Future Event 1",
            event_date=today + timedelta(days=7),
            location="Miami, FL"
        ),
        EventModel(
            name="UFC Future Event 2",
            event_date=today + timedelta(days=20),
            location="Boston, MA"
        ),
        EventModel(
            name="UFC Future Event 3",
            event_date=today + timedelta(days=45),
            location="London, UK"
        )
    ]
    
    all_events = past_events + future_events
    clean_test_session.add_all(all_events)
    await clean_test_session.flush()
    
    return past_events, future_events


@pytest_asyncio.fixture
async def events_different_locations(clean_test_session):
    """
    다양한 장소의 이벤트들 생성
    장소별 테스트용
    """
    events = [
        EventModel(
            name="UFC Vegas 1",
            event_date=date(2024, 2, 10),
            location="Las Vegas, Nevada"
        ),
        EventModel(
            name="UFC Vegas 2",
            event_date=date(2024, 3, 15),
            location="Las Vegas, NV"
        ),
        EventModel(
            name="UFC London",
            event_date=date(2024, 4, 20),
            location="London, England"
        ),
        EventModel(
            name="UFC Paris",
            event_date=date(2024, 5, 25),
            location="Paris, France"
        ),
        EventModel(
            name="UFC Abu Dhabi",
            event_date=date(2024, 6, 30),
            location="Abu Dhabi, UAE"
        )
    ]
    clean_test_session.add_all(events)
    await clean_test_session.flush()
    return events


@pytest_asyncio.fixture
async def events_for_calendar_test(clean_test_session):
    """
    캘린더 테스트용 특정 월의 이벤트들 생성
    """
    events = [
        EventModel(
            name="UFC Event Day 1",
            event_date=date(2024, 8, 1),
            location="Las Vegas, NV"
        ),
        EventModel(
            name="UFC Event Day 15",
            event_date=date(2024, 8, 15),
            location="New York, NY"
        ),
        EventModel(
            name="UFC Event Day 30",
            event_date=date(2024, 8, 30),
            location="Los Angeles, CA"
        )
    ]
    clean_test_session.add_all(events)
    await clean_test_session.flush()
    return events