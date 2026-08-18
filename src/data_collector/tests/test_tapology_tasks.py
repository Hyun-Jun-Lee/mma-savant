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
    save_tapology_event_url,
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
        self.search_terms: list[str] = []
        self.detail_requests: list[str] = []

    def fetch_search_page(self, term: str) -> str | None:
        self.search_terms.append(term)
        return self.search_pages.get(term)

    def fetch_fighter_detail_page(self, path_or_url: str) -> str | None:
        self.detail_requests.append(path_or_url)
        return self.detail_pages.get(path_or_url)

    def fetch_bout_detail_page(self, path_or_url: str) -> str | None:
        self.detail_requests.append(path_or_url)
        return self.detail_pages.get(path_or_url)

    def fetch_event_detail_page(self, path_or_url: str) -> str | None:
        self.detail_requests.append(path_or_url)
        return self.detail_pages.get(path_or_url)


class BlockingTapologyClient(FakeTapologyClient):
    def fetch_search_page(self, term: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology search pages")

    def fetch_fighter_detail_page(self, path_or_url: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology fighter detail pages")

    def fetch_bout_detail_page(self, path_or_url: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology bout detail pages")

    def fetch_event_detail_page(self, path_or_url: str) -> str | None:
        raise AssertionError("crawler_fn should fetch Tapology event detail pages")


class NoopTapologyClient:
    def close(self) -> None:
        pass


class FakeDbContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return None


TAPOLOGY_CHALLENGE_HTML = """
<html>
  <head><title>Just a moment...</title></head>
  <body>
    <script src="/cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1"></script>
    Checking if the site connection is secure
  </body>
</html>
"""


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
                    FighterPromotionRecordModel.__table__,
                    FighterMethodRecordModel.__table__,
                    MatchModel.__table__,
                    FighterMatchModel.__table__,
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
async def test_save_tapology_fighter_enrichment_updates_profile_only(sqlite_session):
    fighter = FighterModel(
        name="Alex Pereira",
        nationality="Existing Nationality",
        born="Existing Born",
        current_streak="Existing Streak",
        last_fight_name="Existing Fight",
        last_fight_date=datetime(2024, 4, 13).date(),
        last_fight_promotion="Existing Promotion",
    )
    sqlite_session.add(fighter)
    await sqlite_session.commit()
    fighter_id = fighter.id

    first_profile = TapologyFighterProfile(
        born=None,
        fighting_out_of="Bethel, Connecticut",
        affiliation="Teixeira MMA & Fitness",
        current_streak="1 Win",
        last_fight_name="October 04, 2025 in UFC",
        last_fight_date=datetime(2025, 10, 4).date(),
        last_fight_promotion="UFC",
    )

    await save_tapology_fighter_enrichment(
        sqlite_session,
        fighter_id,
        "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
        first_profile,
        datetime(2026, 8, 5, 1, 2, 3),
    )

    refreshed = await sqlite_session.get(FighterModel, fighter_id)
    assert refreshed.nationality == "Existing Nationality"
    assert refreshed.born == "Existing Born"
    assert refreshed.fighting_out_of == "Bethel, Connecticut"
    assert refreshed.current_streak == "Existing Streak"
    assert refreshed.last_fight_name == "Existing Fight"
    assert refreshed.last_fight_date == datetime(2024, 4, 13).date()
    assert refreshed.last_fight_promotion == "Existing Promotion"
    assert refreshed.tapology_url == "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira"

    second_profile = TapologyFighterProfile(
        nationality="Brazil",
        born="Sao Bernardo do Campo, Brazil",
    )
    await save_tapology_fighter_enrichment(
        sqlite_session,
        fighter_id,
        "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
        second_profile,
        datetime(2026, 8, 5, 2, 3, 4),
    )

    refreshed = await sqlite_session.get(FighterModel, fighter_id)
    assert refreshed.nationality == "Brazil"
    assert refreshed.born == "Sao Bernardo do Campo, Brazil"
    assert refreshed.fighting_out_of == "Bethel, Connecticut"


@pytest.mark.asyncio
async def test_save_tapology_fighter_enrichment_stores_non_ufc_career_records(sqlite_session):
    fighter = FighterModel(name="Alex Pereira")
    event = EventModel(name="UFC 300", event_date=datetime(2024, 4, 13).date())
    sqlite_session.add_all([fighter, event])
    await sqlite_session.flush()

    ko_match = MatchModel(event_id=event.id, method="KO/TKO-Punches")
    dec_match = MatchModel(event_id=event.id, method="U-DEC")
    sqlite_session.add_all([ko_match, dec_match])
    await sqlite_session.flush()
    sqlite_session.add_all([
        FighterMatchModel(fighter_id=fighter.id, match_id=ko_match.id, result="win"),
        FighterMatchModel(fighter_id=fighter.id, match_id=dec_match.id, result="loss"),
    ])
    await sqlite_session.commit()

    profile = TapologyFighterProfile(
        promotion_records=[
            TapologyPromotionRecord("UFC - Ultimate Fighting Championship", wins=1, losses=1),
            TapologyPromotionRecord("LFA - Legacy Fighting Alliance", wins=2, losses=0),
        ],
        method_records=[
            TapologyMethodRecord(result="win", method_category="TKO", count=3),
            TapologyMethodRecord(result="loss", method_category="DEC", count=1),
        ],
    )

    await save_tapology_fighter_enrichment(
        sqlite_session,
        fighter.id,
        "https://www.tapology.com/fightcenter/fighters/117305-alex-pereira",
        profile,
        datetime(2026, 8, 5, 1, 2, 3),
    )

    promotion_records = (
        await sqlite_session.execute(
            select(FighterPromotionRecordModel).where(FighterPromotionRecordModel.fighter_id == fighter.id)
        )
    ).scalars().all()
    assert [(record.promotion_name, record.wins, record.losses) for record in promotion_records] == [
        ("LFA - Legacy Fighting Alliance", 2, 0),
    ]

    method_records = (
        await sqlite_session.execute(
            select(FighterMethodRecordModel).where(FighterMethodRecordModel.fighter_id == fighter.id)
        )
    ).scalars().all()
    assert [
        (record.scope, record.result, record.method_category, record.count)
        for record in method_records
    ] == [
        ("non_ufc", "win", "KO/TKO", 2),
    ]


@pytest.mark.asyncio
async def test_count_fighters_for_tapology_profile_enrichment_matches_stale_conditions(sqlite_session):
    sqlite_session.add_all([
        FighterModel(name="Missing Url"),
        FighterModel(
            name="Never Scraped",
            tapology_url="https://www.tapology.com/fightcenter/fighters/never",
        ),
        FighterModel(
            name="Stale",
            tapology_url="https://www.tapology.com/fightcenter/fighters/stale",
            tapology_last_scraped_at=datetime(2020, 1, 1),
        ),
        FighterModel(
            name="Fresh",
            tapology_url="https://www.tapology.com/fightcenter/fighters/fresh",
            tapology_last_scraped_at=datetime(2099, 1, 1),
        ),
        FighterModel(
            name="Recent Failed",
            tapology_attempt_status="worker_timeout",
            tapology_last_attempt_at=datetime(2099, 1, 1),
        ),
        FighterModel(
            name="Old Failed",
            tapology_attempt_status="worker_timeout",
            tapology_last_attempt_at=datetime(2020, 1, 1),
        ),
    ])
    await sqlite_session.commit()

    count = await tapology_tasks.count_fighters_for_tapology_profile_enrichment(
        sqlite_session,
        stale_days=30,
    )

    assert count == 4


@pytest.mark.asyncio
async def test_count_matches_for_tapology_bout_enrichment_matches_stale_conditions(sqlite_session):
    event = EventModel(name="UFC Test", event_date=datetime(2026, 1, 1).date())
    sqlite_session.add(event)
    await sqlite_session.flush()
    sqlite_session.add_all([
        MatchModel(event_id=event.id),
        MatchModel(
            event_id=event.id,
            tapology_bout_url="https://www.tapology.com/fightcenter/bouts/never",
        ),
        MatchModel(
            event_id=event.id,
            tapology_bout_url="https://www.tapology.com/fightcenter/bouts/stale",
            tapology_last_scraped_at=datetime(2020, 1, 1),
        ),
        MatchModel(
            event_id=event.id,
            tapology_bout_url="https://www.tapology.com/fightcenter/bouts/fresh",
            tapology_last_scraped_at=datetime(2099, 1, 1),
        ),
        MatchModel(
            event_id=event.id,
            tapology_attempt_status="worker_timeout",
            tapology_last_attempt_at=datetime(2099, 1, 1),
        ),
        MatchModel(
            event_id=event.id,
            tapology_attempt_status="worker_timeout",
            tapology_last_attempt_at=datetime(2020, 1, 1),
        ),
    ])
    await sqlite_session.commit()

    count = await tapology_tasks.count_matches_for_tapology_bout_enrichment(
        sqlite_session,
        stale_days=30,
    )

    assert count == 4


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
async def test_fetch_tapology_search_page_logs_elapsed_context(caplog):
    client = FakeTapologyClient({
        "Alex Pereira": """
        <a href="/fightcenter/fighters/117305-alex-pereira">Alex Pereira</a>
        """,
    })
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.INFO):
        html = await tapology_tasks._fetch_tapology_search_page(
            client,
            None,
            "Alex Pereira",
            logger=logger,
            kind="profile_search",
            fighter_id=1,
            name="Alex Pereira",
        )

    assert "Alex Pereira" in html
    assert "Tapology fetch started: kind=profile_search target=Alex Pereira fighter_id=1 name=Alex Pereira" in caplog.text
    assert "Tapology fetch completed: kind=profile_search target=Alex Pereira" in caplog.text
    assert "bytes=" in caplog.text


@pytest.mark.asyncio
async def test_fetch_tapology_search_page_logs_empty_result(caplog):
    client = FakeTapologyClient({})
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.WARNING):
        html = await tapology_tasks._fetch_tapology_search_page(
            client,
            None,
            "Unknown Fighter",
            logger=logger,
            kind="profile_search",
            fighter_id=9,
            name="Unknown Fighter",
        )

    assert html is None
    assert "Tapology fetch empty: kind=profile_search target=Unknown Fighter" in caplog.text
    assert "fighter_id=9 name=Unknown Fighter" in caplog.text


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
async def test_enrich_fighter_tapology_profile_batch_treats_challenge_search_as_failed(caplog):
    fighter = FighterSchema(id=1, name="Hamdy Abdelwahab")
    client = FakeTapologyClient({"Hamdy Abdelwahab": TAPOLOGY_CHALLENGE_HTML})

    async def save_profile(*args):
        raise AssertionError("challenge search page should not be saved")

    with caplog.at_level(logging.WARNING):
        stats = await tapology_tasks.enrich_fighter_tapology_profile_batch(
            [fighter],
            client,
            save_profile,
            logging.getLogger(__name__),
        )

    assert stats.total == 1
    assert stats.updated == 0
    assert stats.skipped == 0
    assert stats.failed == 1
    assert "blocked by challenge" in caplog.text


@pytest.mark.asyncio
async def test_enrich_fighter_tapology_profile_task_walks_all_batches(monkeypatch):
    seen_after_ids = []
    processed_ids = []

    async def select_batch(session, *, batch_size, stale_days, after_id=None):
        seen_after_ids.append(after_id)
        if after_id is None:
            return [
                FighterSchema(id=1, name="First Fighter"),
                FighterSchema(id=2, name="Second Fighter"),
            ]
        if after_id == 2:
            return [FighterSchema(id=5, name="Fifth Fighter")]
        return []

    async def count_profiles(session, *, stale_days):
        return 3

    async def enrich_batch(
        fighters,
        client,
        save_profile,
        logger,
        crawler_fn=None,
        save_attempt_state=None,
        batch_index=None,
        batch_total=None,
        processed_before=0,
        overall_total=None,
    ):
        processed_ids.extend(fighter.id for fighter in fighters)
        return tapology_tasks.TapologyProfileEnrichmentStats(
            total=len(fighters),
            updated=len(fighters),
        )

    monkeypatch.setattr(tapology_tasks, "get_run_logger", lambda: logging.getLogger(__name__))
    monkeypatch.setattr(tapology_tasks, "get_async_db_context", lambda: FakeDbContext())
    monkeypatch.setattr(tapology_tasks, "TapologyClient", NoopTapologyClient)
    monkeypatch.setattr(tapology_tasks, "count_fighters_for_tapology_profile_enrichment", count_profiles)
    monkeypatch.setattr(tapology_tasks, "select_fighters_for_tapology_profile_enrichment", select_batch)
    monkeypatch.setattr(tapology_tasks, "enrich_fighter_tapology_profile_batch", enrich_batch)

    await tapology_tasks.enrich_fighter_tapology_profile_task.fn(batch_size=2)

    assert seen_after_ids == [None, 2, 5]
    assert processed_ids == [1, 2, 5]


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
        FighterMatchModel(fighter_id=fighter_1.id, match_id=match.id, weight_gain="existing gain"),
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
    assert fighter_matches[0].weight_gain == "existing gain"
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
async def test_save_tapology_event_url_updates_event(sqlite_session):
    event = EventModel(
        name="UFC 311",
        event_date=datetime(2025, 1, 18).date(),
        location="Inglewood, California, USA",
    )
    sqlite_session.add(event)
    await sqlite_session.commit()

    saved = await save_tapology_event_url(
        sqlite_session,
        event.id,
        "https://www.tapology.com/fightcenter/events/118600-ufc-311",
    )

    refreshed = await sqlite_session.get(EventModel, event.id)
    assert saved is not None
    assert refreshed.tapology_url == "https://www.tapology.com/fightcenter/events/118600-ufc-311"


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
async def test_enrich_match_tapology_metadata_batch_matches_from_event_page_and_saves_event_url():
    event_url = "https://www.tapology.com/fightcenter/events/118600-ufc-311"
    bout_url = (
        "https://www.tapology.com/fightcenter/bouts/"
        "942695-ufc-311-merab-the-machine-dvalishvili-vs-umar-nurmagomedov"
    )
    bout = tapology_tasks.TapologyLocalBout(
        match_id=1,
        event_id=10,
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
            "UFC 311": f'<a href="{event_url}">UFC 311</a>',
        },
        {
            event_url: f'<a href="{bout_url}">Co-Main</a>',
            bout_url: "<p>Title Bout: UFC Bantamweight Championship</p>",
        },
    )
    saved_bouts = []
    saved_event_urls = []

    async def save_bout(match_id, tapology_bout_url, metadata, scraped_at):
        saved_bouts.append((match_id, tapology_bout_url, metadata.is_title_bout))

    async def save_event_url(event_id, tapology_url):
        saved_event_urls.append((event_id, tapology_url))

    stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
        [bout],
        client,
        save_bout,
        logging.getLogger(__name__),
        save_event_url=save_event_url,
    )

    assert stats.total == 1
    assert stats.matched == 1
    assert stats.updated == 1
    assert saved_event_urls == [(10, event_url)]
    assert saved_bouts == [(1, bout_url, True)]


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_reuses_existing_event_url_without_event_search():
    event_url = "https://www.tapology.com/fightcenter/events/118600-ufc-311"
    bout_url = "https://www.tapology.com/fightcenter/bouts/123-umar-nurmagomedov-vs-merab-dvalishvili"
    bout = tapology_tasks.TapologyLocalBout(
        match_id=1,
        event_id=10,
        event_name="UFC 311",
        event_date=datetime(2025, 1, 18).date(),
        tapology_bout_url=None,
        event_tapology_url=event_url,
        fighters=[
            tapology_tasks.TapologyLocalBoutFighter(1, 1, "Umar Nurmagomedov"),
            tapology_tasks.TapologyLocalBoutFighter(2, 2, "Merab Dvalishvili"),
        ],
    )
    client = FakeTapologyClient(
        {},
        {
            event_url: f'<a href="{bout_url}">Main Card - 2025 Jan 18</a>',
            bout_url: "<p>Title Bout: UFC Bantamweight Championship</p>",
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

    assert stats.updated == 1
    assert client.search_terms == []
    assert saved == [(1, bout_url, True)]


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_caches_event_page_per_batch():
    event_url = "https://www.tapology.com/fightcenter/events/118600-ufc-311"
    first_bout_url = "https://www.tapology.com/fightcenter/bouts/123-umar-nurmagomedov-vs-merab-dvalishvili"
    second_bout_url = "https://www.tapology.com/fightcenter/bouts/456-islam-makhachev-vs-renato-moicano"
    bouts = [
        tapology_tasks.TapologyLocalBout(
            match_id=1,
            event_id=10,
            event_name="UFC 311",
            event_date=datetime(2025, 1, 18).date(),
            tapology_bout_url=None,
            fighters=[
                tapology_tasks.TapologyLocalBoutFighter(1, 1, "Umar Nurmagomedov"),
                tapology_tasks.TapologyLocalBoutFighter(2, 2, "Merab Dvalishvili"),
            ],
        ),
        tapology_tasks.TapologyLocalBout(
            match_id=2,
            event_id=10,
            event_name="UFC 311",
            event_date=datetime(2025, 1, 18).date(),
            tapology_bout_url=None,
            fighters=[
                tapology_tasks.TapologyLocalBoutFighter(3, 3, "Islam Makhachev"),
                tapology_tasks.TapologyLocalBoutFighter(4, 4, "Renato Moicano"),
            ],
        ),
    ]
    client = FakeTapologyClient(
        {
            "UFC 311": f'<a href="{event_url}">UFC 311</a>',
        },
        {
            event_url: f"""
            <a href="{first_bout_url}">Main Card</a>
            <a href="{second_bout_url}">Main Event</a>
            """,
            first_bout_url: "<p>Title Bout: UFC Bantamweight Championship</p>",
            second_bout_url: "<p>Title Bout: UFC Lightweight Championship</p>",
        },
    )
    saved = []

    async def save_bout(match_id, tapology_bout_url, metadata, scraped_at):
        saved.append((match_id, tapology_bout_url, metadata.is_title_bout))

    stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
        bouts,
        client,
        save_bout,
        logging.getLogger(__name__),
    )

    assert stats.updated == 2
    assert client.search_terms == ["UFC 311"]
    assert client.detail_requests.count(event_url) == 1
    assert saved == [
        (1, first_bout_url, True),
        (2, second_bout_url, True),
    ]


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


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_batch_treats_challenge_search_as_failed(caplog):
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
        "Umar Nurmagomedov Merab Dvalishvili UFC 311": TAPOLOGY_CHALLENGE_HTML,
    })

    async def save_bout(*args):
        raise AssertionError("challenge search page should not be saved")

    with caplog.at_level(logging.WARNING):
        stats = await tapology_tasks.enrich_match_tapology_metadata_batch(
            [bout],
            client,
            save_bout,
            logging.getLogger(__name__),
        )

    assert stats.total == 1
    assert stats.updated == 0
    assert stats.skipped == 0
    assert stats.failed == 1
    assert "blocked by challenge" in caplog.text


@pytest.mark.asyncio
async def test_enrich_match_tapology_metadata_task_walks_all_batches(monkeypatch):
    seen_after_ids = []
    processed_match_ids = []

    def bout(match_id: int) -> tapology_tasks.TapologyLocalBout:
        return tapology_tasks.TapologyLocalBout(
            match_id=match_id,
            event_name="UFC Test",
            event_date=datetime(2026, 1, 1).date(),
            tapology_bout_url=None,
            fighters=[
                tapology_tasks.TapologyLocalBoutFighter(1, 1, "Fighter One"),
                tapology_tasks.TapologyLocalBoutFighter(2, 2, "Fighter Two"),
            ],
        )

    async def select_batch(session, *, batch_size, stale_days, after_id=None):
        seen_after_ids.append(after_id)
        if after_id is None:
            return [bout(10), bout(20)]
        if after_id == 20:
            return [bout(25)]
        return []

    async def count_bouts(session, *, stale_days):
        return 3

    async def enrich_batch(
        bouts,
        client,
        save_bout,
        logger,
        crawler_fn=None,
        save_event_url=None,
        save_attempt_state=None,
        batch_index=None,
        batch_total=None,
        processed_before=0,
        overall_total=None,
    ):
        processed_match_ids.extend(local_bout.match_id for local_bout in bouts)
        return tapology_tasks.TapologyBoutEnrichmentStats(
            total=len(bouts),
            updated=len(bouts),
        )

    monkeypatch.setattr(tapology_tasks, "get_run_logger", lambda: logging.getLogger(__name__))
    monkeypatch.setattr(tapology_tasks, "get_async_db_context", lambda: FakeDbContext())
    monkeypatch.setattr(tapology_tasks, "TapologyClient", NoopTapologyClient)
    monkeypatch.setattr(tapology_tasks, "count_matches_for_tapology_bout_enrichment", count_bouts)
    monkeypatch.setattr(tapology_tasks, "select_matches_for_tapology_bout_enrichment", select_batch)
    monkeypatch.setattr(tapology_tasks, "enrich_match_tapology_metadata_batch", enrich_batch)

    await tapology_tasks.enrich_match_tapology_metadata_task.fn(batch_size=2)

    assert seen_after_ids == [None, 20, 25]
    assert processed_match_ids == [10, 20, 25]
