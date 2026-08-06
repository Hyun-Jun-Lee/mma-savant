import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Iterable, Protocol
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common.utils import normalize_name
from fighter.models import FighterSchema

TAPOLOGY_BASE_URL = "https://www.tapology.com"

logger = logging.getLogger(__name__)


class MatchState(StrEnum):
    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"
    LOW_CONFIDENCE = "low_confidence"


class TapologySearchClient(Protocol):
    def fetch_search_page(self, term: str) -> str | None:
        ...


@dataclass
class TapologyFighterCandidate:
    url: str
    display_name: str
    normalized_name: str
    nickname_text: str | None = None


@dataclass
class TapologyFighterMatchResult:
    state: MatchState
    url: str | None = None
    display_name: str | None = None
    confidence: float = 0.0
    candidates: list[TapologyFighterCandidate] = field(default_factory=list)
    reason: str | None = None


@dataclass
class TapologyBoutCandidate:
    url: str
    text: str
    normalized_text: str
    parsed_date: date | None = None


@dataclass
class TapologyBoutMatchResult:
    state: MatchState
    url: str | None = None
    confidence: float = 0.0
    candidates: list[TapologyBoutCandidate] = field(default_factory=list)
    reason: str | None = None


def match_tapology_fighter(
    fighter: FighterSchema,
    client: TapologySearchClient,
) -> TapologyFighterMatchResult:
    if fighter.tapology_url:
        return TapologyFighterMatchResult(
            state=MatchState.MATCHED,
            url=fighter.tapology_url,
            display_name=fighter.name,
            confidence=1.0,
            reason="existing_tapology_url",
        )

    search_html = client.fetch_search_page(fighter.name)
    if not search_html:
        logger.info("Tapology fighter not found: %s", fighter.name)
        return TapologyFighterMatchResult(state=MatchState.NOT_FOUND, reason="empty_search")

    return match_tapology_fighter_candidates(
        fighter,
        parse_tapology_fighter_candidates(search_html),
    )


def match_tapology_fighter_candidates(
    fighter: FighterSchema,
    candidates: Iterable[TapologyFighterCandidate],
) -> TapologyFighterMatchResult:
    if fighter.tapology_url:
        return TapologyFighterMatchResult(
            state=MatchState.MATCHED,
            url=fighter.tapology_url,
            display_name=fighter.name,
            confidence=1.0,
            reason="existing_tapology_url",
        )

    exact_candidates = [
        candidate
        for candidate in candidates
        if candidate.normalized_name == _normalize_match_name(fighter.name)
    ]

    if not exact_candidates:
        logger.info("No exact Tapology fighter match for %s", fighter.name)
        return TapologyFighterMatchResult(state=MatchState.NOT_FOUND, reason="no_exact_name")

    if len(exact_candidates) == 1:
        candidate = exact_candidates[0]
        return TapologyFighterMatchResult(
            state=MatchState.MATCHED,
            url=candidate.url,
            display_name=candidate.display_name,
            confidence=0.95,
            candidates=exact_candidates,
            reason="single_exact_name",
        )

    nickname_matches = _filter_by_nickname(exact_candidates, fighter.nickname)
    if len(nickname_matches) == 1:
        candidate = nickname_matches[0]
        return TapologyFighterMatchResult(
            state=MatchState.MATCHED,
            url=candidate.url,
            display_name=candidate.display_name,
            confidence=0.98,
            candidates=exact_candidates,
            reason="nickname_disambiguated",
        )

    logger.warning("Ambiguous Tapology fighter match for %s", fighter.name)
    return TapologyFighterMatchResult(
        state=MatchState.AMBIGUOUS,
        candidates=exact_candidates,
        reason="multiple_exact_names",
    )


def parse_tapology_fighter_candidates(search_html: str) -> list[TapologyFighterCandidate]:
    soup = BeautifulSoup(search_html, "html.parser")
    candidates: list[TapologyFighterCandidate] = []
    seen_urls: set[str] = set()

    for link in soup.select('a[href*="/fightcenter/fighters/"]'):
        href = link.get("href")
        display_name = _clean_text(link.get_text(" ", strip=True))
        if not href or not display_name:
            continue

        url = _absolute_url(href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        nickname = _extract_nickname(display_name)
        candidates.append(
            TapologyFighterCandidate(
                url=url,
                display_name=display_name,
                normalized_name=_normalize_match_name(display_name),
                nickname_text=nickname,
            )
        )

    return candidates


def parse_tapology_bout_candidates(html: str) -> list[TapologyBoutCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[TapologyBoutCandidate] = []
    seen_urls: set[str] = set()

    for link in soup.select('a[href*="/fightcenter/bouts/"]'):
        href = link.get("href")
        text = _clean_text(link.get_text(" ", strip=True))
        if not href or not text:
            continue

        url = _absolute_url(href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        candidates.append(
            TapologyBoutCandidate(
                url=url,
                text=text,
                normalized_text=_normalize_match_name(text),
                parsed_date=_extract_date(text),
            )
        )

    return candidates


def match_tapology_bout(
    candidates: Iterable[TapologyBoutCandidate],
    *,
    fighter_names: Iterable[str],
    event_date: date | None,
    event_name: str | None = None,
) -> TapologyBoutMatchResult:
    candidate_list = list(candidates)
    if not candidate_list:
        return TapologyBoutMatchResult(state=MatchState.NOT_FOUND, reason="no_candidates")

    scored: list[tuple[TapologyBoutCandidate, float, bool, bool, bool]] = []
    for candidate in candidate_list:
        pair_matches = _fighter_pair_matches(candidate, fighter_names)
        date_matches = event_date is not None and candidate.parsed_date == event_date
        event_matches = _event_name_matches(candidate, event_name)

        score = 0.0
        if pair_matches:
            score += 0.6
        if date_matches:
            score += 0.25
        if event_matches:
            score += 0.15

        scored.append((candidate, score, pair_matches, date_matches, event_matches))

    high_confidence = [
        candidate
        for candidate, score, pair_matches, date_matches, event_matches in scored
        if pair_matches and date_matches and score >= 0.85
    ]
    if len(high_confidence) == 1:
        return TapologyBoutMatchResult(
            state=MatchState.MATCHED,
            url=high_confidence[0].url,
            confidence=0.95,
            candidates=high_confidence,
            reason="fighter_pair_and_event_date",
        )
    if len(high_confidence) > 1:
        logger.warning("Ambiguous Tapology bout match for fighters=%s date=%s", list(fighter_names), event_date)
        return TapologyBoutMatchResult(
            state=MatchState.AMBIGUOUS,
            candidates=high_confidence,
            reason="multiple_high_confidence_bouts",
        )

    pair_only = [candidate for candidate, _, pair_matches, _, _ in scored if pair_matches]
    if pair_only:
        logger.info("Low-confidence Tapology bout match for fighters=%s", list(fighter_names))
        return TapologyBoutMatchResult(
            state=MatchState.LOW_CONFIDENCE,
            candidates=pair_only,
            reason="fighter_pair_without_event_date",
        )

    return TapologyBoutMatchResult(state=MatchState.NOT_FOUND, reason="no_fighter_pair")


def _filter_by_nickname(
    candidates: list[TapologyFighterCandidate],
    nickname: str | None,
) -> list[TapologyFighterCandidate]:
    if not nickname:
        return []
    normalized_nickname = _normalize_match_name(nickname)
    return [
        candidate
        for candidate in candidates
        if candidate.nickname_text and _normalize_match_name(candidate.nickname_text) == normalized_nickname
    ]


def _fighter_pair_matches(candidate: TapologyBoutCandidate, fighter_names: Iterable[str]) -> bool:
    normalized_text = candidate.normalized_text
    return all(_normalize_match_name(name) in normalized_text for name in fighter_names)


def _event_name_matches(candidate: TapologyBoutCandidate, event_name: str | None) -> bool:
    if not event_name:
        return False
    normalized_text = candidate.normalized_text
    event_tokens = [
        token
        for token in re.split(r"\W+", _normalize_match_name(event_name))
        if token and (token.isdigit() or len(token) > 2)
    ]
    if not event_tokens:
        return False
    return any(token in normalized_text for token in event_tokens)


def _extract_date(text: str) -> date | None:
    for match in re.finditer(r"\b(\d{4})\s+([A-Za-z]{3,9})\s+(\d{1,2})\b", text):
        year, month, day = match.groups()
        for fmt in ("%Y %b %d", "%Y %B %d"):
            try:
                return datetime.strptime(f"{year} {month} {day}", fmt).date()
            except ValueError:
                continue

    for match in re.finditer(r"\b([A-Za-z]{3,9})\s+(\d{1,2}),\s+(\d{4})\b", text):
        month, day, year = match.groups()
        for fmt in ("%B %d %Y", "%b %d %Y"):
            try:
                return datetime.strptime(f"{month} {day} {year}", fmt).date()
            except ValueError:
                continue

    return None


def _normalize_match_name(value: str) -> str:
    without_nickname = re.sub(r'"[^"]*"', "", value)
    without_nickname = re.sub(r"\([^)]*\)", "", without_nickname)
    normalized = normalize_name(without_nickname)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _extract_nickname(value: str) -> str | None:
    match = re.search(r'"([^"]+)"', value)
    if match:
        return match.group(1).strip()
    match = re.search(r"\((?:\"?)([^)\"]+)(?:\"?)\)", value)
    if match:
        return match.group(1).strip()
    return None


def _absolute_url(path_or_url: str) -> str:
    return urljoin(f"{TAPOLOGY_BASE_URL}/", path_or_url)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
