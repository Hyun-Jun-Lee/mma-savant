"""
Dashboard Repository 테스트
실제 테스트 DB를 사용하여 모든 집계 쿼리 검증

fixture 데이터 구성 (conftest.py dashboard_data):
  - wc=4 (LW) 7매치 + wc=5 (WW) 2매치 = 총 9매치
  - Fighter A: 7전 전승 (wc4: 5전, wc5: 2전)
  - Fighter B: 7전 3승4패 (wc4: 2승3패, wc5: 0승2패)
  - Fighter C: 4전 전패 (wc4 only → HAVING >= 5 제외)
"""
import pytest
from pytest import approx
from dashboard import repositories as dashboard_repo


# =============================================================================
# Tab 1: Home
# =============================================================================

@pytest.mark.asyncio
async def test_get_summary(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_summary(clean_test_session)
    assert result["total_fighters"] == 3
    assert result["total_matches"] == 9
    assert result["total_events"] == 7


@pytest.mark.asyncio
async def test_get_recent_events(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_recent_events(clean_test_session)
    assert len(result) == 5
    dates = [r["event_date"] for r in result]
    assert dates == sorted(dates, reverse=True)
    for event in result:
        assert "id" in event
        assert "name" in event
        assert "location" in event
        assert "total_fights" in event
        assert "main_event" in event


@pytest.mark.asyncio
async def test_get_recent_events_main_event(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_recent_events(clean_test_session)
    oldest = result[-1]
    assert oldest["main_event"] is not None
    assert "vs" in oldest["main_event"]


@pytest.mark.asyncio
async def test_get_upcoming_events(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_upcoming_events(clean_test_session)
    assert len(result) == 2
    dates = [r["event_date"] for r in result]
    assert dates == sorted(dates)
    for event in result:
        assert event["days_until"] > 0


@pytest.mark.asyncio
async def test_get_rankings(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_rankings(clean_test_session)
    assert len(result) == 2
    for row in result:
        assert row["weight_class_id"] == 4
        assert row["weight_class"].lower() == "lightweight"
    assert result[0]["ranking"] == 1
    assert result[1]["ranking"] == 2
    assert result[0]["fighter_name"] == "Alpha Fighter"
    assert result[1]["fighter_name"] == "Beta Fighter"


# =============================================================================
# Tab 2: Overview
# =============================================================================

@pytest.mark.asyncio
async def test_get_finish_methods(clean_test_session, dashboard_data):
    """전체 9매치: KO/TKO=3, SUB=3, U-DEC=1, S-DEC=1, M-DEC=1"""
    result = await dashboard_repo.get_finish_methods(clean_test_session)
    categories = {r["method_category"]: r["count"] for r in result}
    assert categories["KO/TKO"] == 3
    assert categories["SUB"] == 3
    assert categories["U-DEC"] == 1
    assert categories["S-DEC"] == 1
    assert categories["M-DEC"] == 1


@pytest.mark.asyncio
async def test_get_finish_methods_with_weight_class(clean_test_session, dashboard_data):
    """wc=4만 필터: 7매치 (전체 9에서 wc=5 2매치 제외)"""
    result = await dashboard_repo.get_finish_methods(clean_test_session, weight_class_id=4)
    total = sum(r["count"] for r in result)
    assert total == 7
    categories = {r["method_category"]: r["count"] for r in result}
    assert categories["KO/TKO"] == 2
    assert categories["SUB"] == 2


@pytest.mark.asyncio
async def test_get_finish_methods_no_match(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_finish_methods(clean_test_session, weight_class_id=999)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_weight_class_activity(clean_test_session, dashboard_data):
    """2개 체급: LW 7전, WW 2전"""
    result = await dashboard_repo.get_weight_class_activity(clean_test_session)
    assert len(result) == 2
    wc_map = {r["weight_class"].lower(): r for r in result}

    lw = wc_map["lightweight"]
    assert lw["total_fights"] == 7
    assert lw["ko_tko_count"] == 2
    assert lw["sub_count"] == 2
    assert float(lw["finish_rate"]) == approx(57.1, abs=0.1)
    assert float(lw["ko_tko_rate"]) == approx(28.6, abs=0.1)

    ww = wc_map["welterweight"]
    assert ww["total_fights"] == 2
    assert ww["ko_tko_count"] == 1
    assert ww["sub_count"] == 1
    assert float(ww["finish_rate"]) == approx(100.0, abs=0.1)


@pytest.mark.asyncio
async def test_get_events_timeline(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_events_timeline(clean_test_session)
    assert len(result) >= 1
    years = [r["year"] for r in result]
    assert years == sorted(years)
    total_events = sum(r["event_count"] for r in result)
    assert total_events == 7


@pytest.mark.asyncio
async def test_get_leaderboard_wins_no_filter(clean_test_session, dashboard_data):
    """필터 없이 fighter 테이블의 wins 컬럼 기준 정렬"""
    result = await dashboard_repo.get_leaderboard_wins(clean_test_session)
    assert len(result) >= 3
    assert result[0]["name"] == "Alpha Fighter"
    assert result[0]["wins"] == 10


@pytest.mark.asyncio
async def test_get_leaderboard_wins_with_filter(clean_test_session, dashboard_data):
    """체급 필터: fighter_match에서 실시간 집계, wc=4에서 A 5승"""
    result = await dashboard_repo.get_leaderboard_wins(clean_test_session, weight_class_id=4)
    assert len(result) >= 2
    assert result[0]["name"] == "Alpha Fighter"
    assert result[0]["wins"] == 5


@pytest.mark.asyncio
async def test_get_leaderboard_winrate_min10(clean_test_session, dashboard_data):
    """min_fights=10: A(12전 83.3%), B(13전 61.5%) 통과, C(5전) 제외"""
    result = await dashboard_repo.get_leaderboard_winrate(clean_test_session, min_fights=10)
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert float(result[0]["win_rate"]) == approx(83.3, abs=0.1)
    assert result[1]["name"] == "Beta Fighter"
    assert float(result[1]["win_rate"]) == approx(61.5, abs=0.1)


@pytest.mark.asyncio
async def test_get_leaderboard_winrate_min30(clean_test_session, dashboard_data):
    """min_fights=30: 아무도 해당 없음"""
    result = await dashboard_repo.get_leaderboard_winrate(clean_test_session, min_fights=30)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_leaderboard_winrate_with_filter(clean_test_session, dashboard_data):
    """wc=4 + min_fights=5: A(5전 100%), B(5전 40%)"""
    result = await dashboard_repo.get_leaderboard_winrate(
        clean_test_session, min_fights=5, weight_class_id=4
    )
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert float(result[0]["win_rate"]) == 100.0
    assert result[1]["name"] == "Beta Fighter"
    assert float(result[1]["win_rate"]) == 40.0


@pytest.mark.asyncio
async def test_get_fight_duration_rounds(clean_test_session, dashboard_data):
    """9매치: R1=3(match 0,2,7), R2=3(match 1,5,8), R3=3(match 3,4,6)"""
    result = await dashboard_repo.get_fight_duration_rounds(clean_test_session)
    rounds = {r["result_round"]: r for r in result}
    assert rounds[1]["fight_count"] == 3
    assert rounds[2]["fight_count"] == 3
    assert rounds[3]["fight_count"] == 3
    total_pct = float(sum(r["percentage"] for r in result))
    assert 99.9 <= total_pct <= 100.1


@pytest.mark.asyncio
async def test_get_fight_duration_avg_round(clean_test_session, dashboard_data):
    """(1+2+1+3+3+2+3+1+2)/9 = 18/9 = 2.0"""
    result = await dashboard_repo.get_fight_duration_avg_round(clean_test_session)
    assert isinstance(result, float)
    assert result == approx(2.0, abs=0.1)


# =============================================================================
# Tab 3: Striking
# =============================================================================

@pytest.mark.asyncio
async def test_get_strike_targets(clean_test_session, dashboard_data):
    """전체 18 fighter_match의 합계"""
    result = await dashboard_repo.get_strike_targets(clean_test_session)
    assert len(result) == 5
    targets = {r["target"]: r["landed"] for r in result}
    assert targets["Head"] == 358
    assert targets["Body"] == 206
    assert targets["Leg"] == 83
    assert targets["Clinch"] == 35
    assert targets["Ground"] == 31


@pytest.mark.asyncio
async def test_get_strike_targets_with_filter(clean_test_session, dashboard_data):
    """wc=4만: 전체(358)보다 적은 298 (wc=5 제외됨)"""
    result = await dashboard_repo.get_strike_targets(clean_test_session, weight_class_id=4)
    targets = {r["target"]: r["landed"] for r in result}
    assert targets["Head"] == 298
    assert targets["Body"] == 172
    assert targets["Leg"] == 71
    assert targets["Clinch"] == 29
    assert targets["Ground"] == 26


@pytest.mark.asyncio
async def test_get_strike_targets_no_match(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_strike_targets(clean_test_session, weight_class_id=999)
    assert len(result) == 5
    for r in result:
        assert r["landed"] == 0


@pytest.mark.asyncio
async def test_get_striking_accuracy(clean_test_session, dashboard_data):
    """HAVING >= 5전: A(7전 61.8%), B(7전 54.3%), C(4전) 제외"""
    result = await dashboard_repo.get_striking_accuracy(clean_test_session, min_fights=5)
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert float(result[0]["accuracy"]) == approx(61.8, abs=0.1)
    assert result[0]["total_sig_landed"] == 315
    assert result[0]["total_sig_attempted"] == 510
    assert result[1]["name"] == "Beta Fighter"
    assert float(result[1]["accuracy"]) == approx(54.3, abs=0.1)


@pytest.mark.asyncio
async def test_get_ko_tko_leaders(clean_test_session, dashboard_data):
    """A: KO/TKO 승리 = match 0, 1, 7 → 3"""
    result = await dashboard_repo.get_ko_tko_leaders(clean_test_session)
    assert len(result) == 1
    assert result[0]["name"] == "Alpha Fighter"
    assert result[0]["ko_tko_finishes"] == 3


@pytest.mark.asyncio
async def test_get_sig_strikes_per_fight(clean_test_session, dashboard_data):
    """HAVING >= 5전: A(315/7=45.0), B(228/7=32.57)"""
    result = await dashboard_repo.get_sig_strikes_per_fight(clean_test_session, min_fights=5)
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert float(result[0]["sig_str_per_fight"]) == approx(45.0, abs=0.1)
    assert result[1]["name"] == "Beta Fighter"
    assert float(result[1]["sig_str_per_fight"]) == approx(32.57, abs=0.1)


# =============================================================================
# Tab 4: Grappling
# =============================================================================

@pytest.mark.asyncio
async def test_get_takedown_accuracy(clean_test_session, dashboard_data):
    """HAVING >= 5전 AND td_attempted >= 10: A(17/27=63.0%), B(9/21=42.9%)"""
    result = await dashboard_repo.get_takedown_accuracy(clean_test_session, min_fights=5)
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert result[0]["total_td_landed"] == 17
    assert result[0]["total_td_attempted"] == 27
    assert float(result[0]["td_accuracy"]) == approx(63.0, abs=0.1)
    assert result[1]["name"] == "Beta Fighter"
    assert result[1]["total_td_landed"] == 9
    assert result[1]["total_td_attempted"] == 21
    assert float(result[1]["td_accuracy"]) == approx(42.9, abs=0.1)


@pytest.mark.asyncio
async def test_get_submission_techniques(clean_test_session, dashboard_data):
    """3종: Rear Naked Choke(wc4), Armbar(wc4), Guillotine(wc5)"""
    result = await dashboard_repo.get_submission_techniques(clean_test_session)
    techniques = {r["technique"]: r["count"] for r in result}
    assert len(techniques) == 3
    assert techniques["Rear Naked Choke"] == 1
    assert techniques["Armbar"] == 1
    assert techniques["Guillotine"] == 1


@pytest.mark.asyncio
async def test_get_submission_techniques_with_filter(clean_test_session, dashboard_data):
    """wc=4만: Guillotine(wc=5) 제외"""
    result = await dashboard_repo.get_submission_techniques(clean_test_session, weight_class_id=4)
    techniques = {r["technique"]: r["count"] for r in result}
    assert len(techniques) == 2
    assert "Guillotine" not in techniques


@pytest.mark.asyncio
async def test_get_control_time(clean_test_session, dashboard_data):
    """2개 체급: LW avg=124, WW avg=118"""
    result = await dashboard_repo.get_control_time(clean_test_session)
    assert len(result) == 2
    wc_map = {r["weight_class"].lower(): r for r in result}
    lw = wc_map["lightweight"]
    assert lw["avg_control_seconds"] == 124
    assert lw["total_fights"] == 7
    ww = wc_map["welterweight"]
    assert ww["avg_control_seconds"] in (117, 118)
    assert ww["total_fights"] == 2


@pytest.mark.asyncio
async def test_get_ground_strikes(clean_test_session, dashboard_data):
    """HAVING >= 5전: A(15/25=60.0%), B(9/18=50.0%)"""
    result = await dashboard_repo.get_ground_strikes(clean_test_session, min_fights=5)
    assert len(result) == 2
    assert result[0]["name"] == "Alpha Fighter"
    assert result[0]["total_ground_landed"] == 15
    assert float(result[0]["accuracy"]) == approx(60.0, abs=0.1)
    assert result[1]["name"] == "Beta Fighter"
    assert result[1]["total_ground_landed"] == 9
    assert float(result[1]["accuracy"]) == approx(50.0, abs=0.1)


@pytest.mark.asyncio
async def test_get_submission_efficiency_fighters(clean_test_session, dashboard_data):
    """HAVING sub_attempts >= 5 AND >= 5전: A(9시도 2성공), B(6시도 1성공)"""
    result = await dashboard_repo.get_submission_efficiency_fighters(clean_test_session, min_fights=5)
    assert len(result) == 2
    fighters = {r["name"]: r for r in result}
    assert fighters["Alpha Fighter"]["total_sub_attempts"] == 9
    assert fighters["Alpha Fighter"]["sub_finishes"] == 2
    assert fighters["Beta Fighter"]["total_sub_attempts"] == 6
    assert fighters["Beta Fighter"]["sub_finishes"] == 1


@pytest.mark.asyncio
async def test_get_submission_efficiency_avg_ratio(clean_test_session, dashboard_data):
    """전체: 3성공/15시도 = 0.200"""
    result = await dashboard_repo.get_submission_efficiency_avg_ratio(clean_test_session, min_fights=5)
    assert isinstance(result, float)
    assert result == approx(0.200, abs=0.01)


@pytest.mark.asyncio
async def test_get_submission_efficiency_avg_ratio_with_filter(clean_test_session, dashboard_data):
    """wc=4: 2성공/12시도 = 0.167 (전체 0.200과 다름)"""
    result = await dashboard_repo.get_submission_efficiency_avg_ratio(
        clean_test_session, weight_class_id=4, min_fights=5
    )
    assert result == approx(0.167, abs=0.01)


@pytest.mark.asyncio
async def test_get_submission_efficiency_no_match(clean_test_session, dashboard_data):
    result = await dashboard_repo.get_submission_efficiency_avg_ratio(
        clean_test_session, weight_class_id=999
    )
    assert result == 0.0
