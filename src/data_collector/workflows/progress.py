def format_progress(
    *,
    batch_index: int | None = None,
    batch_total: int | None = None,
    item_index: int | None = None,
    item_total: int | None = None,
    overall_index: int | None = None,
    overall_total: int | None = None,
) -> str:
    segments: list[str] = []

    batch_segment = _format_pair("batch", batch_index, batch_total)
    item_segment = _format_pair("item", item_index, item_total)
    overall_segment = _format_pair("overall", overall_index, overall_total)

    if batch_segment and item_segment:
        segments.append(f"{batch_segment} {item_segment}")
    elif batch_segment:
        segments.append(batch_segment)
    elif item_segment:
        segments.append(item_segment)

    if overall_segment:
        segments.append(overall_segment)

    if not segments:
        return ""

    return f"[{' | '.join(segments)}]"


def _format_pair(label: str, index: int | None, total: int | None) -> str:
    if index is None or total is None:
        return ""
    return f"{label} {index}/{total}"
