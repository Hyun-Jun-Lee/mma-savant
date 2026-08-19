import logging
from types import SimpleNamespace

import pytest

from data_collector.scrapers import ranking_scraper
from data_collector.scrapers.ranking_scraper import (
    mapping_ranking_fighter,
    parse_ufc_rankings_from_html,
)


def test_parse_rankings_skips_pound_for_pound_top_rank_as_champion():
    html = """
    <div class="view-grouping">
      <div class="view-grouping-header">Men's Pound-for-Pound<span>Top Rank</span></div>
      <div class="rankings--athlete--champion">
        <h5><a>Islam Makhachev</a></h5>
      </div>
      <table>
        <tbody>
          <tr><td>1</td><td><a>Islam Makhachev</a></td></tr>
          <tr><td>14</td><td><a>Magomed Ankalaev</a></td></tr>
          <tr><td>14</td><td><a>Carlos Ulberg</a></td></tr>
        </tbody>
      </table>
    </div>
    """

    rankings = parse_ufc_rankings_from_html(html)

    assert rankings["men's pound-for-pound"] == [
        (1, "Islam Makhachev"),
        (14, "Magomed Ankalaev"),
        (14, "Carlos Ulberg"),
    ]


def test_parse_rankings_keeps_regular_division_champion_as_rank_zero():
    html = """
    <div class="view-grouping">
      <div class="view-grouping-header">플라이급</div>
      <div class="rankings--athlete--champion">
        <h5><a>Joshua Van</a></h5>
      </div>
      <table>
        <tbody>
          <tr><td>1</td><td><a>Alexandre Pantoja</a></td></tr>
        </tbody>
      </table>
    </div>
    """

    rankings = parse_ufc_rankings_from_html(html)

    assert rankings["flyweight"] == [
        (0, "Joshua Van"),
        (1, "Alexandre Pantoja"),
    ]


def test_parse_rankings_prefers_media_panel_when_meta_panel_also_exists():
    html = """
    <div id="rankings-panel-media">
      <div class="view-grouping">
        <div class="view-grouping-header">플라이급</div>
        <div class="rankings--athlete--champion">
          <h5><a>Media Champion</a></h5>
        </div>
        <table>
          <tbody>
            <tr><td>1</td><td><a>Media Fighter</a></td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div id="rankings-panel-meta">
      <div class="view-grouping">
        <div class="view-grouping-header">플라이급</div>
        <div class="rankings--athlete--champion">
          <h5><a>Meta Champion</a></h5>
        </div>
        <table>
          <tbody>
            <tr><td>1</td><td><a>Meta Fighter</a></td></tr>
          </tbody>
        </table>
      </div>
    </div>
    """

    rankings = parse_ufc_rankings_from_html(html)

    assert rankings["flyweight"] == [
        (0, "Media Champion"),
        (1, "Media Fighter"),
    ]


@pytest.mark.asyncio
async def test_mapping_ranking_fighter_skips_duplicate_fighter_weight_class(
    monkeypatch,
    caplog,
):
    async def get_same_fighter(session, fighter_name):
        return SimpleNamespace(id=2386)

    monkeypatch.setattr(
        ranking_scraper,
        "get_fighter_by_ranking_display_name",
        get_same_fighter,
    )

    with caplog.at_level(logging.WARNING):
        rankings = await mapping_ranking_fighter(
            None,
            {"men's pound-for-pound": [(1, "Islam Makhachev"), (1, "Islam Makhachev")]},
        )

    assert len(rankings) == 1
    assert rankings[0].fighter_id == 2386
    assert rankings[0].weight_class_id == 15
    assert rankings[0].ranking == 1
    assert "중복 랭킹을 건너뜁니다" in caplog.text
