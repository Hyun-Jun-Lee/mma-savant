from datetime import date

from fighter.models import FighterSchema

from data_collector.workflows.tapology_matcher import (
    MatchState,
    match_tapology_bout,
    match_tapology_fighter,
    match_tapology_fighter_candidates,
    parse_tapology_bout_candidates,
    parse_tapology_fighter_candidates,
)


class FakeTapologyClient:
    def __init__(self, search_html: str | None = None) -> None:
        self.search_html = search_html
        self.search_terms = []

    def fetch_search_page(self, term: str) -> str | None:
        self.search_terms.append(term)
        return self.search_html


def test_existing_tapology_url_bypasses_search():
    fighter = FighterSchema(
        id=1,
        name="Alex Pereira",
        nickname="Poatan",
        tapology_url="https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
    )
    client = FakeTapologyClient()

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"
    assert result.confidence == 1.0
    assert client.search_terms == []


def test_single_exact_name_candidate_matches():
    fighter = FighterSchema(id=1, name="Alex Pereira", nickname="Poatan")
    client = FakeTapologyClient("""
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    <a href="/fightcenter/fighters/454006-alexander-pereira">Alexander Pereira</a>
    """)

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"
    assert result.display_name == 'Alex "Poatan" Pereira'


def test_multiple_exact_name_candidates_without_nickname_are_ambiguous():
    fighter = FighterSchema(id=1, name="Alex Pereira")
    client = FakeTapologyClient("""
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    <a href="/fightcenter/fighters/422892-alex-pereira-gigante">Alex "Gigante" Pereira</a>
    """)

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.AMBIGUOUS
    assert len(result.candidates) == 2


def test_nickname_selects_one_exact_name_candidate():
    fighter = FighterSchema(id=1, name="Alex Pereira", nickname="Gigante")
    client = FakeTapologyClient("""
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    <a href="/fightcenter/fighters/422892-alex-pereira-gigante">Alex "Gigante" Pereira</a>
    """)

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/fighters/422892-alex-pereira-gigante"


def test_no_fighter_search_result_returns_not_found():
    fighter = FighterSchema(id=1, name="No Match")
    client = FakeTapologyClient("<html><body>No fighters here</body></html>")

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.NOT_FOUND


def test_parse_tapology_fighter_candidates_strips_duplicate_links():
    html = """
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    """

    candidates = parse_tapology_fighter_candidates(html)

    assert len(candidates) == 1
    assert candidates[0].url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"


def test_match_tapology_fighter_candidates_matches_without_client_search():
    fighter = FighterSchema(id=1, name="Alex Pereira", nickname="Poatan")
    candidates = parse_tapology_fighter_candidates("""
    <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
    """)

    result = match_tapology_fighter_candidates(fighter, candidates)

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"


def test_bout_matching_requires_fighter_pair_and_event_date():
    candidates = parse_tapology_bout_candidates("""
    <a href="/fightcenter/bouts/123-umar-vs-merab">
      Umar Nurmagomedov vs Merab Dvalishvili - UFC 311 - 2025 Jan 18
    </a>
    """)

    result = match_tapology_bout(
        candidates,
        fighter_names=["Umar Nurmagomedov", "Merab Dvalishvili"],
        event_date=date(2025, 1, 18),
        event_name="UFC 311: Makhachev vs. Moicano",
    )

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/bouts/123-umar-vs-merab"


def test_bout_matching_low_confidence_when_only_fighter_pair_matches():
    candidates = parse_tapology_bout_candidates("""
    <a href="/fightcenter/bouts/123-umar-vs-merab">
      Umar Nurmagomedov vs Merab Dvalishvili
    </a>
    """)

    result = match_tapology_bout(
        candidates,
        fighter_names=["Umar Nurmagomedov", "Merab Dvalishvili"],
        event_date=date(2025, 1, 18),
        event_name="UFC 311: Makhachev vs. Moicano",
    )

    assert result.state == MatchState.LOW_CONFIDENCE


def test_bout_matching_ambiguous_when_multiple_high_confidence_candidates():
    candidates = parse_tapology_bout_candidates("""
    <a href="/fightcenter/bouts/123-umar-vs-merab">
      Umar Nurmagomedov vs Merab Dvalishvili - UFC 311 - 2025 Jan 18
    </a>
    <a href="/fightcenter/bouts/456-umar-vs-merab">
      Merab Dvalishvili vs Umar Nurmagomedov - UFC 311 - 2025 Jan 18
    </a>
    """)

    result = match_tapology_bout(
        candidates,
        fighter_names=["Umar Nurmagomedov", "Merab Dvalishvili"],
        event_date=date(2025, 1, 18),
        event_name="UFC 311: Makhachev vs. Moicano",
    )

    assert result.state == MatchState.AMBIGUOUS
