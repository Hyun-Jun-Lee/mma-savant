"""
Event location geocoding script.

Geocodes distinct event locations using Nominatim (OpenStreetMap).
Runs as a one-time migration: only processes rows where latitude IS NULL.

Usage:
    cd src && uv run python -m data_collector.scripts.geocode_events
"""

import logging
import sys

import psycopg2
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        dbname=Config.DB_NAME,
    )


def fetch_ungeolocated_locations(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT location FROM event "
            "WHERE latitude IS NULL AND location IS NOT NULL"
        )
        return [row[0] for row in cur.fetchall()]


def geocode_locations(locations: list[str]) -> dict[str, tuple[float, float]]:
    geolocator = Nominatim(user_agent="mma-savant-geocoder", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

    results: dict[str, tuple[float, float]] = {}
    failed: list[str] = []

    for i, loc in enumerate(locations, 1):
        logger.info("[%d/%d] Geocoding: %s", i, len(locations), loc)
        try:
            result = geocode(loc)
            if result:
                results[loc] = (result.latitude, result.longitude)
                logger.info("  -> (%.4f, %.4f)", result.latitude, result.longitude)
            else:
                failed.append(loc)
                logger.warning("  -> No result found")
        except Exception as e:
            failed.append(loc)
            logger.error("  -> Error: %s", e)

    if failed:
        logger.warning(
            "Failed to geocode %d locations:\n%s",
            len(failed),
            "\n".join(f"  - {loc}" for loc in failed),
        )

    return results


def update_events(conn, results: dict[str, tuple[float, float]]) -> int:
    updated = 0
    with conn.cursor() as cur:
        for location, (lat, lng) in results.items():
            cur.execute(
                "UPDATE event SET latitude = %s, longitude = %s WHERE location = %s",
                (lat, lng, location),
            )
            updated += cur.rowcount
    conn.commit()
    return updated


def main():
    logger.info("Starting event geocoding...")
    conn = get_connection()

    try:
        locations = fetch_ungeolocated_locations(conn)
        logger.info("Found %d unique locations to geocode", len(locations))

        if not locations:
            logger.info("Nothing to geocode. Exiting.")
            return

        results = geocode_locations(locations)
        logger.info("Successfully geocoded %d / %d locations", len(results), len(locations))

        updated = update_events(conn, results)
        logger.info("Updated %d event rows", updated)
    finally:
        conn.close()

    logger.info("Done.")


if __name__ == "__main__":
    main()
