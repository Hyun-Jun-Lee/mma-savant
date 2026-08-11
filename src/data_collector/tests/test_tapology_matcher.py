from datetime import date

from fighter.models import FighterSchema

from data_collector.workflows.tapology_matcher import (
    MatchState,
    match_tapology_event_candidates,
    match_tapology_bout,
    match_tapology_fighter,
    match_tapology_fighter_candidates,
    parse_tapology_event_candidates,
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


def test_curly_quoted_nickname_candidate_matches_exact_name():
    fighter = FighterSchema(id=1, name="Hamdy Abdelwahab")
    client = FakeTapologyClient("""
    <a href="/fightcenter/fighters/227049-hamdy-abdelwahab">Hamdy \u201cThe Hammer\u201d Abdelwahab</a>
    """)

    result = match_tapology_fighter(fighter, client)

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/fighters/227049-hamdy-abdelwahab"


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


def test_bout_matching_allows_one_day_event_date_tolerance():
    candidates = parse_tapology_bout_candidates("""
    <a href="/fightcenter/bouts/123-umar-vs-merab">
      Umar Nurmagomedov vs Merab Dvalishvili - UFC 311 - 2025 Jan 19
    </a>
    """)

    result = match_tapology_bout(
        candidates,
        fighter_names=["Umar Nurmagomedov", "Merab Dvalishvili"],
        event_date=date(2025, 1, 18),
        event_name="UFC 311: Makhachev vs. Moicano",
    )

    assert result.state == MatchState.MATCHED


def test_bout_matching_uses_url_slug_when_event_page_link_text_is_generic():
    candidates = parse_tapology_bout_candidates("""
    <a href="/fightcenter/bouts/942695-ufc-311-merab-the-machine-dvalishvili-vs-umar-nurmagomedov">
      Co-Main
    </a>
    """)
    candidates[0].parsed_date = date(2025, 1, 18)

    result = match_tapology_bout(
        candidates,
        fighter_names=["Merab Dvalishvili", "Umar Nurmagomedov"],
        event_date=date(2025, 1, 18),
        event_name="UFC 311",
    )

    assert result.state == MatchState.MATCHED
    assert result.url == (
        "https://www.tapology.com/fightcenter/bouts/"
        "942695-ufc-311-merab-the-machine-dvalishvili-vs-umar-nurmagomedov"
    )


def test_event_matching_selects_single_high_confidence_candidate():
    candidates = parse_tapology_event_candidates("""
    <a href="/fightcenter/events/118600-ufc-311">UFC 311</a>
    <a href="/fightcenter/events/120000-ufc-fight-night">UFC Fight Night</a>
    """)

    result = match_tapology_event_candidates(
        candidates,
        event_name="UFC 311",
        event_date=date(2025, 1, 18),
    )

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/events/118600-ufc-311"


def test_event_matching_accepts_same_ufc_number_without_date():
    candidates = parse_tapology_event_candidates("""
    <a href="/fightcenter/events/130000-ufc-324">UFC 324</a>
    """)

    result = match_tapology_event_candidates(
        candidates,
        event_name="UFC 324: Gaethje vs. Pimblett",
        event_date=None,
    )

    assert result.state == MatchState.MATCHED
    assert result.url == "https://www.tapology.com/fightcenter/events/130000-ufc-324"


def test_event_matching_rejects_different_ufc_number():
    candidates = parse_tapology_event_candidates("""
    <a href="/fightcenter/events/130000-ufc-324">UFC 324</a>
    """)

    result = match_tapology_event_candidates(
        candidates,
        event_name="UFC 325: Gaethje vs. Pimblett",
        event_date=None,
    )

    assert result.state == MatchState.NOT_FOUND


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
