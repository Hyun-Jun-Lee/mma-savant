"""
테스트용 공통 fixture 정의
모든 테스트에서 사용될 공통 fixture들을 정의
"""
import sys
from unittest.mock import MagicMock

# redis 모듈이 설치되지 않은 환경에서도 서비스 테스트 가능하도록 mock 처리
if "redis" not in sys.modules:
    sys.modules["redis"] = MagicMock()

import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
from typing import List

from database.connection.postgres_conn_test import (
    cleanup_test_db, reset_test_db_sequences
)
from fighter.models import FighterModel, FighterSchema, RankingModel, RankingSchema
from match.models import MatchModel, FighterMatchModel, SigStrMatchStatModel, BasicMatchStatModel
from event.models import EventModel
from common.utils import utc_today


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    테스트 세션 시작시 데이터 정리
    테이블은 Docker 초기화 시 생성됨 (00_create_test_db.sh)
    """
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
    today = utc_today()
    
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


# =============================================================================
# Dashboard 테스트용 fixture
# =============================================================================

@pytest_asyncio.fixture
async def dashboard_data(clean_test_session):
    """
    Dashboard 집계 쿼리 테스트를 위한 종합 데이터 세트

    데이터 구성:
    - 3명의 파이터 (A, B: 5전 이상, C: 4전 — HAVING >= 5 필터 테스트용)
    - 7개의 이벤트 (5 past, 2 future)
    - 9개의 매치: wc=4 (LW) 7개 + wc=5 (WW) 2개
    - 18개의 fighter_match / match_statistics / strike_detail 기록
    - 2개의 ranking 기록
    """
    session = clean_test_session
    today = date.today()

    # === Fighters ===
    fighter_a = FighterModel(name="Alpha Fighter", wins=10, losses=2, draws=0)
    fighter_b = FighterModel(name="Beta Fighter", wins=8, losses=4, draws=1)
    fighter_c = FighterModel(name="Gamma Fighter", wins=3, losses=2, draws=0)
    session.add_all([fighter_a, fighter_b, fighter_c])
    await session.flush()

    # === Events (5 past + 2 future) ===
    events = [
        EventModel(name="UFC Test 301", event_date=today - timedelta(days=400), location="Las Vegas, NV"),
        EventModel(name="UFC Test 302", event_date=today - timedelta(days=300), location="New York, NY"),
        EventModel(name="UFC Test 303", event_date=today - timedelta(days=120), location="London, UK"),
        EventModel(name="UFC Test 304", event_date=today - timedelta(days=60), location="Abu Dhabi, UAE"),
        EventModel(name="UFC Test 305", event_date=today - timedelta(days=14), location="Miami, FL"),
        EventModel(name="UFC Test 306", event_date=today + timedelta(days=14), location="Tokyo, Japan"),
        EventModel(name="UFC Test 307", event_date=today + timedelta(days=45), location="Sydney, Australia"),
    ]
    session.add_all(events)
    await session.flush()

    # === Matches: wc=4 (Lightweight) 7개 + wc=5 (Welterweight) 2개 ===
    matches = [
        # --- wc=4 (Lightweight) ---
        MatchModel(event_id=events[0].id, weight_class_id=4, method="KO-Punch",
                   result_round=1, time="2:30", order=1, is_main_event=True),
        MatchModel(event_id=events[1].id, weight_class_id=4, method="TKO-Punches",
                   result_round=2, time="4:15", order=1, is_main_event=False),
        MatchModel(event_id=events[2].id, weight_class_id=4, method="SUB-Rear Naked Choke",
                   result_round=1, time="3:45", order=1, is_main_event=False),
        MatchModel(event_id=events[3].id, weight_class_id=4, method="U-DEC",
                   result_round=3, time="15:00", order=1, is_main_event=False),
        MatchModel(event_id=events[4].id, weight_class_id=4, method="S-DEC",
                   result_round=3, time="15:00", order=1, is_main_event=False),
        MatchModel(event_id=events[2].id, weight_class_id=4, method="SUB-Armbar",
                   result_round=2, time="4:50", order=2, is_main_event=False),
        MatchModel(event_id=events[3].id, weight_class_id=4, method="M-DEC",
                   result_round=3, time="15:00", order=2, is_main_event=False),
        # --- wc=5 (Welterweight) ---
        MatchModel(event_id=events[4].id, weight_class_id=5, method="KO-Punch",
                   result_round=1, time="3:10", order=2, is_main_event=False),
        MatchModel(event_id=events[3].id, weight_class_id=5, method="SUB-Guillotine",
                   result_round=2, time="4:30", order=3, is_main_event=False),
    ]
    session.add_all(matches)
    await session.flush()

    # === Fighter Matches ===
    # wc=4: A 5전(전승), B 5전(2승3패), C 4전(전패)
    # wc=5: A 2전(전승), B 2전(전패)
    # 합계: A 7전, B 7전, C 4전 (C는 HAVING >= 5 제외)
    fm_a0 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[0].id, result="win")
    fm_b0 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[0].id, result="loss")
    fm_a1 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[1].id, result="win")
    fm_b1 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[1].id, result="loss")
    fm_a2 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[2].id, result="win")
    fm_b2 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[2].id, result="loss")
    fm_a3 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[3].id, result="win")
    fm_c3 = FighterMatchModel(fighter_id=fighter_c.id, match_id=matches[3].id, result="loss")
    fm_a4 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[4].id, result="win")
    fm_c4 = FighterMatchModel(fighter_id=fighter_c.id, match_id=matches[4].id, result="loss")
    fm_b5 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[5].id, result="win")
    fm_c5 = FighterMatchModel(fighter_id=fighter_c.id, match_id=matches[5].id, result="loss")
    fm_b6 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[6].id, result="win")
    fm_c6 = FighterMatchModel(fighter_id=fighter_c.id, match_id=matches[6].id, result="loss")

    all_fms = [fm_a0, fm_b0, fm_a1, fm_b1, fm_a2, fm_b2, fm_a3, fm_c3, fm_a4, fm_c4, fm_b5, fm_c5, fm_b6, fm_c6]
    session.add_all(all_fms)
    await session.flush()

    # --- wc=5 Fighter Matches ---
    fm_a7 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[7].id, result="win")
    fm_b7 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[7].id, result="loss")
    fm_a8 = FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[8].id, result="win")
    fm_b8 = FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[8].id, result="loss")
    session.add_all([fm_a7, fm_b7, fm_a8, fm_b8])
    await session.flush()

    # === Match Statistics (BasicMatchStatModel) ===
    basic_stats = [
        BasicMatchStatModel(fighter_match_id=fm_a0.id, sig_str_landed=50, sig_str_attempted=80,
                            td_landed=3, td_attempted=5, control_time_seconds=180,
                            submission_attempts=1, knockdowns=1, total_str_landed=65, total_str_attempted=95, round=1),
        BasicMatchStatModel(fighter_match_id=fm_a1.id, sig_str_landed=45, sig_str_attempted=70,
                            td_landed=2, td_attempted=4, control_time_seconds=200,
                            submission_attempts=2, knockdowns=1, total_str_landed=60, total_str_attempted=85, round=2),
        BasicMatchStatModel(fighter_match_id=fm_a2.id, sig_str_landed=30, sig_str_attempted=55,
                            td_landed=4, td_attempted=6, control_time_seconds=300,
                            submission_attempts=3, knockdowns=0, total_str_landed=40, total_str_attempted=65, round=1),
        BasicMatchStatModel(fighter_match_id=fm_a3.id, sig_str_landed=60, sig_str_attempted=100,
                            td_landed=2, td_attempted=3, control_time_seconds=150,
                            submission_attempts=1, knockdowns=0, total_str_landed=80, total_str_attempted=120, round=3),
        BasicMatchStatModel(fighter_match_id=fm_a4.id, sig_str_landed=55, sig_str_attempted=90,
                            td_landed=1, td_attempted=2, control_time_seconds=100,
                            submission_attempts=0, knockdowns=0, total_str_landed=72, total_str_attempted=108, round=3),
        BasicMatchStatModel(fighter_match_id=fm_b0.id, sig_str_landed=35, sig_str_attempted=65,
                            td_landed=1, td_attempted=3, control_time_seconds=60,
                            submission_attempts=1, knockdowns=0, total_str_landed=48, total_str_attempted=72, round=1),
        BasicMatchStatModel(fighter_match_id=fm_b1.id, sig_str_landed=40, sig_str_attempted=75,
                            td_landed=2, td_attempted=4, control_time_seconds=80,
                            submission_attempts=0, knockdowns=0, total_str_landed=55, total_str_attempted=90, round=2),
        BasicMatchStatModel(fighter_match_id=fm_b2.id, sig_str_landed=25, sig_str_attempted=50,
                            td_landed=0, td_attempted=2, control_time_seconds=30,
                            submission_attempts=1, knockdowns=0, total_str_landed=32, total_str_attempted=58, round=1),
        BasicMatchStatModel(fighter_match_id=fm_b5.id, sig_str_landed=38, sig_str_attempted=60,
                            td_landed=3, td_attempted=5, control_time_seconds=250,
                            submission_attempts=2, knockdowns=0, total_str_landed=50, total_str_attempted=75, round=2),
        BasicMatchStatModel(fighter_match_id=fm_b6.id, sig_str_landed=48, sig_str_attempted=85,
                            td_landed=2, td_attempted=3, control_time_seconds=120,
                            submission_attempts=1, knockdowns=0, total_str_landed=62, total_str_attempted=98, round=3),
        BasicMatchStatModel(fighter_match_id=fm_c3.id, sig_str_landed=55, sig_str_attempted=95,
                            td_landed=1, td_attempted=3, control_time_seconds=90,
                            submission_attempts=1, knockdowns=0, total_str_landed=70, total_str_attempted=110, round=3),
        BasicMatchStatModel(fighter_match_id=fm_c4.id, sig_str_landed=50, sig_str_attempted=88,
                            td_landed=2, td_attempted=4, control_time_seconds=80,
                            submission_attempts=0, knockdowns=0, total_str_landed=65, total_str_attempted=100, round=3),
        BasicMatchStatModel(fighter_match_id=fm_c5.id, sig_str_landed=20, sig_str_attempted=45,
                            td_landed=0, td_attempted=2, control_time_seconds=20,
                            submission_attempts=0, knockdowns=0, total_str_landed=28, total_str_attempted=55, round=2),
        BasicMatchStatModel(fighter_match_id=fm_c6.id, sig_str_landed=42, sig_str_attempted=78,
                            td_landed=1, td_attempted=3, control_time_seconds=70,
                            submission_attempts=0, knockdowns=0, total_str_landed=55, total_str_attempted=90, round=3),
    ]
    session.add_all(basic_stats)
    await session.flush()

    # --- wc=5 Match Statistics ---
    wc5_basic_stats = [
        BasicMatchStatModel(fighter_match_id=fm_a7.id, sig_str_landed=40, sig_str_attempted=60,
                            td_landed=2, td_attempted=3, control_time_seconds=150,
                            submission_attempts=0, knockdowns=1, total_str_landed=52, total_str_attempted=72, round=1),
        BasicMatchStatModel(fighter_match_id=fm_b7.id, sig_str_landed=20, sig_str_attempted=40,
                            td_landed=1, td_attempted=2, control_time_seconds=40,
                            submission_attempts=0, knockdowns=0, total_str_landed=28, total_str_attempted=48, round=1),
        BasicMatchStatModel(fighter_match_id=fm_a8.id, sig_str_landed=35, sig_str_attempted=55,
                            td_landed=3, td_attempted=4, control_time_seconds=250,
                            submission_attempts=2, knockdowns=0, total_str_landed=45, total_str_attempted=68, round=2),
        BasicMatchStatModel(fighter_match_id=fm_b8.id, sig_str_landed=22, sig_str_attempted=45,
                            td_landed=0, td_attempted=2, control_time_seconds=30,
                            submission_attempts=1, knockdowns=0, total_str_landed=30, total_str_attempted=55, round=2),
    ]
    session.add_all(wc5_basic_stats)
    await session.flush()

    # === Strike Details (SigStrMatchStatModel) ===
    strike_details = [
        SigStrMatchStatModel(fighter_match_id=fm_a0.id, head_strikes_landed=25, head_strikes_attempts=40,
                             body_strikes_landed=15, body_strikes_attempts=25, leg_strikes_landed=5, leg_strikes_attempts=10,
                             clinch_strikes_landed=3, clinch_strikes_attempts=5, ground_strikes_landed=2, ground_strikes_attempts=5, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_a1.id, head_strikes_landed=22, head_strikes_attempts=35,
                             body_strikes_landed=12, body_strikes_attempts=20, leg_strikes_landed=6, leg_strikes_attempts=8,
                             clinch_strikes_landed=3, clinch_strikes_attempts=5, ground_strikes_landed=2, ground_strikes_attempts=3, round=2),
        SigStrMatchStatModel(fighter_match_id=fm_a2.id, head_strikes_landed=15, head_strikes_attempts=28,
                             body_strikes_landed=8, body_strikes_attempts=15, leg_strikes_landed=3, leg_strikes_attempts=5,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=5, ground_strikes_attempts=8, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_a3.id, head_strikes_landed=30, head_strikes_attempts=50,
                             body_strikes_landed=18, body_strikes_attempts=30, leg_strikes_landed=7, leg_strikes_attempts=12,
                             clinch_strikes_landed=3, clinch_strikes_attempts=5, ground_strikes_landed=2, ground_strikes_attempts=3, round=3),
        SigStrMatchStatModel(fighter_match_id=fm_a4.id, head_strikes_landed=28, head_strikes_attempts=45,
                             body_strikes_landed=16, body_strikes_attempts=28, leg_strikes_landed=8, leg_strikes_attempts=12,
                             clinch_strikes_landed=2, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=3),
        SigStrMatchStatModel(fighter_match_id=fm_b0.id, head_strikes_landed=18, head_strikes_attempts=35,
                             body_strikes_landed=10, body_strikes_attempts=18, leg_strikes_landed=4, leg_strikes_attempts=7,
                             clinch_strikes_landed=2, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_b1.id, head_strikes_landed=20, head_strikes_attempts=38,
                             body_strikes_landed=12, body_strikes_attempts=22, leg_strikes_landed=5, leg_strikes_attempts=8,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=1, ground_strikes_attempts=3, round=2),
        SigStrMatchStatModel(fighter_match_id=fm_b2.id, head_strikes_landed=12, head_strikes_attempts=25,
                             body_strikes_landed=8, body_strikes_attempts=15, leg_strikes_landed=3, leg_strikes_attempts=5,
                             clinch_strikes_landed=1, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_b5.id, head_strikes_landed=20, head_strikes_attempts=30,
                             body_strikes_landed=10, body_strikes_attempts=17, leg_strikes_landed=4, leg_strikes_attempts=6,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=2, ground_strikes_attempts=3, round=2),
        SigStrMatchStatModel(fighter_match_id=fm_b6.id, head_strikes_landed=24, head_strikes_attempts=42,
                             body_strikes_landed=14, body_strikes_attempts=25, leg_strikes_landed=6, leg_strikes_attempts=10,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=2, ground_strikes_attempts=4, round=3),
        SigStrMatchStatModel(fighter_match_id=fm_c3.id, head_strikes_landed=28, head_strikes_attempts=48,
                             body_strikes_landed=16, body_strikes_attempts=28, leg_strikes_landed=7, leg_strikes_attempts=12,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=2, ground_strikes_attempts=3, round=3),
        SigStrMatchStatModel(fighter_match_id=fm_c4.id, head_strikes_landed=25, head_strikes_attempts=44,
                             body_strikes_landed=15, body_strikes_attempts=26, leg_strikes_landed=6, leg_strikes_attempts=11,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=2, ground_strikes_attempts=3, round=3),
        SigStrMatchStatModel(fighter_match_id=fm_c5.id, head_strikes_landed=10, head_strikes_attempts=22,
                             body_strikes_landed=6, body_strikes_attempts=13, leg_strikes_landed=2, leg_strikes_attempts=5,
                             clinch_strikes_landed=1, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=2),
        SigStrMatchStatModel(fighter_match_id=fm_c6.id, head_strikes_landed=21, head_strikes_attempts=39,
                             body_strikes_landed=12, body_strikes_attempts=23, leg_strikes_landed=5, leg_strikes_attempts=9,
                             clinch_strikes_landed=2, clinch_strikes_attempts=4, ground_strikes_landed=2, ground_strikes_attempts=3, round=3),
    ]
    session.add_all(strike_details)
    await session.flush()

    # --- wc=5 Strike Details ---
    wc5_strike_details = [
        SigStrMatchStatModel(fighter_match_id=fm_a7.id, head_strikes_landed=20, head_strikes_attempts=30,
                             body_strikes_landed=12, body_strikes_attempts=18, leg_strikes_landed=4, leg_strikes_attempts=7,
                             clinch_strikes_landed=2, clinch_strikes_attempts=3, ground_strikes_landed=2, ground_strikes_attempts=2, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_b7.id, head_strikes_landed=10, head_strikes_attempts=20,
                             body_strikes_landed=6, body_strikes_attempts=12, leg_strikes_landed=2, leg_strikes_attempts=4,
                             clinch_strikes_landed=1, clinch_strikes_attempts=2, ground_strikes_landed=1, ground_strikes_attempts=2, round=1),
        SigStrMatchStatModel(fighter_match_id=fm_a8.id, head_strikes_landed=18, head_strikes_attempts=28,
                             body_strikes_landed=10, body_strikes_attempts=16, leg_strikes_landed=4, leg_strikes_attempts=6,
                             clinch_strikes_landed=2, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=2),
        SigStrMatchStatModel(fighter_match_id=fm_b8.id, head_strikes_landed=12, head_strikes_attempts=24,
                             body_strikes_landed=6, body_strikes_attempts=12, leg_strikes_landed=2, leg_strikes_attempts=4,
                             clinch_strikes_landed=1, clinch_strikes_attempts=3, ground_strikes_landed=1, ground_strikes_attempts=2, round=2),
    ]
    session.add_all(wc5_strike_details)
    await session.flush()

    # === Rankings (Lightweight) ===
    rankings = [
        RankingModel(fighter_id=fighter_a.id, weight_class_id=4, ranking=1),
        RankingModel(fighter_id=fighter_b.id, weight_class_id=4, ranking=2),
    ]
    session.add_all(rankings)
    await session.flush()

    return {
        "fighters": [fighter_a, fighter_b, fighter_c],
        "events": events,
        "matches": matches,
        "fighter_matches": all_fms,
        "rankings": rankings,
    }