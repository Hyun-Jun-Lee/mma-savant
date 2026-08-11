import pytest

from data_collector.scrapers.event_detail_scraper import scrap_event_detail
from fighter.models import FighterSchema


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
        {"fighter_id": 1, "result": "win"},
        {"fighter_id": 3, "result": "loss"},
    ]
