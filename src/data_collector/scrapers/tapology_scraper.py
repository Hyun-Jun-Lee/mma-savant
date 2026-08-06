import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

from bs4 import BeautifulSoup
from bs4.element import Tag


@dataclass
class TapologyPromotionRecord:
    promotion_name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0


@dataclass
class TapologyMethodRecord:
    result: str
    method_category: str
    count: int = 0
    scope: str = "all_career"


@dataclass
class TapologyFighterProfile:
    born: str | None = None
    fighting_out_of: str | None = None
    affiliation: str | None = None
    gym: str | None = None
    current_streak: str | None = None
    last_fight_name: str | None = None
    last_fight_date: date | None = None
    last_fight_promotion: str | None = None
    promotion_records: list[TapologyPromotionRecord] = field(default_factory=list)
    method_records: list[TapologyMethodRecord] = field(default_factory=list)


@dataclass
class TapologyFighterBoutMetadata:
    fighter_name: str | None = None
    weigh_in_result: str | None = None
    fight_night_weight: str | None = None
    weight_gain: str | None = None


@dataclass
class TapologyBoutMetadata:
    is_title_bout: bool = False
    title_bout_name: str | None = None
    bout_status: str | None = None
    cancellation_reason: str | None = None
    fighter_metadata: list[TapologyFighterBoutMetadata] = field(default_factory=list)


METHOD_CATEGORIES = {"TKO", "KO/TKO", "SUB", "DEC", "DQD", "DQ", "NC", "OTHER"}
SECTION_STOPPERS = {
    "MMA Fight Record",
    "Combat Sports Record",
    "Regional MMA Rankings",
    "UFC Ranking",
    "News",
    "May contain errors",
}


def parse_tapology_fighter_profile(html: str) -> TapologyFighterProfile:
    soup = BeautifulSoup(html, "html.parser")
    lines = _text_lines(soup)

    last_fight = _value_after_label(lines, ["Last Fight"])
    last_fight_date, last_fight_promotion = _parse_last_fight(last_fight)

    affiliation = _value_after_label(lines, ["Affiliation"])
    gym = _value_after_label(lines, ["Team/Gym", "Team", "Gym"]) or affiliation

    return TapologyFighterProfile(
        born=_value_after_label(lines, ["Born"]),
        fighting_out_of=_value_after_label(lines, ["Fighting out of", "Fighting Out Of"]),
        affiliation=affiliation,
        gym=gym,
        current_streak=_value_after_label(lines, ["Current MMA Streak", "Current Streak"]),
        last_fight_name=last_fight,
        last_fight_date=last_fight_date,
        last_fight_promotion=last_fight_promotion,
        promotion_records=parse_tapology_promotion_records(html),
        method_records=parse_tapology_method_records(html),
    )


def parse_tapology_promotion_records(html: str) -> list[TapologyPromotionRecord]:
    soup = BeautifulSoup(html, "html.parser")
    structured_records = _parse_structured_promotion_records(soup)
    if structured_records:
        return structured_records

    lines = _section_lines(
        _text_lines(soup),
        "MMA Record By Promotion",
        SECTION_STOPPERS,
    )
    records: list[TapologyPromotionRecord] = []

    for idx, line in enumerate(lines):
        if not line.startswith("Image: "):
            continue
        promotion_name = line.replace("Image: ", "", 1).strip()
        if not promotion_name:
            continue
        window = lines[idx + 1 : idx + 14]
        record = TapologyPromotionRecord(
            promotion_name=promotion_name,
            wins=_count_before_label(window, "win"),
            losses=_count_before_label(window, "loss"),
            draws=_count_before_label(window, "draw"),
            no_contests=_count_before_label(window, "no contest"),
        )
        if any([record.wins, record.losses, record.draws, record.no_contests]):
            records.append(record)

    return records


def parse_tapology_method_records(html: str) -> list[TapologyMethodRecord]:
    soup = BeautifulSoup(html, "html.parser")
    structured_records = _parse_structured_method_records(soup)
    if structured_records:
        return structured_records

    lines = _section_lines(
        _text_lines(soup),
        "Pro MMA Statistics",
        {"MMA Record By Promotion", *SECTION_STOPPERS},
    )
    records: list[TapologyMethodRecord] = []

    for idx, line in enumerate(lines):
        method = _normalize_method_category(line)
        if method is None:
            continue
        window = lines[idx + 1 : idx + 10]
        win_count = _count_after_marker(window, "W")
        loss_count = _count_after_marker(window, "L")
        if win_count is not None:
            records.append(TapologyMethodRecord(result="win", method_category=method, count=win_count))
        if loss_count is not None:
            records.append(TapologyMethodRecord(result="loss", method_category=method, count=loss_count))

    return records


def parse_tapology_bout_metadata(
    html: str,
    fighter_names: Iterable[str] | None = None,
) -> TapologyBoutMetadata:
    soup = BeautifulSoup(html, "html.parser")
    lines = _text_lines(soup)

    title_bout_name = _value_after_label(lines, ["Title Bout"])
    cancellation_reason = _value_after_label(lines, ["Reason", "Cancellation Reason"])
    bout_status = _parse_bout_status(lines, cancellation_reason)

    return TapologyBoutMetadata(
        is_title_bout=title_bout_name is not None,
        title_bout_name=title_bout_name,
        bout_status=bout_status,
        cancellation_reason=cancellation_reason,
        fighter_metadata=_parse_fighter_bout_metadata(soup, fighter_names),
    )


def _parse_structured_promotion_records(soup: BeautifulSoup) -> list[TapologyPromotionRecord]:
    records: list[TapologyPromotionRecord] = []
    rows = soup.select("[data-promotion-record], .tapology-promotion-record")
    for row in rows:
        lines = _text_lines(row)
        promotion_name = (
            row.get("data-promotion-name")
            or _value_after_label(lines, ["Promotion"])
            or _first_text(row.select_one(".promotion-name, [data-field='promotion_name']"))
        )
        if not promotion_name:
            continue
        records.append(
            TapologyPromotionRecord(
                promotion_name=promotion_name,
                wins=_int_value(row.get("data-wins")) or _value_int(lines, ["Wins", "Win"]),
                losses=_int_value(row.get("data-losses")) or _value_int(lines, ["Losses", "Loss"]),
                draws=_int_value(row.get("data-draws")) or _value_int(lines, ["Draws", "Draw"]),
                no_contests=_int_value(row.get("data-no-contests"))
                or _value_int(lines, ["No Contests", "No Contest"]),
            )
        )
    return records


def _parse_structured_method_records(soup: BeautifulSoup) -> list[TapologyMethodRecord]:
    records: list[TapologyMethodRecord] = []
    rows = soup.select("[data-method-record], .tapology-method-record")
    for row in rows:
        lines = _text_lines(row)
        method = (
            row.get("data-method-category")
            or _value_after_label(lines, ["Method"])
            or _first_text(row.select_one(".method-category, [data-field='method_category']"))
        )
        result = row.get("data-result") or _value_after_label(lines, ["Result"])
        count = _int_value(row.get("data-count")) or _value_int(lines, ["Count"])
        method = _normalize_method_category(method or "")
        if method and result:
            records.append(
                TapologyMethodRecord(
                    result=result.lower(),
                    method_category=method,
                    count=count,
                )
            )
    return records


def _parse_fighter_bout_metadata(
    soup: BeautifulSoup,
    fighter_names: Iterable[str] | None,
) -> list[TapologyFighterBoutMetadata]:
    records: list[TapologyFighterBoutMetadata] = []
    for node in soup.select("[data-fighter-name], .tapology-fighter-bout"):
        lines = _text_lines(node)
        fighter_name = node.get("data-fighter-name") or _value_after_label(lines, ["Fighter"])
        metadata = TapologyFighterBoutMetadata(
            fighter_name=fighter_name,
            weigh_in_result=_value_after_label(lines, ["Weigh-In Result"]),
            fight_night_weight=_value_after_label(lines, ["Fight Night Weight"]),
            weight_gain=_value_after_label(lines, ["Weight Gain"]),
        )
        if any([metadata.weigh_in_result, metadata.fight_night_weight, metadata.weight_gain]):
            records.append(metadata)

    if records:
        return records

    lines = _text_lines(soup)
    metadata = TapologyFighterBoutMetadata(
        fighter_name=next(iter(fighter_names), None) if fighter_names else None,
        weigh_in_result=_value_after_label(lines, ["Weigh-In Result"]),
        fight_night_weight=_value_after_label(lines, ["Fight Night Weight"]),
        weight_gain=_value_after_label(lines, ["Weight Gain"]),
    )
    if any([metadata.weigh_in_result, metadata.fight_night_weight, metadata.weight_gain]):
        return [metadata]
    return []


def _parse_bout_status(lines: list[str], cancellation_reason: str | None) -> str | None:
    lowered = [line.lower() for line in lines]
    if cancellation_reason or "cancelled" in lowered or "canceled" in lowered:
        return "cancelled"
    explicit = _value_after_label(lines, ["Bout Status", "Status"])
    if explicit:
        return explicit.lower()
    if any(line in lowered for line in ["billing", "duration"]) or _value_after_label(lines, ["Billing", "Duration"]):
        return "completed"
    return None


def _parse_last_fight(value: str | None) -> tuple[date | None, str | None]:
    if not value:
        return None, None
    date_text, promotion = _split_once(value, " in ")
    parsed_date = _parse_date(date_text)
    return parsed_date, promotion


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%B %d, %Y", "%Y %b %d", "%Y %B %d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _text_lines(node: BeautifulSoup | Tag) -> list[str]:
    lines: list[str] = []
    for child in node.descendants:
        if isinstance(child, Tag) and child.name == "img":
            alt = child.get("alt")
            if alt:
                lines.append(f"Image: {_clean_text(alt)}")
        elif isinstance(child, str):
            text = _clean_text(child)
            if text:
                lines.append(text)
    return _merge_inline_label_values(lines)


def _merge_inline_label_values(lines: list[str]) -> list[str]:
    merged: list[str] = []
    idx = 0
    while idx < len(lines):
        current = lines[idx]
        if current.endswith(":") and idx + 1 < len(lines):
            merged.append(f"{current} {lines[idx + 1]}")
            idx += 2
            continue
        merged.append(current)
        idx += 1
    return merged


def _section_lines(lines: list[str], heading: str, stoppers: set[str]) -> list[str]:
    start = None
    for idx, line in enumerate(lines):
        if heading.lower() in line.lower():
            start = idx + 1
            break
    if start is None:
        return []

    section: list[str] = []
    for line in lines[start:]:
        if any(stopper.lower() in line.lower() for stopper in stoppers):
            break
        section.append(line)
    return section


def _value_after_label(lines: list[str], labels: list[str]) -> str | None:
    normalized_labels = [label.lower().rstrip(":") for label in labels]
    for idx, line in enumerate(lines):
        normalized_line = line.lower().strip()
        for label in normalized_labels:
            prefix = f"{label}:"
            if normalized_line.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                return value or None
            if normalized_line == label and idx + 1 < len(lines):
                return lines[idx + 1]
    return None


def _value_int(lines: list[str], labels: list[str]) -> int:
    value = _value_after_label(lines, labels)
    return _int_value(value)


def _count_before_label(lines: list[str], label: str) -> int:
    label = label.lower()
    for idx, line in enumerate(lines):
        if line.lower() != label or idx == 0:
            continue
        return _int_value(lines[idx - 1])
    return 0


def _count_after_marker(lines: list[str], marker: str) -> int | None:
    for idx, line in enumerate(lines):
        if line != marker:
            continue
        for candidate in lines[idx + 1 : idx + 4]:
            parsed = _int_or_none(candidate)
            if parsed is not None:
                return parsed
    return None


def _normalize_method_category(value: str) -> str | None:
    method = value.upper().strip()
    method = method.replace("KO / TKO", "KO/TKO")
    if method == "TKO":
        return "TKO"
    if method in METHOD_CATEGORIES:
        return method
    return None


def _first_text(node: Tag | None) -> str | None:
    if node is None:
        return None
    value = _clean_text(node.get_text(" ", strip=True))
    return value or None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _split_once(value: str, separator: str) -> tuple[str, str | None]:
    if separator not in value:
        return value, None
    left, right = value.split(separator, 1)
    return left.strip(), right.strip() or None


def _int_value(value) -> int:
    parsed = _int_or_none(value)
    return parsed if parsed is not None else 0


def _int_or_none(value) -> int | None:
    if value is None:
        return None
    match = re.search(r"-?\d+", str(value))
    if not match:
        return None
    return int(match.group(0))
