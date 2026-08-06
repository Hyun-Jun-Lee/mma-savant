import logging
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from data_collector.scrapers.tapology_scraper import (
    TapologyBoutMetadata,
    TapologyFighterBoutMetadata,
    TapologyFighterProfile,
    TapologyMethodRecord,
    TapologyPromotionRecord,
)
from data_collector.workflows import tapology_tasks
from data_collector.workflows.data_store import (
    save_tapology_fighter_enrichment,
    save_tapology_match_enrichment,
)
from event.models import EventModel
from fighter.models import (
    FighterMethodRecordModel,
    FighterModel,
    FighterPromotionRecordModel,
    FighterSchema,
)
from match.models import FighterMatchModel, MatchModel


class FakeTapologyClient:
    def __init__(self, search_pages: dict[str, str], detail_pages: dict[str, str] | None = None) -> None:
        self.search_pages = search_pages
        self.detail_pages = detail_pages or {}

    def fetch_search_page(self, term: str) -> str | None:
        return self.search_pages.get(term)

    def fetch_fighter_detail_page(self, path_or_url: str) -> str | None:
        return self.detail_pages.get(path_or_url)

    def fetch_bout_detail_page(self, path_or_url: str) -> str | None:
        return self.detail_pages.get(path_or_url)


class BlockingTapologyClient(FakeTapologyClient):
    def fetch_search_page(self, term: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology search pages")

    def fetch_fighter_detail_page(self, path_or_url: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology fighter detail pages")

    def fetch_bout_detail_page(self, path_or_url: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology bout detail pages")


@pytest_asyncio.fixture
async def sqlite_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: FighterModel.metadata.create_all(
                sync_conn,
                tables=[
                    EventModel.__table__,
                    FighterModel.__table__,
                    MatchModel.__table__,
                    FighterMatchModel.__table__,
                    FighterPromotionRecordModel.__table__,
                    FighterMethodRecordModel.__table__,
                ],
            )
        )

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_save_tapology_fighter_enrichment_updates_profile_and_replaces_records(sqlite_session):
    fighter = FighterModel(name="Alex Pereira", born="Existing Born")
    sqlite_session.add(fighter)
    await sqlite_session.commit()
    fighter_id = fighter.id

    first_profile = TapologyFighterProfile(
        born=None,
        fighting_out_of="Bethel, Connecticut",
        affiliation="Teixeira MMA & Fitness",
        current_streak="1 Win",
        promotion_records=[
            TapologyPromotionRecord("UFC", wins=10, losses=2),
            TapologyPromotionRecord("LFA", wins=1),
        ],
        method_records=[
            TapologyMethodRecord(result="win", method_category="TKO", count=11),
            TapologyMethodRecord(result="loss", method_category="SUB", count=1),
        ],
    )

    await save_tapology_fighter_enrichment(
        sqlite_session,
        fighter_id,
        "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
        first_profile,
        datetime(2026, 8, 5, 1, 2, 3),
    )

    refreshed = await sqlite_session.get(FighterModel, fighter_id)
    assert refreshed.born == "Existing Born"
    assert refreshed.fighting_out_of == "Bethel, Connecticut"
    assert refreshed.tapology_url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"

    second_profile = TapologyFighterProfile(
        born="Sao Bernardo do Campo, Brazil",
        promotion_records=[TapologyPromotionRecord("UFC", wins=11, losses=2)],
        method_records=[TapologyMethodRecord(result="win", method_category="DEC", count=2)],
    )
    await save_tapology_fighter_enrichment(
        sqlite_session,
        fighter_id,
        "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
        second_profile,
        datetime(2026, 8, 5, 2, 3, 4),
    )

    refreshed = await sqlite_session.get(FighterModel, fighter_id)
    assert refreshed.born == "Sao Bernardo do Campo, Brazil"
    assert refreshed.fighting_out_of == "Bethel, Connecticut"

    promotions = (
        await sqlite_session.execute(select(FighterPromotionRecordModel))
    ).scalars().all()
    methods = (
        await sqlite_session.execute(select(FighterMethodRecordModel))
    ).scalars().all()

    assert len(promotions) == 1
    assert promotions[0].promotion_name == "UFC"
    assert promotions[0].wins == 11
    assert len(methods) == 1
    assert methods[0].method_category == "DEC"
    assert methods[0].count == 2


@pytest.mark.asyncio
async def test_enrich_fighter_tapology_profile_batch_skips_ambiguous_match():
    fighter = FighterSchema(id=1, name="Alex Pereira")
    client = FakeTapologyClient({
        "Alex Pereira": """
        <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
        <a href="/fightcenter/fighters/422892-alex-pereira-gigante">Alex "Gigante" Pereira</a>
        """,
    })

    async def save_profile(*args):
        raise AssertionError("ambiguous fighter should not be saved")

    stats = await tapology_tasks.enrich_fighter_tapology_profile_batch(
        [fighter],
        client,
        save_profile,
        logging.getLogger(__name__),
    )

    assert stats.total == 1
    assert stats.updated == 0
    assert stats.skipped == 1
    assert stats.failed == 0


@pytest.mark.asyncio
async def test_enrich_fighter_tapology_profile_batch_continues_after_parser_failure(monkeypatch):
    bad_url = "https://www.tapology.com/fightcenter/fighters/bad"
    good_url = "https://www.tapology.com/fightcenter/fighters/good"
    client = FakeTapologyClient(
        {
            "Bad Fighter": '<a href="/fightcenter/fighters/bad">Bad Fighter</a>',
            "Good Fighter": '<a href="/fightcenter/fighters/good">Good Fighter</a>',
        },
        {
            bad_url: "<html>bad</html>",
            good_url: "<html>good</html>",
        },
    )

    def parse_profile(html: str) -> TapologyFighterProfile:
        if "bad" in html:
            raise ValueError("broken profile")
        return TapologyFighterProfile(born="Brazil")

    saved = []

    async def save_profile(fighter_id, tapology_url, profile, scraped_at):
        saved.append((fighter_id, tapology_url, profile.born))

    monkeypatch.setattr(tapology_tasks, "parse_tapology_fighter_profile", parse_profile)

    stats = await tapology_tasks.enrich_fighter_tapology_profile_batch(
        [
            FighterSchema(id=1, name="Bad Fighter"),
            FighterSchema(id=2, name="Good Fighter"),
        ],
        client,
        save_profile,
        logging.getLogger(__name__),
    )

    assert stats.total == 2
    assert stats.updated == 1
    assert stats.failed == 1
    assert saved == [(2, good_url, "Brazil")]


@pytest.mark.asyncio
async def test_enrich_fighter_tapology_profile_batch_uses_crawler_fn_when_provided():
    fighter_url = "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"
    responses = {
        "https://www.tapology.com/search?term=Alex+Pereira": """
        <a href="/fightcenter/fighters/117305-alex-pereira">Alex "Poatan" Pereira</a>
        """,
        fighter_url: "<p>Born: Sao Bernardo do Campo, Brazil</p>",
    }

    async def crawler_fn(url: str) -> str | None:
        return responses.get(url)

    saved = []

    async def save_profile(fighter_id, tapology_url, profile, scraped_at):
        saved.append((fighter_id, tapology_url, profile.born))

    stats = await tapology_tasks.enrich_fighter_tapology_profile_batch(
        [FighterSchema(id=1, name="Alex Pereira", nickname="Poatan")],
        BlockingTapologyClient({}),
        save_profile,
        logging.getLogger(__name__),
        crawler_fn=crawler_fn,
    )

    assert stats.updated == 1
    assert saved == [(1, fighter_url, "Sao Bernardo do Campo, Brazil")]


@pytest.mark.asyncio
async def test_save_tapology_match_enrichment_updates_title_and_weigh_in(sqlite_session):
    event = EventModel(name="UFC 311", event_date=datetime(2025, 1, 18).date())
    fighter_1 = FighterModel(name="Umar Nurmagomedov")
    fighter_2 = FighterModel(name="Merab Dvalishvili")
    sqlite_session.add_all([event, fighter_1, fighter_2])
    await sqlite_session.flush()

    match = MatchModel(event_id=event.id, is_main_event=False)
    sqlite_session.add(match)
    await sqlite_session.flush()
    sqlite_session.add_all([
        FighterMatchModel(fighter_id=fighter_1.id, match_id=match.id),
        FighterMatchModel(fighter_id=fighter_2.id, match_id=match.id),
    ])
    await sqlite_session.commit()

    metadata = TapologyBoutMetadata(
        is_title_bout=True,
        bout_status="completed",
        fighter_metadata=[
            TapologyFighterBoutMetadata(
                fighter_name="Umar Nurmagomedov",
                weigh_in_result="135.0 lbs",
                fight_night_weight="156.8 lbs",
                weight_gain="21.8 lbs",
            ),
            TapologyFighterBoutMetadata(
                fighter_name="Merab Dvalishvili",
                weigh_in_result="134.0 lbs",
            ),
        ],
    )

    await save_tapology_match_enrichment(
        sqlite_session,
        match.id,
        "https://www.tapology.com/fightcenter/bouts/123",
        metadata,
        datetime(2026, 8, 6, 1, 2, 3),
    )

    refreshed = await sqlite_session.get(MatchModel, match.id)
    assert refreshed.is_title_bout is True
    assert refreshed.bout_status == "completed"
    assert refreshed.tapology_bout_url == "https://www.tapology.com/fightcenter/bouts/123"

    fighter_matches = (
        await sqlite_session.execute(
            select(FighterMatchModel).order_by(FighterMatchModel.fighter_id)
        )
    ).scalars().all()
    assert fighter_matches[0].weigh_in_result == "135.0 lbs"
    assert fighter_matches[0].fight_night_weight == "156.8 lbs"
    assert fighter_matches[0].weight_gain == "21.8 lbs"
    assert fighter_matches[1].weigh_in_result == "134.0 lbs"


@pytest.mark.asyncio
async def test_save_tapology_match_enrichment_preserves_completed_result_on_cancelled_conflict(sqlite_session):
    event = EventModel(name="UFC Fight Night", event_date=datetime(2025, 1, 18).date())
    fighter_1 = FighterModel(name="Fighter One")
    fighter_2 = FighterModel(name="Fighter Two")
    sqlite_session.add_all([event, fighter_1, fighter_2])
    await sqlite_session.flush()

    match = MatchModel(event_id=event.id, bout_status="completed", is_main_event=False)
    sqlite_session.add(match)
    await sqlite_session.flush()
    sqlite_session.add_all([
        FighterMatchModel(fighter_id=fighter_1.id, match_id=match.id, result="win"),
        FighterMatchModel(fighter_id=fighter_2.id, match_id=match.id, result="loss"),
    ])
    await sqlite_session.commit()

    metadata = TapologyBoutMetadata(
        is_title_bout=False,
        bout_status="cancelled",
        cancellation_reason="Fighter withdrew",
    )

    await save_tapology_match_enrichment(
        sqlite_session,
        match.id,
        "https://www.tapology.com/fightcenter/bouts/cancelled",
        metadata,
        datetime(2026, 8, 6, 1, 2, 3),
    )

    refreshed = await sqlite_session.get(MatchModel, match.id)
    assert refreshed.bout_status == "completed"
    assert refreshed.cancellation_reason is None
    assert refreshed.tapology_bout_url == "https://www.tapology.com/fightcenter/bouts/cancelled"


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_skips_low_confidence_match():
    bout = tapology_tasks.TapologyLocalBout(
        match_id=1,
        event_name="UFC 311",
        event_date=datetime(2025, 1, 18).date(),
        tapology_bout_url=None,
        fighters=[
            tapology_tasks.TapologyLocalBoutFighter(1, 1, "Umar Nurmagomedov"),
            tapology_tasks.TapologyLocalBoutFighter(2, 2, "Merab Dvalishvili"),
        ],
    )
    client = FakeTapologyClient({
        "Umar Nurmagomedov Merab Dvalishvili UFC 311": """
        <a href="/fightcenter/bouts/123-umar-vs-merab">
          Umar Nurmagomedov vs Merab Dvalishvili
        </a>
        """,
    })

    async def save_bout(*args):
        raise AssertionError("low-confidence bout should not be saved")

    stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
        [bout],
        client,
        save_bout,
        logging.getLogger(__name__),
    )

    assert stats.total == 1
    assert stats.updated == 0
    assert stats.skipped == 1
    assert stats.failed == 0


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_updates_high_confidence_match():
    bout_url = "https://www.tapology.com/fightcenter/bouts/123-umar-vs-merab"
    bout = tapology_tasks.TapologyLocalBout(
        match_id=1,
        event_name="UFC 311",
        event_date=datetime(2025, 1, 18).date(),
        tapology_bout_url=None,
        fighters=[
            tapology_tasks.TapologyLocalBoutFighter(1, 1, "Umar Nurmagomedov"),
            tapology_tasks.TapologyLocalBoutFighter(2, 2, "Merab Dvalishvili"),
        ],
    )
    client = FakeTapologyClient(
        {
            "Umar Nurmagomedov Merab Dvalishvili UFC 311": """
            <a href="/fightcenter/bouts/123-umar-vs-merab">
              Umar Nurmagomedov vs Merab Dvalishvili - UFC 311 - 2025 Jan 18
            </a>
            """,
        },
        {
            bout_url: """
            <p>Title Bout: UFC Bantamweight Championship</p>
            <section data-fighter-name="Umar Nurmagomedov">
              <p>Weigh-In Result: 135.0 lbs</p>
            </section>
            """,
        },
    )
    saved = []

    async def save_bout(match_id, tapology_bout_url, metadata, scraped_at):
        saved.append((match_id, tapology_bout_url, metadata.is_title_bout))

    stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
        [bout],
        client,
        save_bout,
        logging.getLogger(__name__),
    )

    assert stats.total == 1
    assert stats.matched == 1
    assert stats.updated == 1
    assert saved == [(1, bout_url, True)]


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_uses_crawler_fn_when_provided():
    bout_url = "https://www.tapology.com/fightcenter/bouts/123-umar-vs-merab"
    bout = tapology_tasks.TapologyLocalBout(
        match_id=1,
        event_name="UFC 311",
        event_date=datetime(2025, 1, 18).date(),
        tapology_bout_url=None,
        fighters=[
            tapology_tasks.TapologyLocalBoutFighter(1, 1, "Umar Nurmagomedov"),
            tapology_tasks.TapologyLocalBoutFighter(2, 2, "Merab Dvalishvili"),
        ],
    )
    responses = {
        "https://www.tapology.com/search?term=Umar+Nurmagomedov+Merab+Dvalishvili+UFC+311": """
        <a href="/fightcenter/bouts/123-umar-vs-merab">
          Umar Nurmagomedov vs Merab Dvalishvili - UFC 311 - 2025 Jan 18
        </a>
        """,
        bout_url: "<p>Title Bout: UFC Bantamweight Championship</p>",
    }

    async def crawler_fn(url: str) -> str | None:
        return responses.get(url)

    saved = []

    async def save_bout(match_id, tapology_bout_url, metadata, scraped_at):
        saved.append((match_id, tapology_bout_url, metadata.is_title_bout))

    stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
        [bout],
        BlockingTapologyClient({}),
        save_bout,
        logging.getLogger(__name__),
        crawler_fn=crawler_fn,
    )

    assert stats.updated == 1
    assert saved == [(1, bout_url, True)]
