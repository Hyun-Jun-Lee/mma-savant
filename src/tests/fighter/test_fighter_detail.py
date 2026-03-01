"""
Fighter Detail 기능 테스트
- Repository: get_fight_history, get_per_match_stats, get_finish_breakdown
- Service: get_fighter_detail
- Helper: _calc_current_streak, _calc_age
"""
import pytest
import pytest_asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel
from match.models import MatchModel, FighterMatchModel, BasicMatchStatModel, SigStrMatchStatModel
from event.models import EventModel
from fighter import repositories as fighter_repo
from fighter import services as fighter_services
from fighter.services import _calc_current_streak, _calc_age
from fighter.dto import FighterDetailResponseDTO
from fighter.exceptions import FighterNotFoundError, FighterValidationError


# =============================================================================
# Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def fighter_detail_data(clean_test_session):
    """
    Fighter detail 테스트를 위한 종합 데이터 세트

    데이터 구성:
    - fighter_a: 3전 (KO 1승, SUB 1승, DEC 1승) — birthdate 있음, belt=True
    - fighter_b: 상대 선수 (3전 전패)
    - 3개 이벤트 (날짜 다름)
    - 3개 매치 (KO/TKO, Submission, Decision)
    - round=0 통계 (전체 합산)
    - ranking 1개
    """
    session = clean_test_session

    # === Fighters ===
    fighter_a = FighterModel(
        name="Detail Test Fighter A",
        nickname="The Tester",
        wins=3, losses=0, draws=0,
        stance="Southpaw",
        belt=True,
        height_cm=180.0,
        weight_kg=77.0,
        reach_cm=185.0,
        birthdate="1991-10-27",
        nationality="Russia",
    )
    fighter_b = FighterModel(
        name="Detail Test Fighter B",
        nickname="The Opponent",
        wins=5, losses=3, draws=0,
        stance="Orthodox",
        nationality="United States",
    )
    session.add_all([fighter_a, fighter_b])
    await session.flush()

    # === Rankings ===
    ranking = RankingModel(fighter_id=fighter_a.id, weight_class_id=4, ranking=0)  # champion
    session.add(ranking)
    await session.flush()

    # === Events (oldest → newest) ===
    events = [
        EventModel(name="UFC 301", event_date=date(2024, 1, 15), location="Las Vegas"),
        EventModel(name="UFC 302", event_date=date(2024, 6, 1), location="New York"),
        EventModel(name="UFC 303", event_date=date(2024, 9, 10), location="Abu Dhabi"),
    ]
    session.add_all(events)
    await session.flush()

    # === Matches ===
    matches = [
        MatchModel(
            event_id=events[0].id, weight_class_id=4,
            method="KO/TKO", result_round=1, time="2:30",
            order=1, is_main_event=False,
        ),
        MatchModel(
            event_id=events[1].id, weight_class_id=4,
            method="Submission", result_round=2, time="4:15",
            order=1, is_main_event=True,
        ),
        MatchModel(
            event_id=events[2].id, weight_class_id=4,
            method="Decision - Unanimous", result_round=3, time="15:00",
            order=1, is_main_event=True,
        ),
    ]
    session.add_all(matches)
    await session.flush()

    # === FighterMatch (A wins all 3) ===
    fms_a = []
    fms_b = []
    for match in matches:
        fm_a = FighterMatchModel(fighter_id=fighter_a.id, match_id=match.id, result="Win")
        fm_b = FighterMatchModel(fighter_id=fighter_b.id, match_id=match.id, result="Loss")
        fms_a.append(fm_a)
        fms_b.append(fm_b)
    session.add_all(fms_a + fms_b)
    await session.flush()

    # === BasicMatchStatModel (round=0 — 전체 합산) ===
    basic_stats_a = [
        BasicMatchStatModel(
            fighter_match_id=fms_a[0].id, round=0,
            knockdowns=1, sig_str_landed=30, sig_str_attempted=50,
            total_str_landed=40, total_str_attempted=60,
            td_landed=2, td_attempted=3,
            control_time_seconds=120, submission_attempts=0,
        ),
        BasicMatchStatModel(
            fighter_match_id=fms_a[1].id, round=0,
            knockdowns=0, sig_str_landed=25, sig_str_attempted=45,
            total_str_landed=35, total_str_attempted=55,
            td_landed=3, td_attempted=5,
            control_time_seconds=200, submission_attempts=2,
        ),
        BasicMatchStatModel(
            fighter_match_id=fms_a[2].id, round=0,
            knockdowns=0, sig_str_landed=45, sig_str_attempted=80,
            total_str_landed=60, total_str_attempted=95,
            td_landed=1, td_attempted=2,
            control_time_seconds=100, submission_attempts=1,
        ),
    ]
    session.add_all(basic_stats_a)
    await session.flush()

    # === SigStrMatchStatModel (round=0 — 전체 합산) ===
    sig_str_stats_a = [
        SigStrMatchStatModel(
            fighter_match_id=fms_a[0].id, round=0,
            head_strikes_landed=15, head_strikes_attempts=25,
            body_strikes_landed=10, body_strikes_attempts=15,
            leg_strikes_landed=5, leg_strikes_attempts=10,
            clinch_strikes_landed=2, clinch_strikes_attempts=3,
            ground_strikes_landed=1, ground_strikes_attempts=2,
        ),
        SigStrMatchStatModel(
            fighter_match_id=fms_a[1].id, round=0,
            head_strikes_landed=12, head_strikes_attempts=22,
            body_strikes_landed=8, body_strikes_attempts=13,
            leg_strikes_landed=5, leg_strikes_attempts=10,
            clinch_strikes_landed=3, clinch_strikes_attempts=5,
            ground_strikes_landed=2, ground_strikes_attempts=3,
        ),
        SigStrMatchStatModel(
            fighter_match_id=fms_a[2].id, round=0,
            head_strikes_landed=25, head_strikes_attempts=40,
            body_strikes_landed=12, body_strikes_attempts=25,
            leg_strikes_landed=8, leg_strikes_attempts=15,
            clinch_strikes_landed=1, clinch_strikes_attempts=2,
            ground_strikes_landed=0, ground_strikes_attempts=0,
        ),
    ]
    session.add_all(sig_str_stats_a)
    await session.flush()

    return {
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "events": events,
        "matches": matches,
        "fms_a": fms_a,
        "fms_b": fms_b,
        "ranking": ranking,
    }


@pytest_asyncio.fixture
async def fighter_no_matches(clean_test_session):
    """경기 기록이 없는 파이터"""
    fighter = FighterModel(
        name="No Match Fighter",
        wins=0, losses=0, draws=0,
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()
    return fighter


# =============================================================================
# Helper 함수 단위 테스트
# =============================================================================

class TestCalcCurrentStreak:
    def test_win_streak(self):
        """연승 계산"""
        rows = [
            {"result": "Win"},
            {"result": "Win"},
            {"result": "Win"},
            {"result": "Loss"},
        ]
        assert _calc_current_streak(rows) == {"type": "win", "count": 3}

    def test_loss_streak(self):
        """연패 계산"""
        rows = [
            {"result": "Loss"},
            {"result": "Loss"},
            {"result": "Win"},
        ]
        assert _calc_current_streak(rows) == {"type": "loss", "count": 2}

    def test_single_result(self):
        """단일 경기"""
        rows = [{"result": "Win"}]
        assert _calc_current_streak(rows) == {"type": "win", "count": 1}

    def test_empty_rows(self):
        """경기 없음"""
        assert _calc_current_streak([]) == {"type": "none", "count": 0}

    def test_draw_first(self):
        """첫 경기가 무승부"""
        rows = [{"result": "Draw"}, {"result": "Win"}]
        assert _calc_current_streak(rows) == {"type": "none", "count": 0}

    def test_none_result(self):
        """result가 None인 경우"""
        rows = [{"result": None}]
        assert _calc_current_streak(rows) == {"type": "none", "count": 0}

    def test_case_insensitive(self):
        """대소문자 무관"""
        rows = [{"result": "win"}, {"result": "WIN"}, {"result": "Loss"}]
        assert _calc_current_streak(rows) == {"type": "win", "count": 2}


class TestCalcAge:
    def test_with_date_object(self):
        """date 객체로 나이 계산"""
        bd = date.today() - timedelta(days=365 * 30 + 7)  # 약 30세
        age = _calc_age(bd)
        assert age == 30

    def test_with_string(self):
        """문자열로 나이 계산"""
        age = _calc_age("1991-10-27")
        assert isinstance(age, int)
        assert age > 30

    def test_none(self):
        """None이면 None 반환"""
        assert _calc_age(None) is None

    def test_invalid_string(self):
        """잘못된 문자열이면 None 반환"""
        assert _calc_age("not-a-date") is None


# =============================================================================
# Repository 테스트: get_fight_history
# =============================================================================

@pytest.mark.asyncio
async def test_get_fight_history_success(fighter_detail_data, clean_test_session):
    """파이터의 경기 이력을 정상 조회"""
    data = fighter_detail_data
    fighter_a = data["fighter_a"]

    rows = await fighter_repo.get_fight_history(clean_test_session, fighter_a.id)

    # 3경기 조회
    assert len(rows) == 3

    # 날짜 내림차순 (newest first)
    assert rows[0]["event_name"] == "UFC 303"
    assert rows[1]["event_name"] == "UFC 302"
    assert rows[2]["event_name"] == "UFC 301"

    # 첫 번째 row 필드 확인
    first = rows[0]
    assert first["result"] == "Win"
    assert first["method"] == "Decision - Unanimous"
    assert first["result_round"] == 3
    assert first["is_main_event"] is True
    assert first["opponent_id"] == data["fighter_b"].id
    assert first["opponent_name"] == "Detail Test Fighter B"
    assert first["opponent_nationality"] == "United States"
    assert first["fighter_match_id"] is not None


@pytest.mark.asyncio
async def test_get_fight_history_no_matches(fighter_no_matches, clean_test_session):
    """경기가 없는 파이터의 이력 조회"""
    rows = await fighter_repo.get_fight_history(clean_test_session, fighter_no_matches.id)
    assert rows == []


@pytest.mark.asyncio
async def test_get_fight_history_nonexistent_fighter(clean_test_session):
    """존재하지 않는 파이터 ID"""
    rows = await fighter_repo.get_fight_history(clean_test_session, 99999)
    assert rows == []


# =============================================================================
# Repository 테스트: get_per_match_stats
# =============================================================================

@pytest.mark.asyncio
async def test_get_per_match_stats_success(fighter_detail_data, clean_test_session):
    """경기별 스탯 배치 조회"""
    fms_a = fighter_detail_data["fms_a"]
    fm_ids = [fm.id for fm in fms_a]

    stats_map = await fighter_repo.get_per_match_stats(clean_test_session, fm_ids)

    # 3개 fighter_match에 대해 모두 스탯 존재
    assert len(stats_map) == 3

    for fm_id in fm_ids:
        assert fm_id in stats_map
        assert "basic" in stats_map[fm_id]
        assert "sig_str" in stats_map[fm_id]

    # 첫 번째 매치 basic 스탯 값 확인
    basic_0 = stats_map[fms_a[0].id]["basic"]
    assert basic_0.knockdowns == 1
    assert basic_0.sig_str_landed == 30
    assert basic_0.td_landed == 2

    # 첫 번째 매치 sig_str 스탯 값 확인
    sig_str_0 = stats_map[fms_a[0].id]["sig_str"]
    assert sig_str_0.head_strikes_landed == 15
    assert sig_str_0.body_strikes_landed == 10
    assert sig_str_0.leg_strikes_landed == 5


@pytest.mark.asyncio
async def test_get_per_match_stats_empty_list(clean_test_session):
    """빈 리스트면 빈 dict 반환"""
    stats_map = await fighter_repo.get_per_match_stats(clean_test_session, [])
    assert stats_map == {}


@pytest.mark.asyncio
async def test_get_per_match_stats_nonexistent_ids(clean_test_session):
    """존재하지 않는 ID들"""
    stats_map = await fighter_repo.get_per_match_stats(clean_test_session, [99998, 99999])
    assert stats_map == {}


# =============================================================================
# Repository 테스트: get_finish_breakdown
# =============================================================================

@pytest.mark.asyncio
async def test_get_finish_breakdown_success(fighter_detail_data, clean_test_session):
    """피니시 방법별 집계"""
    fighter_a = fighter_detail_data["fighter_a"]

    breakdown = await fighter_repo.get_finish_breakdown(clean_test_session, fighter_a.id)

    assert breakdown["ko_tko"] == 1
    assert breakdown["submission"] == 1
    assert breakdown["decision"] == 1


@pytest.mark.asyncio
async def test_get_finish_breakdown_no_wins(fighter_no_matches, clean_test_session):
    """승리가 없는 파이터"""
    breakdown = await fighter_repo.get_finish_breakdown(clean_test_session, fighter_no_matches.id)

    assert breakdown["ko_tko"] == 0
    assert breakdown["submission"] == 0
    assert breakdown["decision"] == 0


@pytest.mark.asyncio
async def test_get_finish_breakdown_nonexistent_fighter(clean_test_session):
    """존재하지 않는 파이터"""
    breakdown = await fighter_repo.get_finish_breakdown(clean_test_session, 99999)

    assert breakdown["ko_tko"] == 0
    assert breakdown["submission"] == 0
    assert breakdown["decision"] == 0


# =============================================================================
# Service 테스트: get_fighter_detail — 성공 케이스
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_detail_success(fighter_detail_data, clean_test_session):
    """정상적으로 파이터 상세 정보를 조회"""
    fighter_a = fighter_detail_data["fighter_a"]

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter_a.id)

    assert isinstance(result, FighterDetailResponseDTO)

    # === Profile ===
    profile = result.profile
    assert profile.id == fighter_a.id
    assert profile.name == "Detail Test Fighter A"
    assert profile.nickname == "The Tester"
    assert profile.nationality == "Russia"
    assert profile.stance == "Southpaw"
    assert profile.belt is True
    assert profile.height_cm == 180.0
    assert profile.weight_kg == 77.0
    assert profile.reach_cm == 185.0
    assert profile.birthdate == "1991-10-27"
    assert profile.age is not None
    assert profile.age > 30

    # rankings
    assert "lightweight" in profile.rankings
    assert profile.rankings["lightweight"] == 0  # champion


@pytest.mark.asyncio
async def test_get_fighter_detail_record(fighter_detail_data, clean_test_session):
    """전적 정보 확인"""
    result = await fighter_services.get_fighter_detail(
        clean_test_session, fighter_detail_data["fighter_a"].id
    )
    record = result.record

    assert record.wins == 3
    assert record.losses == 0
    assert record.draws == 0
    assert record.win_rate == 100.0

    # finish breakdown
    assert record.finish_breakdown.ko_tko == 1
    assert record.finish_breakdown.submission == 1
    assert record.finish_breakdown.decision == 1

    # current streak (3연승)
    assert record.current_streak["type"] == "win"
    assert record.current_streak["count"] == 3


@pytest.mark.asyncio
async def test_get_fighter_detail_stats(fighter_detail_data, clean_test_session):
    """커리어 통계 확인"""
    result = await fighter_services.get_fighter_detail(
        clean_test_session, fighter_detail_data["fighter_a"].id
    )

    assert result.stats is not None

    # Striking
    striking = result.stats.striking
    assert striking.sig_str_landed == 100  # 30+25+45
    assert striking.sig_str_attempted == 175  # 50+45+80
    assert striking.knockdowns == 1
    assert striking.match_count == 3
    assert striking.sig_str_accuracy > 0

    # head/body/leg (from sig_str aggregate)
    assert striking.head_landed == 52  # 15+12+25
    assert striking.body_landed == 30  # 10+8+12
    assert striking.leg_landed == 18  # 5+5+8

    # Grappling
    grappling = result.stats.grappling
    assert grappling.td_landed == 6  # 2+3+1
    assert grappling.td_attempted == 10  # 3+5+2
    assert grappling.control_time_seconds == 420  # 120+200+100
    assert grappling.avg_control_time_seconds == 140  # 420 // 3
    assert grappling.submission_attempts == 3  # 0+2+1
    assert grappling.match_count == 3


@pytest.mark.asyncio
async def test_get_fighter_detail_fight_history(fighter_detail_data, clean_test_session):
    """경기 이력 확인"""
    result = await fighter_services.get_fighter_detail(
        clean_test_session, fighter_detail_data["fighter_a"].id
    )

    assert len(result.fight_history) == 3

    # 날짜 내림차순 — 가장 최근 경기
    latest = result.fight_history[0]
    assert latest.result == "Win"
    assert latest.method == "Decision - Unanimous"
    assert latest.round == 3
    assert latest.time == "15:00"
    assert latest.event_name == "UFC 303"
    assert latest.event_date == date(2024, 9, 10)
    assert latest.weight_class == "lightweight"
    assert latest.is_main_event is True

    # opponent
    assert latest.opponent.id == fighter_detail_data["fighter_b"].id
    assert latest.opponent.name == "Detail Test Fighter B"
    assert latest.opponent.nationality == "United States"


@pytest.mark.asyncio
async def test_get_fighter_detail_per_match_stats(fighter_detail_data, clean_test_session):
    """경기별 상세 스탯 포함 확인"""
    result = await fighter_services.get_fighter_detail(
        clean_test_session, fighter_detail_data["fighter_a"].id
    )

    # 모든 경기에 stats 존재
    for fight in result.fight_history:
        assert fight.stats is not None
        assert fight.stats.basic is not None
        assert fight.stats.sig_str is not None

    # 가장 오래된 경기 (KO, index=2) basic stats
    oldest = result.fight_history[2]
    assert oldest.method == "KO/TKO"
    assert oldest.stats.basic.knockdowns == 1
    assert oldest.stats.basic.sig_str_landed == 30
    assert oldest.stats.basic.td_landed == 2

    # sig_str stats
    assert oldest.stats.sig_str.head_landed == 15
    assert oldest.stats.sig_str.body_landed == 10
    assert oldest.stats.sig_str.leg_landed == 5
    assert oldest.stats.sig_str.clinch_landed == 2
    assert oldest.stats.sig_str.ground_landed == 1


# =============================================================================
# Service 테스트: get_fighter_detail — 엣지 케이스
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_detail_not_found(clean_test_session):
    """존재하지 않는 파이터 ID로 조회 시 예외 발생"""
    with pytest.raises(FighterNotFoundError):
        await fighter_services.get_fighter_detail(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_fighter_detail_invalid_id_negative(clean_test_session):
    """음수 ID 처리"""
    with pytest.raises(FighterValidationError, match="fighter_id must be a positive integer"):
        await fighter_services.get_fighter_detail(clean_test_session, -1)


@pytest.mark.asyncio
async def test_get_fighter_detail_invalid_id_zero(clean_test_session):
    """0 ID 처리"""
    with pytest.raises(FighterValidationError, match="fighter_id must be a positive integer"):
        await fighter_services.get_fighter_detail(clean_test_session, 0)


@pytest.mark.asyncio
async def test_get_fighter_detail_no_matches(fighter_no_matches, clean_test_session):
    """경기 없는 파이터 — stats=None, fight_history=[]"""
    result = await fighter_services.get_fighter_detail(clean_test_session, fighter_no_matches.id)

    assert isinstance(result, FighterDetailResponseDTO)

    # profile 기본 정보
    assert result.profile.name == "No Match Fighter"
    assert result.profile.rankings == {}

    # record
    assert result.record.wins == 0
    assert result.record.losses == 0
    assert result.record.draws == 0
    assert result.record.win_rate == 0.0
    assert result.record.current_streak == {"type": "none", "count": 0}
    assert result.record.finish_breakdown.ko_tko == 0

    # stats null
    assert result.stats is None

    # fight_history 빈 배열
    assert result.fight_history == []


@pytest.mark.asyncio
async def test_get_fighter_detail_no_birthdate(clean_test_session):
    """birthdate 없는 파이터 — age=None"""
    fighter = FighterModel(
        name="No Birthdate Fighter",
        wins=5, losses=1, draws=0,
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter.id)

    assert result.profile.birthdate is None
    assert result.profile.age is None


@pytest.mark.asyncio
async def test_get_fighter_detail_no_rankings(clean_test_session):
    """랭킹 없는 파이터 — rankings = {}"""
    fighter = FighterModel(
        name="Unranked Detail Fighter",
        wins=8, losses=2, draws=1,
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter.id)

    assert result.profile.rankings == {}


@pytest.mark.asyncio
async def test_get_fighter_detail_win_rate_calculation(clean_test_session):
    """win_rate 정확도 확인 (소수점 1자리)"""
    fighter = FighterModel(
        name="Win Rate Test Fighter",
        wins=26, losses=1, draws=0,
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter.id)

    # 26 / 27 * 100 = 96.296... → 96.3
    assert result.record.win_rate == 96.3


@pytest.mark.asyncio
async def test_get_fighter_detail_zero_physical_stats(clean_test_session):
    """height/weight/reach가 0이면 None으로 반환"""
    fighter = FighterModel(
        name="Zero Stats Fighter",
        wins=1, losses=0, draws=0,
        height_cm=0, weight_kg=0, reach_cm=0,
    )
    clean_test_session.add(fighter)
    await clean_test_session.flush()

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter.id)

    assert result.profile.height_cm is None
    assert result.profile.weight_kg is None
    assert result.profile.reach_cm is None


# =============================================================================
# Service 테스트: current_streak 시나리오
# =============================================================================

@pytest.mark.asyncio
async def test_get_fighter_detail_loss_streak(clean_test_session):
    """연패 streak 확인"""
    session = clean_test_session

    fighter_a = FighterModel(name="Loss Streak Fighter", wins=3, losses=2, draws=0)
    fighter_b = FighterModel(name="Winner Fighter", wins=5, losses=0, draws=0)
    session.add_all([fighter_a, fighter_b])
    await session.flush()

    events = [
        EventModel(name="Event Old", event_date=date(2024, 1, 1), location="A"),
        EventModel(name="Event Mid", event_date=date(2024, 6, 1), location="B"),
        EventModel(name="Event New", event_date=date(2024, 9, 1), location="C"),
    ]
    session.add_all(events)
    await session.flush()

    # 시간순: Win → Loss → Loss (newest first: Loss, Loss, Win)
    matches = [
        MatchModel(event_id=events[0].id, weight_class_id=4, method="U-DEC",
                   result_round=3, time="15:00", order=1, is_main_event=False),
        MatchModel(event_id=events[1].id, weight_class_id=4, method="KO/TKO",
                   result_round=1, time="3:00", order=1, is_main_event=False),
        MatchModel(event_id=events[2].id, weight_class_id=4, method="Submission",
                   result_round=2, time="4:00", order=1, is_main_event=False),
    ]
    session.add_all(matches)
    await session.flush()

    fms = [
        FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[0].id, result="Win"),
        FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[0].id, result="Loss"),
        FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[1].id, result="Loss"),
        FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[1].id, result="Win"),
        FighterMatchModel(fighter_id=fighter_a.id, match_id=matches[2].id, result="Loss"),
        FighterMatchModel(fighter_id=fighter_b.id, match_id=matches[2].id, result="Win"),
    ]
    session.add_all(fms)
    await session.flush()

    result = await fighter_services.get_fighter_detail(session, fighter_a.id)

    # newest first: Loss, Loss, Win → 2연패
    assert result.record.current_streak["type"] == "loss"
    assert result.record.current_streak["count"] == 2


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_fighter_detail_full_workflow(fighter_detail_data, clean_test_session):
    """전체 Fighter Detail 워크플로우 통합 검증"""
    data = fighter_detail_data
    fighter_a = data["fighter_a"]

    result = await fighter_services.get_fighter_detail(clean_test_session, fighter_a.id)

    # 1. 전체 응답 구조 확인
    assert result.profile is not None
    assert result.record is not None
    assert result.stats is not None
    assert len(result.fight_history) == 3

    # 2. Profile → Record → Stats → FightHistory 데이터 일관성
    assert result.profile.name == "Detail Test Fighter A"
    assert result.record.wins == 3
    assert result.record.win_rate == 100.0
    assert result.stats.striking.match_count == 3
    assert result.stats.grappling.match_count == 3

    # 3. fight_history의 모든 항목에 opponent과 stats 존재
    for fight in result.fight_history:
        assert fight.opponent is not None
        assert fight.opponent.id == data["fighter_b"].id
        assert fight.stats is not None

    # 4. 시간순 정렬: 최신이 먼저
    dates = [f.event_date for f in result.fight_history if f.event_date]
    assert dates == sorted(dates, reverse=True)

    # 5. sig_str accuracy 계산 확인 (100/175 * 100 ≈ 57.1)
    assert result.stats.striking.sig_str_accuracy == pytest.approx(57.1, abs=0.1)

    # 6. td accuracy 계산 확인 (6/10 * 100 = 60.0)
    assert result.stats.grappling.td_accuracy == 60.0
