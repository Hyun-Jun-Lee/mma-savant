from typing import Any
from urllib.parse import urlparse


def extract_ufcstats_fighter_detail_id(url: str | None) -> str | None:
    if not url:
        return None
    path = urlparse(url).path
    return path.rstrip("/").split("/")[-1] or None


def resolve_fighter_id(
    fighter_name: str,
    fighter_link: str | None,
    fighter_lookup: dict[str, Any],
) -> int | None:
    candidates = fighter_lookup.get(fighter_name.lower().strip())
    if candidates is None:
        return None

    if isinstance(candidates, int):
        return candidates

    if len(candidates) == 1:
        return getattr(candidates[0], "id", None)

    detail_id = extract_ufcstats_fighter_detail_id(fighter_link)
    if not detail_id:
        return None

    for candidate in candidates:
        if extract_ufcstats_fighter_detail_id(getattr(candidate, "detail_url", None)) == detail_id:
            return getattr(candidate, "id", None)

    return None
