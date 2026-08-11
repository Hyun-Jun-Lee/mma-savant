from datetime import date
from pathlib import Path

from data_collector.scrapers.tapology_scraper import (
    parse_tapology_bout_metadata,
    parse_tapology_fighter_profile,
    parse_tapology_method_records,
    parse_tapology_promotion_records,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "scrapers" / "test-by-html"


def _fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text()


def test_parse_tapology_fighter_profile_with_all_fields():
    profile = parse_tapology_fighter_profile(_fixture("tapology_fighter_profile_full.html"))

    assert profile.born == "Sao Bernardo do Campo, Sao Paulo, Brazil"
    assert profile.fighting_out_of == "Bethel, Connecticut"
    assert profile.affiliation == "Teixeira MMA & Fitness"
    assert profile.gym == "Teixeira MMA & Fitness"
    assert profile.current_streak == "1 Win"
    assert profile.last_fight_name == "October 04, 2025 in UFC"
    assert profile.last_fight_date == date(2025, 10, 4)
    assert profile.last_fight_promotion == "UFC"
    assert profile.promotion_records == []
    assert profile.method_records == []


def test_parse_tapology_fighter_profile_missing_optional_fields():
    profile = parse_tapology_fighter_profile("""
    <section>
      <p>Current Streak: N/A</p>
      <p>Born: Brazil</p>
    </section>
    """)

    assert profile.born == "Brazil"
    assert profile.current_streak == "N/A"
    assert profile.affiliation is None
    assert profile.gym is None
    assert profile.fighting_out_of is None


def test_parse_tapology_promotion_records():
    records = parse_tapology_promotion_records(_fixture("tapology_fighter_profile_full.html"))

    assert records[0].promotion_name == "UFC - Ultimate Fighting Championship"
    assert records[0].wins == 10
    assert records[0].losses == 2
    assert records[0].draws == 0
    assert records[0].no_contests == 0
    assert records[1].promotion_name == "LFA - Legacy Fighting Alliance"
    assert records[1].wins == 1


def test_parse_tapology_method_records():
    records = parse_tapology_method_records(_fixture("tapology_fighter_profile_full.html"))
    by_key = {(record.result, record.method_category): record.count for record in records}

    assert by_key[("win", "TKO")] == 11
    assert by_key[("loss", "TKO")] == 1
    assert by_key[("win", "SUB")] == 0
    assert by_key[("loss", "SUB")] == 1
    assert by_key[("win", "DEC")] == 2
    assert by_key[("loss", "DEC")] == 1


def test_parse_tapology_completed_title_bout_with_weigh_in_metadata():
    metadata = parse_tapology_bout_metadata(_fixture("tapology_bout_title_weigh_in.html"))

    assert metadata.is_title_bout is True
    assert metadata.title_bout_name == "UFC Bantamweight Championship"
    assert metadata.bout_status == "completed"
    assert metadata.cancellation_reason is None
    assert metadata.fighter_metadata[0].fighter_name == "Umar Nurmagomedov"
    assert metadata.fighter_metadata[0].weigh_in_result == "135.0 lbs (61.2 kgs)"
    assert metadata.fighter_metadata[0].fight_night_weight == "156.8 lbs (71.1 kgs)"
    assert metadata.fighter_metadata[0].weight_gain is None
    assert metadata.fighter_metadata[1].fighter_name == "Merab Dvalishvili"


def test_parse_tapology_cancelled_bout():
    metadata = parse_tapology_bout_metadata(
        _fixture("tapology_bout_cancelled.html"),
        fighter_names=["Tony Gravely"],
    )

    assert metadata.is_title_bout is False
    assert metadata.bout_status == "cancelled"
    assert metadata.cancellation_reason == "Maness Withdrew"
    assert metadata.fighter_metadata[0].fighter_name == "Tony Gravely"
    assert metadata.fighter_metadata[0].weigh_in_result == "135.5 lbs (61.5 kgs)"
