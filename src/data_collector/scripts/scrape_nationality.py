"""
Fighter nationality scraping script.

Scrapes fighter nationality using Tapology.com as primary source,
with UFC.com athlete profiles as fallback.

Usage:
    cd src && uv run python -m data_collector.scripts.scrape_nationality
"""

import asyncio
import logging
import random
import re
import sys

import time

import psycopg2
import requests as http_requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
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

# Tapology 설정
_ua = UserAgent()
TAPOLOGY_BASE_DELAY = (2.0, 4.0)  # 요청 간 기본 딜레이 (초)
TAPOLOGY_CIRCUIT_BREAKER_THRESHOLD = 5  # 연속 실패 N회 시 일시 중단
TAPOLOGY_CIRCUIT_BREAKER_COOLDOWN = 60  # 중단 시 대기 시간 (초)

# ISO 3166-1 alpha-2 → 국가명 매핑
ISO_TO_COUNTRY: dict[str, str] = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AR": "Argentina",
    "AM": "Armenia", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan",
    "BH": "Bahrain", "BD": "Bangladesh", "BY": "Belarus", "BE": "Belgium",
    "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BR": "Brazil",
    "BG": "Bulgaria", "CM": "Cameroon", "CA": "Canada", "CL": "Chile",
    "CN": "China", "CO": "Colombia", "CD": "DR Congo", "CG": "Republic of the Congo",
    "CR": "Costa Rica", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus",
    "CZ": "Czech Republic", "DK": "Denmark", "DO": "Dominican Republic",
    "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador", "EE": "Estonia",
    "FI": "Finland", "FR": "France", "GE": "Georgia", "DE": "Germany",
    "GH": "Ghana", "GR": "Greece", "GU": "Guam", "GT": "Guatemala",
    "GY": "Guyana", "HN": "Honduras", "HK": "Hong Kong", "HU": "Hungary",
    "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran",
    "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "IT": "Italy",
    "JM": "Jamaica", "JP": "Japan", "JO": "Jordan", "KZ": "Kazakhstan",
    "KE": "Kenya", "XK": "Kosovo", "KW": "Kuwait", "KG": "Kyrgyzstan",
    "LV": "Latvia", "LB": "Lebanon", "LT": "Lithuania", "LU": "Luxembourg",
    "MK": "North Macedonia", "MY": "Malaysia", "MX": "Mexico", "MD": "Moldova",
    "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco", "MM": "Myanmar",
    "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua",
    "NG": "Nigeria", "NO": "Norway", "PK": "Pakistan", "PS": "Palestine",
    "PA": "Panama", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines",
    "PL": "Poland", "PT": "Portugal", "PR": "Puerto Rico", "RO": "Romania",
    "RU": "Russia", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia",
    "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia", "ZA": "South Africa",
    "KR": "South Korea", "ES": "Spain", "LK": "Sri Lanka", "SE": "Sweden",
    "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan",
    "TH": "Thailand", "TN": "Tunisia", "TR": "Turkey", "TM": "Turkmenistan",
    "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan",
    "VE": "Venezuela", "VN": "Vietnam", "TT": "Trinidad and Tobago",
    "SR": "Suriname", "EN": "England", "SC": "Scotland", "WA": "Wales",
}


def _strip_nickname(display_name: str) -> str:
    """Tapology 표시명에서 닉네임을 제거한다.

    'Alex "Poatan" Pereira' -> 'Alex Pereira'
    """
    # ASCII 따옴표와 유니코드 따옴표 모두 처리
    result = re.sub(r'"[^"]*"\s*', "", display_name)
    result = re.sub(r'\u201c[^\u201d]*\u201d\s*', "", result)
    return result.strip()


class TapologyClient:
    """Tapology 국적 조회 클라이언트.

    - requests.Session으로 쿠키/커넥션 유지
    - fake_useragent로 매 요청마다 UA 로테이션
    - 연속 실패 시 circuit breaker로 일시 중단
    - 요청 간 2~4초 랜덤 딜레이
    """

    def __init__(self) -> None:
        self._session = http_requests.Session()
        self._consecutive_failures = 0

    def _get_headers(self) -> dict[str, str]:
        return {"User-Agent": _ua.random}

    def _request(self, url: str) -> http_requests.Response | None:
        """HTTP GET with circuit breaker."""
        if self._consecutive_failures >= TAPOLOGY_CIRCUIT_BREAKER_THRESHOLD:
            logger.warning(
                "Circuit breaker open (%d consecutive failures), "
                "cooling down %ds...",
                self._consecutive_failures,
                TAPOLOGY_CIRCUIT_BREAKER_COOLDOWN,
            )
            time.sleep(TAPOLOGY_CIRCUIT_BREAKER_COOLDOWN)
            self._consecutive_failures = 0

        try:
            resp = self._session.get(
                url, headers=self._get_headers(), timeout=10,
            )
            if resp.status_code == 200:
                self._consecutive_failures = 0
                return resp
            logger.warning("Tapology %d for %s", resp.status_code, url)
            self._consecutive_failures += 1
            return None
        except Exception as e:
            logger.warning("Tapology request error for %s: %s", url, e)
            self._consecutive_failures += 1
            return None

    def fetch_nationality(
        self, name: str, nickname: str | None = None,
    ) -> str | None:
        """Tapology 검색 → 상세 페이지에서 국기 ISO 코드로 국가명을 반환한다."""
        # 1) 검색
        search_term = name.replace(" ", "+")
        resp = self._request(
            f"https://www.tapology.com/search?term={search_term}",
        )
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select('a[href*="/fightcenter/fighters/"]')
        if not links:
            return None

        # 2) 이름 매칭으로 후보 필터링
        name_lower = name.lower().strip()
        candidates: list[tuple[str, str]] = []
        for a in links:
            display = a.get_text(strip=True)
            clean = _strip_nickname(display).lower().strip()
            if clean == name_lower:
                candidates.append((a["href"], display))

        if not candidates:
            return None

        # 3) 후보가 여러 명이고 nickname이 있으면 nickname으로 구분
        detail_path = candidates[0][0]
        if len(candidates) > 1 and nickname:
            nick_lower = nickname.lower()
            for href, display in candidates:
                if nick_lower in display.lower():
                    detail_path = href
                    break

        # 요청 간 딜레이
        time.sleep(random.uniform(*TAPOLOGY_BASE_DELAY))

        # 4) 상세 페이지에서 첫 번째 국기 ISO 코드 추출
        detail_resp = self._request(
            f"https://www.tapology.com{detail_path}",
        )
        if not detail_resp:
            return None

        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
        flag_img = detail_soup.select_one('img[src*="/flags/"]')
        if not flag_img:
            return None

        match = re.search(r"/flags/([A-Z]{2})", flag_img["src"])
        if not match:
            return None

        iso_code = match.group(1)
        return ISO_TO_COUNTRY.get(iso_code)

    def close(self) -> None:
        self._session.close()


async def fetch_nationality_from_tapology(
    name: str,
    nickname: str | None = None,
    *,
    client: TapologyClient | None = None,
) -> str | None:
    """Tapology 국적 조회의 async wrapper.

    client를 전달하면 세션을 재사용한다. 전달하지 않으면 일회용 세션을 생성한다.
    """
    if client:
        return await asyncio.to_thread(client.fetch_nationality, name, nickname)
    c = TapologyClient()
    try:
        return await asyncio.to_thread(c.fetch_nationality, name, nickname)
    finally:
        c.close()


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
