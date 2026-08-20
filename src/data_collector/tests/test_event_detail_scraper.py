import pytest

from data_collector.scrapers.event_detail_scraper import scrap_event_detail
from fighter.models import FighterSchema


def _event_detail_html(
    *,
    date: str = "March 12, 2022",
    detail_url: str = "http://ufcstats.com/fight-details/example",
    result_cell: str = '<a class="b-flag b-flag_style_green">win</a>',
    icons: tuple[str, ...] = (),
    method: str = "KO/TKO Punches",
) -> str:
    icon_html = "\n".join(
        f'<img src="http://ufcstats.com/images/{icon_file}" />'
        for icon_file in icons
    )
    return f"""
    <html>
      <body>
        <div class="b-list__info-box">
          <li class="b-list__box-list-item">
            <i class="b-list__box-item-title">Date:</i> {date}
          </li>
        </div>
        <table>
          <tr class="b-fight-details__table-row"></tr>
          <tr class="b-fight-details__table-row js-fight-details-click"
              data-link="{detail_url}">
            <td class="b-fight-details__table-col">
              {result_cell}
            </td>
            <td class="b-fight-details__table-col">
              <a href="http://ufcstats.com/fighter-details/a">alpha fighter</a>
              <a href="http://ufcstats.com/fighter-details/b">beta fighter</a>
            </td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col">
              Lightweight
              {icon_html}
            </td>
            <td class="b-fight-details__table-col">{method}</td>
            <td class="b-fight-details__table-col">1</td>
            <td class="b-fight-details__table-col">2:00</td>
          </tr>
        </table>
      </body>
    </html>
    """


@pytest.mark.asyncio
async def test_scrap_event_detail_resolves_duplicate_fighter_names_by_detail_url():
    html = """
    <html>
      <body>
        <div class="b-list__info-box">
          <li class="b-list__box-list-item">
            <i class="b-list__box-item-title">Date:</i> March 12, 2022
          </li>
        </div>
        <table>
          <tr class="b-fight-details__table-row"></tr>
          <tr class="b-fight-details__table-row js-fight-details-click"
              data-link="http://ufcstats.com/fight-details/226884e46a10865d">
            <td class="b-fight-details__table-col">
              <a class="b-flag b-flag_style_green">win</a>
            </td>
            <td class="b-fight-details__table-col">
              <a href="http://ufcstats.com/fighter-details/3079abc">alex pereira</a>
              <a href="http://ufcstats.com/fighter-details/12ebd7d157e91701">bruno silva</a>
            </td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col"></td>
            <td class="b-fight-details__table-col">Middleweight</td>
            <td class="b-fight-details__table-col">KO/TKO Punches</td>
            <td class="b-fight-details__table-col">1</td>
            <td class="b-fight-details__table-col">2:00</td>
          </tr>
        </table>
      </body>
    </html>
    """

    async def crawler_fn(url: str) -> str:
        return html

    fighter_lookup = {
        "alex pereira": [
            FighterSchema(id=1, name="alex pereira", detail_url="3079abc"),
        ],
        "bruno silva": [
            FighterSchema(id=2, name="bruno silva", nickname="Bulldog", detail_url="294aa73dbf37d281"),
            FighterSchema(id=3, name="bruno silva", nickname="Blindado", detail_url="12ebd7d157e91701"),
        ],
    }

    matches = await scrap_event_detail(
        crawler_fn,
        "http://ufcstats.com/event-details/example",
        10,
        fighter_lookup,
    )

    assert len(matches) == 1
    assert matches[0]["fighters"] == [
        {"fighter_id": 1, "result": "win", "has_performance_of_the_night_bonus": False},
        {"fighter_id": 3, "result": "loss", "has_performance_of_the_night_bonus": False},
    ]


@pytest.mark.asyncio
async def test_scrap_event_detail_collects_event_row_bonus_icons():
    html = _event_detail_html(
        detail_url="http://ufcstats.com/fight-details/title-fotn",
        icons=("belt.png", "fight.png"),
    )

    async def crawler_fn(url: str) -> str:
        return html

    matches = await scrap_event_detail(
        crawler_fn,
        "http://ufcstats.com/event-details/example",
        10,
        {"alpha fighter": 1, "beta fighter": 2},
    )

    assert len(matches) == 1
    match = matches[0]["match"]
    assert match.is_title_bout is True
    assert match.has_fight_of_the_night_bonus is True
    assert matches[0]["fighters"] == [
        {"fighter_id": 1, "result": "win", "has_performance_of_the_night_bonus": False},
        {"fighter_id": 2, "result": "loss", "has_performance_of_the_night_bonus": False},
    ]


@pytest.mark.asyncio
async def test_scrap_event_detail_assigns_performance_bonus_to_winner_only():
    html = _event_detail_html(
        detail_url="http://ufcstats.com/fight-details/perf",
        icons=("perf.png",),
        method="SUB Arm Triangle",
    )

    async def crawler_fn(url: str) -> str:
        return html

    matches = await scrap_event_detail(
        crawler_fn,
        "http://ufcstats.com/event-details/example",
        10,
        {"alpha fighter": 1, "beta fighter": 2},
    )

    assert matches[0]["fighters"] == [
        {"fighter_id": 1, "result": "win", "has_performance_of_the_night_bonus": True},
        {"fighter_id": 2, "result": "loss", "has_performance_of_the_night_bonus": False},
    ]


@pytest.mark.asyncio
async def test_scrap_event_detail_does_not_guess_performance_bonus_for_future_event():
    html = _event_detail_html(
        date="January 1, 2999",
        detail_url="http://ufcstats.com/fight-details/future",
        result_cell="",
        icons=("perf.png", "mystery.png"),
        method="",
    )

    async def crawler_fn(url: str) -> str:
        return html

    matches = await scrap_event_detail(
        crawler_fn,
        "http://ufcstats.com/event-details/example",
        10,
        {"alpha fighter": 1, "beta fighter": 2},
    )

    assert matches[0]["fighters"] == [
        {"fighter_id": 1, "result": None, "has_performance_of_the_night_bonus": False},
        {"fighter_id": 2, "result": None, "has_performance_of_the_night_bonus": False},
    ]
