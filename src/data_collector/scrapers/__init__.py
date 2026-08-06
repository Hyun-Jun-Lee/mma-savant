from data_collector.scrapers.event_detail_scraper import scrap_event_detail
from data_collector.scrapers.events_scraper import scrap_all_events
from data_collector.scrapers.fighters_scraper import scrap_fighters
from data_collector.scrapers.match_detail_scraper import scrap_match_significant_strikes, scrap_match_basic_statistics
from data_collector.scrapers.ranking_scraper import scrap_rankings
from data_collector.scrapers.tapology_scraper import (
    parse_tapology_bout_metadata,
    parse_tapology_fighter_profile,
    parse_tapology_method_records,
    parse_tapology_promotion_records,
)
