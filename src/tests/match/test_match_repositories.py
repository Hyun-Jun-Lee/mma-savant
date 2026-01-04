"""
Match Repositories 테스트
match/repositories.py의 모든 repository 함수에 대한 포괄적인 테스트
"""
import pytest

from match import repositories as match_repo
from match.models import MatchSchema, FighterMatchSchema, BasicMatchStatSchema, SigStrMatchStatSchema
from match.dto import (
    FighterBasicStatsAggregateDTO,
    FighterSigStrStatsAggregateDTO,
    MatchWithResultDTO,
    MatchWithFightersDTO,
    MatchStatisticsDTO
)


@pytest.mark.asyncio
async def test_get_match_by_id_existing(sample_match, clean_test_session):
    """존재하는 매치 ID로 조회 테스트"""
    # When: Repository 함수 호출
    result = await match_repo.get_match_by_id(clean_test_session, sample_match.id)

    # Then: 올바른 MatchSchema 반환
    assert result is not None
    assert isinstance(result, MatchSchema)
    assert result.id == sample_match.id
    assert result.event_id == sample_match.event_id
    assert result.weight_class_id == sample_match.weight_class_id
    assert result.method == "Decision - Unanimous"
    assert result.result_round == 3
    assert result.time == "15:00"
    assert result.order == 1
    assert result.is_main_event is False


@pytest.mark.asyncio
async def test_get_match_by_id_nonexistent(clean_test_session):
    """존재하지 않는 매치 ID로 조회 테스트"""
    # When: 존재하지 않는 ID로 조회
    result = await match_repo.get_match_by_id(clean_test_session, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_matches_by_event_id(multiple_matches_for_event, clean_test_session):
    """이벤트 ID로 매치들 조회 테스트"""
    # Given: multiple_matches_for_event fixture 사용
    event, matches = multiple_matches_for_event

    # When: 이벤트 ID로 매치들 조회
    result = await match_repo.get_matches_by_event_id(clean_test_session, event.id)

    # Then: 모든 매치가 order 순으로 반환
    assert isinstance(result, list)
    assert len(result) == 3

    # order 순서대로 정렬되어 있는지 확인
    assert result[0].order == 1
    assert result[1].order == 2
    assert result[2].order == 3

    # 메인 이벤트가 마지막에 있는지 확인
    assert result[2].is_main_event is True
    assert result[0].is_main_event is False
    assert result[1].is_main_event is False

    # 모든 결과가 MatchSchema 타입인지 확인
    for match in result:
        assert isinstance(match, MatchSchema)
        assert match.event_id == event.id


@pytest.mark.asyncio
async def test_get_matches_between_fighters(fighters_with_multiple_matches, clean_test_session):
    """두 파이터 간의 모든 매치 조회 테스트"""
    # Given: fighters_with_multiple_matches fixture 사용
    fighters, matches, fighter_matches = fighters_with_multiple_matches

    # When: 두 파이터 간 매치 조회
    result = await match_repo.get_matches_between_fighters(
        clean_test_session, fighters[0].id, fighters[1].id
    )

    # Then: 모든 매치가 반환
    assert isinstance(result, list)
    assert len(result) == 3

    # 모든 결과가 MatchSchema 타입인지 확인
    for match in result:
        assert isinstance(match, MatchSchema)

    # 매치 방법들이 올바른지 확인
    methods = [match.method for match in result]
    assert "Decision" in methods
    assert "KO/TKO" in methods
    assert "Submission" in methods


@pytest.mark.asyncio
async def test_get_basic_match_stats(match_with_statistics, clean_test_session):
    """기본 매치 통계 조회 테스트"""
    # Given: match_with_statistics fixture 사용
    match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics

    # When: 첫 번째 파이터의 기본 통계 조회
    result = await match_repo.get_basic_match_stats(
        clean_test_session, fighters[0].id, match.id
    )

    # Then: 올바른 기본 통계 반환
    assert result is not None
    assert isinstance(result, BasicMatchStatSchema)
    assert result.fighter_match_id == fighter_matches[0].id
    assert result.knockdowns == 1
    assert result.control_time_seconds == 240
    assert result.submission_attempts == 2
    assert result.sig_str_landed == 45
    assert result.sig_str_attempted == 75
    assert result.td_landed == 3
    assert result.td_attempted == 6
    assert result.round == 3


@pytest.mark.asyncio
async def test_get_sig_str_match_stats(match_with_statistics, clean_test_session):
    """스트라이크 상세 통계 조회 테스트"""
    # Given: match_with_statistics fixture 사용
    match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics

    # When: 첫 번째 파이터의 스트라이크 통계 조회
    result = await match_repo.get_sig_str_match_stats(
        clean_test_session, fighters[0].id, match.id
    )

    # Then: 올바른 스트라이크 통계 반환
    assert result is not None
    assert isinstance(result, SigStrMatchStatSchema)
    assert result.fighter_match_id == fighter_matches[0].id
    assert result.head_strikes_landed == 25
    assert result.head_strikes_attempts == 40
    assert result.body_strikes_landed == 15
    assert result.body_strikes_attempts == 25
    assert result.leg_strikes_landed == 5
    assert result.leg_strikes_attempts == 10
    assert result.takedowns_landed == 3
    assert result.takedowns_attempts == 6
    assert result.round == 3


@pytest.mark.asyncio
async def test_get_basic_match_stats_nonexistent(clean_test_session):
    """존재하지 않는 파이터/매치 조합 기본 통계 조회 테스트"""
    # When: 존재하지 않는 조합으로 조회
    result = await match_repo.get_basic_match_stats(clean_test_session, 99999, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_sig_str_match_stats_nonexistent(clean_test_session):
    """존재하지 않는 파이터/매치 조합 스트라이크 통계 조회 테스트"""
    # When: 존재하지 않는 조합으로 조회
    result = await match_repo.get_sig_str_match_stats(clean_test_session, 99999, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_fighters_matches(fighters_with_multiple_matches, clean_test_session):
    """파이터의 모든 매치 조회 테스트"""
    # Given: fighters_with_multiple_matches fixture 사용
    fighters, matches, fighter_matches = fighters_with_multiple_matches

    # When: 첫 번째 파이터의 모든 매치 조회
    result = await match_repo.get_fighters_matches(clean_test_session, fighters[0].id)

    # Then: 모든 파이터 매치가 반환
    assert isinstance(result, list)
    assert len(result) == 3

    # 모든 결과가 FighterMatchSchema 타입인지 확인
    for fighter_match in result:
        assert isinstance(fighter_match, FighterMatchSchema)
        assert fighter_match.fighter_id == fighters[0].id

    # 결과 확인 - 첫 번째 파이터가 모든 경기에서 승리
    results = [fm.result for fm in result]
    assert all(r == "win" for r in results)


@pytest.mark.asyncio
async def test_get_fighters_matches_with_limit(fighters_with_multiple_matches, clean_test_session):
    """파이터의 매치 조회 제한 테스트"""
    # Given: fighters_with_multiple_matches fixture 사용
    fighters, matches, fighter_matches = fighters_with_multiple_matches

    # When: 첫 번째 파이터의 최근 2개 매치만 조회
    result = await match_repo.get_fighters_matches(clean_test_session, fighters[0].id, limit=2)

    # Then: 2개의 파이터 매치만 반환
    assert isinstance(result, list)
    assert len(result) == 2

    # 모든 결과가 FighterMatchSchema 타입인지 확인
    for fighter_match in result:
        assert isinstance(fighter_match, FighterMatchSchema)
        assert fighter_match.fighter_id == fighters[0].id


@pytest.mark.asyncio
async def test_get_fighter_match_by_match_id(match_with_fighters, clean_test_session):
    """매치 ID로 파이터 매치 관계 조회 테스트"""
    # Given: match_with_fighters fixture 사용
    match, fighters, fighter_matches = match_with_fighters

    # When: 매치 ID로 파이터 매치 관계 조회
    result = await match_repo.get_fighter_match_by_match_id(clean_test_session, match.id)

    # Then: 두 파이터의 매치 관계가 반환
    assert isinstance(result, list)
    assert len(result) == 2

    # 모든 결과가 FighterMatchSchema 타입인지 확인
    for fighter_match in result:
        assert isinstance(fighter_match, FighterMatchSchema)
        assert fighter_match.match_id == match.id

    # 결과 확인 (winner와 loser)
    results = [fm.result for fm in result]
    assert "win" in results
    assert "loss" in results


@pytest.mark.asyncio
async def test_get_match_fighter_mapping(match_with_fighters, clean_test_session):
    """매치 파이터 매핑 조회 테스트"""
    # Given: match_with_fighters fixture 사용
    match, fighters, fighter_matches = match_with_fighters

    # When: 매치 파이터 매핑 조회 (매개변수 없음)
    result = await match_repo.get_match_fighter_mapping(clean_test_session)

    # Then: detail_url을 키로 하는 매핑 반환
    assert isinstance(result, dict)

    # match.detail_url이 키로 있는지 확인
    if match.detail_url:
        assert match.detail_url in result
        match_mapping = result[match.detail_url]
        assert isinstance(match_mapping, dict)

        # 파이터 ID와 FighterMatchSchema 매핑 확인
        for fighter_id, fighter_match_schema in match_mapping.items():
            assert isinstance(fighter_id, int)
            assert isinstance(fighter_match_schema, FighterMatchSchema)
            assert fighter_match_schema.fighter_id == fighter_id
            assert fighter_match_schema.match_id == match.id


@pytest.mark.asyncio
async def test_get_fighter_basic_stats_aggregate(match_with_statistics, clean_test_session):
    """파이터 기본 통계 집계 테스트"""
    # Given: match_with_statistics fixture 사용 (추가 매치 데이터 필요하면 생성)
    match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics

    # When: 첫 번째 파이터의 기본 통계 집계 조회
    result = await match_repo.get_fighter_basic_stats_aggregate(clean_test_session, fighters[0].id)

    # Then: 집계된 통계 DTO 반환
    assert result is not None
    assert isinstance(result, FighterBasicStatsAggregateDTO)

    # DTO 필드들 확인
    assert isinstance(result.match_count, int)
    assert isinstance(result.knockdowns, int)
    assert isinstance(result.control_time_seconds, int)
    assert isinstance(result.submission_attempts, int)
    assert isinstance(result.sig_str_landed, int)
    assert isinstance(result.sig_str_attempted, int)
    assert isinstance(result.total_str_landed, int)
    assert isinstance(result.total_str_attempted, int)
    assert isinstance(result.td_landed, int)
    assert isinstance(result.td_attempted, int)

    # 실제 값 확인 (현재 1개 매치)
    assert result.match_count == 1
    assert result.knockdowns == 1
    assert result.control_time_seconds == 240
    assert result.submission_attempts == 2


@pytest.mark.asyncio
async def test_get_fighter_sig_str_stats_aggregate(match_with_statistics, clean_test_session):
    """파이터 스트라이크 통계 집계 테스트"""
    # Given: match_with_statistics fixture 사용
    match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics

    # When: 첫 번째 파이터의 스트라이크 통계 집계 조회
    result = await match_repo.get_fighter_sig_str_stats_aggregate(clean_test_session, fighters[0].id)

    # Then: 집계된 스트라이크 통계 DTO 반환
    assert result is not None
    assert isinstance(result, FighterSigStrStatsAggregateDTO)

    # DTO 필드들 확인
    assert isinstance(result.match_count, int)
    assert isinstance(result.head_strikes_landed, int)
    assert isinstance(result.head_strikes_attempts, int)
    assert isinstance(result.body_strikes_landed, int)
    assert isinstance(result.body_strikes_attempts, int)
    assert isinstance(result.leg_strikes_landed, int)
    assert isinstance(result.leg_strikes_attempts, int)
    assert isinstance(result.takedowns_landed, int)
    assert isinstance(result.takedowns_attempts, int)
    assert isinstance(result.clinch_strikes_landed, int)
    assert isinstance(result.clinch_strikes_attempts, int)
    assert isinstance(result.ground_strikes_landed, int)
    assert isinstance(result.ground_strikes_attempts, int)

    # 실제 값 확인 (현재 1개 매치)
    assert result.match_count == 1
    assert result.head_strikes_landed == 25
    assert result.head_strikes_attempts == 40
    assert result.body_strikes_landed == 15
    assert result.takedowns_landed == 3


@pytest.mark.asyncio
async def test_get_fighter_basic_stats_aggregate_no_matches(sample_fighter, clean_test_session):
    """매치가 없는 파이터 기본 통계 집계 테스트"""
    # When: 매치가 없는 파이터의 기본 통계 집계 조회
    result = await match_repo.get_fighter_basic_stats_aggregate(clean_test_session, sample_fighter.id)

    # Then: 모든 값이 0인 DTO 반환
    assert result is not None
    assert isinstance(result, FighterBasicStatsAggregateDTO)
    assert result.match_count == 0
    assert result.knockdowns == 0
    assert result.control_time_seconds == 0
    assert result.submission_attempts == 0
    assert result.sig_str_landed == 0
    assert result.sig_str_attempted == 0
    assert result.total_str_landed == 0
    assert result.total_str_attempted == 0
    assert result.td_landed == 0
    assert result.td_attempted == 0


@pytest.mark.asyncio
async def test_get_fighter_sig_str_stats_aggregate_no_matches(sample_fighter, clean_test_session):
    """매치가 없는 파이터 스트라이크 통계 집계 테스트"""
    # When: 매치가 없는 파이터의 스트라이크 통계 집계 조회
    result = await match_repo.get_fighter_sig_str_stats_aggregate(clean_test_session, sample_fighter.id)

    # Then: 모든 값이 0인 DTO 반환
    assert result is not None
    assert isinstance(result, FighterSigStrStatsAggregateDTO)
    assert result.match_count == 0
    assert result.head_strikes_landed == 0
    assert result.head_strikes_attempts == 0
    assert result.body_strikes_landed == 0
    assert result.body_strikes_attempts == 0
    assert result.leg_strikes_landed == 0
    assert result.leg_strikes_attempts == 0
    assert result.takedowns_landed == 0
    assert result.takedowns_attempts == 0
    assert result.clinch_strikes_landed == 0
    assert result.clinch_strikes_attempts == 0
    assert result.ground_strikes_landed == 0
    assert result.ground_strikes_attempts == 0


@pytest.mark.asyncio
async def test_get_matches_by_nonexistent_event(clean_test_session):
    """존재하지 않는 이벤트 ID로 매치 조회 테스트"""
    # When: 존재하지 않는 이벤트 ID로 조회
    result = await match_repo.get_matches_by_event_id(clean_test_session, 99999)

    # Then: 빈 리스트 반환
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_fighters_matches_nonexistent_fighter(clean_test_session):
    """존재하지 않는 파이터 ID로 매치 조회 테스트"""
    # When: 존재하지 않는 파이터 ID로 조회
    result = await match_repo.get_fighters_matches(clean_test_session, 99999)

    # Then: 빈 리스트 반환
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_match_fighter_mapping_no_matches(clean_test_session):
    """매치가 없을 때 매치 파이터 매핑 조회 테스트"""
    # When: 매치가 없는 상태에서 조회
    result = await match_repo.get_match_fighter_mapping(clean_test_session)

    # Then: 빈 딕셔너리 반환
    assert isinstance(result, dict)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_match_with_winner_loser(match_with_fighters, clean_test_session):
    """매치의 승자/패자 정보 조회 테스트"""
    # Given: match_with_fighters fixture 사용
    match, fighters, fighter_matches = match_with_fighters

    # When: 매치의 승자/패자 정보 조회
    result = await match_repo.get_match_with_winner_loser(clean_test_session, match.id)

    # Then: MatchWithResultDTO 반환
    assert result is not None
    assert isinstance(result, MatchWithResultDTO)

    # 매치 정보 확인
    assert isinstance(result.match, MatchSchema)
    assert result.match.id == match.id

    # 파이터 정보 확인 (2명)
    assert isinstance(result.fighters, list)
    assert len(result.fighters) == 2

    # 승자 정보 확인
    assert result.winner is not None
    assert result.winner.result.lower() == "win"
    assert result.winner.fighter is not None

    # 패자 정보 확인
    assert result.loser is not None
    assert result.loser.result.lower() == "loss"
    assert result.loser.fighter is not None

    # 승자와 패자가 다른 파이터인지 확인
    assert result.winner.fighter.id != result.loser.fighter.id


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_nonexistent(clean_test_session):
    """존재하지 않는 매치의 승자/패자 정보 조회 테스트"""
    # When: 존재하지 않는 매치 ID로 조회
    result = await match_repo.get_match_with_winner_loser(clean_test_session, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_match_with_participants(match_with_fighters, clean_test_session):
    """매치 참여자 정보 조회 테스트"""
    # Given: match_with_fighters fixture 사용
    match, fighters, fighter_matches = match_with_fighters

    # When: 매치 참여자 정보 조회
    result = await match_repo.get_match_with_participants(clean_test_session, match.id)

    # Then: MatchWithFightersDTO 반환
    assert result is not None
    assert isinstance(result, MatchWithFightersDTO)

    # 매치 정보 확인
    assert isinstance(result.match, MatchSchema)
    assert result.match.id == match.id

    # 파이터 정보 확인 (2명)
    assert isinstance(result.fighters, list)
    assert len(result.fighters) == 2

    # 각 파이터 정보 확인
    for fighter_info in result.fighters:
        assert fighter_info.fighter is not None
        assert fighter_info.result is not None
        assert fighter_info.result in ["win", "loss", "draw"]


@pytest.mark.asyncio
async def test_get_match_with_participants_nonexistent(clean_test_session):
    """존재하지 않는 매치의 참여자 정보 조회 테스트"""
    # When: 존재하지 않는 매치 ID로 조회
    result = await match_repo.get_match_with_participants(clean_test_session, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_match_statistics(match_with_statistics, clean_test_session):
    """매치 통계 정보 조회 테스트"""
    # Given: match_with_statistics fixture 사용
    match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics

    # When: 매치 통계 정보 조회
    result = await match_repo.get_match_statistics(clean_test_session, match.id)

    # Then: MatchStatisticsDTO 반환
    assert result is not None
    assert isinstance(result, MatchStatisticsDTO)

    # 매치 ID 확인
    assert result.match_id == match.id

    # 파이터별 통계 확인
    assert isinstance(result.fighter_stats, list)
    assert len(result.fighter_stats) >= 1  # 최소 1명의 파이터 통계

    # 첫 번째 파이터 통계 확인
    first_fighter_stat = result.fighter_stats[0]
    assert first_fighter_stat.fighter_id is not None
    assert first_fighter_stat.result is not None
    assert first_fighter_stat.basic_stats is not None
    assert first_fighter_stat.sig_str_stats is not None

    # 합계 통계 확인
    combined_stats = result.combined_stats
    assert combined_stats is not None
    assert combined_stats.total_strikes_attempted >= 0
    assert combined_stats.total_strikes_landed >= 0
    assert combined_stats.total_sig_str_attempted >= 0
    assert combined_stats.total_sig_str_landed >= 0
    assert combined_stats.total_takedowns_attempted >= 0
    assert combined_stats.total_takedowns_landed >= 0
    assert combined_stats.total_control_time >= 0
    assert combined_stats.total_knockdowns >= 0
    assert combined_stats.total_submission_attempts >= 0


@pytest.mark.asyncio
async def test_get_match_statistics_nonexistent(clean_test_session):
    """존재하지 않는 매치의 통계 정보 조회 테스트"""
    # When: 존재하지 않는 매치 ID로 조회
    result = await match_repo.get_match_statistics(clean_test_session, 99999)

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_match_with_winner_loser_empty_fighters(sample_match, clean_test_session):
    """파이터가 없는 매치의 승자/패자 정보 조회 테스트"""
    # Given: 파이터가 연결되지 않은 매치

    # When: 파이터가 없는 매치의 승자/패자 정보 조회
    result = await match_repo.get_match_with_winner_loser(clean_test_session, sample_match.id)

    # Then: 매치 정보는 있지만 파이터 정보는 비어있음 (None 반환 가능)
    if result is not None:  # 매치는 존재하지만 파이터가 없을 수 있음
        assert isinstance(result, MatchWithResultDTO)
        assert isinstance(result.match, MatchSchema)
        assert isinstance(result.fighters, list)
        assert len(result.fighters) == 0


if __name__ == "__main__":
    print("Match Repositories 테스트 실행...")
    print("✅ Test Database를 사용한 완전한 통합 테스트!")
    print("✅ 새로 추가된 Repository 함수들 테스트 포함!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_repositories.py -v")