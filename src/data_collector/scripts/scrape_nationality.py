"""
Fighter nationality scraping script.

Scrapes fighter hometown from UFC.com athlete profiles, extracts nationality
from the last comma-separated segment of the hometown field.

Usage:
    cd src && uv run python -m data_collector.scripts.scrape_nationality
"""

import asyncio
import logging
import random
import re
import sys

import psycopg2
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from text_unidecode import unidecode

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# 한국어/영어 hometown 라벨
HOMETOWN_LABELS = {"hometown", "고향"}


def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        dbname=Config.DB_NAME,
    )


def fetch_fighters_without_nationality(conn) -> list[tuple[int, str]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name FROM fighter WHERE nationality IS NULL ORDER BY id"
        )
        return cur.fetchall()


def slugify_name(name: str) -> str:
    """Convert fighter name to UFC.com URL slug.

    Examples:
        "Danny Abbadi"  -> "danny-abbadi"
        "José Aldo"     -> "jose-aldo"
        "Li Jingliang"  -> "li-jingliang"
        "St-Pierre"     -> "st-pierre"
    """
    slug = unidecode(name).lower().strip()
    # Replace spaces and dots with hyphens
    slug = re.sub(r"[\s.]+", "-", slug)
    # Remove anything that's not alphanumeric or hyphen
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


def build_profile_url(name: str) -> str:
    """Build UFC.com athlete profile URL from fighter name."""
    return f"https://www.ufc.com/athlete/{slugify_name(name)}"


def extract_nationality(hometown: str) -> str | None:
    """Extract nationality from hometown string.

    Examples:
        "Dagestan Republic, Russia" -> "Russia"
        "Coconut Creek, Florida, United States" -> "United States"
        "Sydney, New South Wales, Australia" -> "Australia"
        "Seoul, South Korea" -> "South Korea"
    """
    if not hometown:
        return None
    parts = [p.strip() for p in hometown.split(",")]
    return parts[-1] if parts else None


def parse_hometown_from_html(html: str) -> str | None:
    """Parse hometown from UFC.com profile page HTML.

    UFC.com bio structure:
        <div class="c-bio__field">
          <div class="c-bio__label">고향</div>       (or "Hometown")
          <div class="c-bio__text">Orlando, United States</div>
        </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    for field in soup.select(".c-bio__field"):
        label_el = field.select_one(".c-bio__label")
        if not label_el:
            continue
        label_text = label_el.get_text(strip=True).lower()
        if label_text in HOMETOWN_LABELS:
            text_el = field.select_one(".c-bio__text")
            if text_el:
                hometown = text_el.get_text(strip=True)
                if hometown:
                    return hometown

    return None


async def scrape_profile(page, profile_url: str) -> str | None:
    """Navigate to profile and extract hometown. Returns None on 404 or error."""
    try:
        resp = await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        if resp and resp.status == 404:
            return None
        await page.wait_for_timeout(2000)
        html = await page.content()
        return parse_hometown_from_html(html)
    except Exception as e:
        logger.error("Scrape failed for %s: %s", profile_url, e)
        return None


def update_nationality(conn, fighter_id: int, nationality: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE fighter SET nationality = %s WHERE id = %s",
            (nationality, fighter_id),
        )
    conn.commit()


async def run():
    conn = get_connection()

    try:
        fighters = fetch_fighters_without_nationality(conn)
        logger.info("Found %d fighters without nationality", len(fighters))

        if not fighters:
            logger.info("Nothing to scrape. Exiting.")
            return

        success_count = 0
        fail_no_profile: list[str] = []
        fail_no_hometown: list[str] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            for i, (fighter_id, name) in enumerate(fighters, 1):
                logger.info("[%d/%d] Processing: %s (id=%d)", i, len(fighters), name, fighter_id)

                profile_url = build_profile_url(name)
                hometown = await scrape_profile(page, profile_url)

                if hometown is None:
                    # Profile not found or no hometown
                    fail_no_profile.append(f"{name} ({profile_url})")
                    logger.warning("  -> No profile or hometown at %s", profile_url)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    continue

                nationality = extract_nationality(hometown)
                if nationality:
                    update_nationality(conn, fighter_id, nationality)
                    success_count += 1
                    logger.info("  -> %s (hometown: %s)", nationality, hometown)
                else:
                    fail_no_hometown.append(name)
                    logger.warning("  -> Could not extract nationality from: %s", hometown)

                await asyncio.sleep(random.uniform(1.0, 2.0))

            await browser.close()

        logger.info("=== Results ===")
        logger.info("Success: %d / %d", success_count, len(fighters))
        if fail_no_profile:
            logger.warning(
                "No profile/hometown (%d):\n%s",
                len(fail_no_profile),
                "\n".join(f"  - {n}" for n in fail_no_profile[:50]),
            )
        if fail_no_hometown:
            logger.warning(
                "Could not extract nationality (%d):\n%s",
                len(fail_no_hometown),
                "\n".join(f"  - {n}" for n in fail_no_hometown[:50]),
            )
    finally:
        conn.close()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
