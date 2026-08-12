import json
from pathlib import Path

from common.utils import format_schema_for_prompt


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema.json"


def test_schema_prompt_renders_query_map_and_views_before_raw_tables():
    schema_data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    prompt = format_schema_for_prompt(schema_data)

    assert "## Preferred Query Map" in prompt
    assert "## Canonical Views" in prompt
    assert "Prefer v_completed_fighter_fights" in prompt
    assert "Prefer v_fighter_opponents" in prompt
    assert "Current DB canonical KO/TKO pattern is method ILIKE 'KO/TKO%'" in prompt
    assert "**v_fighter_method_summary**" in prompt
    assert "completed_fight = event_date <= current_date and result IS NOT NULL" in prompt
    assert prompt.index("## Preferred Query Map") < prompt.index("## Canonical Views")
    assert prompt.index("## Canonical Views") < prompt.index("### Tables and Relationships:")
