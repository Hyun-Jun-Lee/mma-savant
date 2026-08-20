import logging
import asyncio
import inspect
import json
import random
import httpx
import os
import sys
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from user_agent import generate_user_agent

from config import Config
from data_collector.driver import PlaywrightDriver, Crawl4AIDriver

TAPOLOGY_FETCH_SUCCEEDED = "succeeded"
TAPOLOGY_FETCH_EMPTY_RESPONSE = "empty_response"
TAPOLOGY_FETCH_WORKER_TIMEOUT = "worker_timeout"
TAPOLOGY_FETCH_WORKER_CRASH = "worker_crash"
TAPOLOGY_FETCH_PROTOCOL_ERROR = "protocol_error"
TAPOLOGY_FETCH_EXCEPTION = "fetch_exception"
UFC_RANKINGS_MAX_ATTEMPTS = 3
UFC_RANKINGS_RETRY_DELAY_SECONDS = 2.0
UFCSTATS_FIGHT_DETAIL_MAX_ATTEMPTS = 2
UFCSTATS_FIGHT_DETAIL_RETRY_DELAY_SECONDS = 2.0


def _parse_delay_range(value: str | None) -> tuple[float, float]:
    if not value:
        return (4.0, 8.0)
    normalized = value.strip().removeprefix("(").removesuffix(")")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) != 2:
        logging.warning("Invalid TAPOLOGY_SCRAPLING_DELAY_RANGE=%s; using 4.0,8.0", value)
        return (4.0, 8.0)
    try:
        start, end = float(parts[0]), float(parts[1])
    except ValueError:
        logging.warning("Invalid TAPOLOGY_SCRAPLING_DELAY_RANGE=%s; using 4.0,8.0", value)
        return (4.0, 8.0)
    if start < 0 or end < start:
        logging.warning("Invalid TAPOLOGY_SCRAPLING_DELAY_RANGE=%s; using 4.0,8.0", value)
        return (4.0, 8.0)
    return (start, end)


TAPOLOGY_SCRAPLING_DELAY_RANGE = _parse_delay_range(Config.TAPOLOGY_SCRAPLING_DELAY_RANGE)


@dataclass(frozen=True)
class TapologyFetchResult:
    stage: str
    url: str
    status: str
    html: str | None
    error: str | None
    elapsed_seconds: float


def _selector_for_url(url: str) -> Optional[str]:
    parsed_url = urlparse(url)
    host = parsed_url.netloc.lower()
    path = parsed_url.path.rstrip("/")

    if host.endswith("ufcstats.com"):
        if path.startswith("/statistics/events/"):
            return "table.b-statistics__table-events"
        if path.startswith("/statistics/fighters"):
            return "table.b-statistics__table"
        if path.startswith("/event-details/"):
            return "div.b-list__info-box"
        if path.startswith("/fight-details/"):
            return "table.b-fight-details__table"

    if _is_ufc_rankings_url(url):
        return "#rankings-panel-media"

    return None


def _is_ufc_rankings_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return (
        parsed_url.netloc.lower().endswith("ufc.com")
        and parsed_url.path.rstrip("/").endswith("/rankings")
    )


def _is_ufcstats_fight_details_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return (
        parsed_url.netloc.lower().endswith("ufcstats.com")
        and parsed_url.path.rstrip("/").startswith("/fight-details/")
    )


def _is_ufc_edge_forbidden_html(html_content: str | None) -> bool:
    if not html_content:
        return False

    return "403 Forbidden" in html_content and "Varnish cache server" in html_content


def _max_playwright_attempts_for_url(url: str) -> int:
    if _is_ufc_rankings_url(url):
        return UFC_RANKINGS_MAX_ATTEMPTS
    if _is_ufcstats_fight_details_url(url):
        return UFCSTATS_FIGHT_DETAIL_MAX_ATTEMPTS
    return 1


async def crawl_with_playwright(url: str) -> str:
    driver = PlaywrightDriver()
    page = None
    try:
        await driver.initialize()
        max_attempts = _max_playwright_attempts_for_url(url)
        wait_selector = _selector_for_url(url)

        for attempt in range(1, max_attempts + 1):
            if page:
                await page.close()

            page = await driver.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded")
                if wait_selector:
                    await page.wait_for_selector(wait_selector, state="attached", timeout=15000)
            except Exception as exc:
                try:
                    html_content = await page.content()
                except Exception:
                    html_content = None

                if _is_ufc_rankings_url(url) and _is_ufc_edge_forbidden_html(html_content):
                    if attempt < max_attempts:
                        logging.warning(
                            "UFC rankings page returned edge forbidden response; retrying (%s/%s)",
                            attempt,
                            max_attempts,
                        )
                        await page.close()
                        page = None
                        await asyncio.sleep(UFC_RANKINGS_RETRY_DELAY_SECONDS * attempt)
                        continue

                    logging.warning("UFC rankings page returned edge forbidden response after %s attempts", max_attempts)
                    return None

                if _is_ufcstats_fight_details_url(url) and attempt < max_attempts:
                    logging.warning(
                        "UFCStats fight detail crawl failed; retrying (%s/%s): url=%s error=%s",
                        attempt,
                        max_attempts,
                        url,
                        exc,
                    )
                    await page.close()
                    page = None
                    await asyncio.sleep(UFCSTATS_FIGHT_DETAIL_RETRY_DELAY_SECONDS * attempt)
                    continue

                raise

            html_content = await page.content()
            return html_content

        return None
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None
    finally:
        if page:
            await page.close()


async def close_playwright_crawler() -> None:
    await PlaywrightDriver().close()


async def close_crawl4ai_crawlers() -> None:
    await Crawl4AIDriver.close_all()


async def crawl_with_httpx(url: str) -> str:
    headers = {
        "User-Agent": generate_user_agent(os=('mac', 'linux'), device_type='desktop')
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in {403, 404}:
                logging.warning(
                    "크롤링 대상 페이지 접근 불가 또는 없음(status=%s): %s",
                    status_code,
                    e.response.url,
                )
                return None

            print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
            return None
        except Exception as e:
            print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
            return None


async def crawl_with_crawl4ai(url: str, run_config: Any = None) -> str:
    try:
        driver = Crawl4AIDriver()
        result = await driver.run_crawl(url, run_config)
        return _crawl4ai_result_html(result)
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None


async def crawl_tapology_with_scrapling(url: str) -> str:
    try:
        delay = random.uniform(*TAPOLOGY_SCRAPLING_DELAY_RANGE)
        logging.debug("Tapology Scrapling request delay %.2fs for %s", delay, url)
        await asyncio.sleep(delay)
        return await asyncio.to_thread(_fetch_tapology_with_scrapling, url)
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None


async def crawl_tapology_with_scrapling_result(
    url: str,
    *,
    stage: str = "unknown",
) -> TapologyFetchResult:
    started_at = time.perf_counter()
    try:
        html = await crawl_tapology_with_scrapling(url)
    except Exception as exc:
        return TapologyFetchResult(
            stage=stage,
            url=url,
            status=TAPOLOGY_FETCH_EXCEPTION,
            html=None,
            error=str(exc),
            elapsed_seconds=time.perf_counter() - started_at,
        )

    return TapologyFetchResult(
        stage=stage,
        url=url,
        status=TAPOLOGY_FETCH_SUCCEEDED if html else TAPOLOGY_FETCH_EMPTY_RESPONSE,
        html=html,
        error=None,
        elapsed_seconds=time.perf_counter() - started_at,
    )


def _fetch_tapology_with_scrapling(url: str) -> str | None:
    from scrapling.fetchers import StealthyFetcher

    response = StealthyFetcher.fetch(
        url,
        **_build_tapology_scrapling_fetch_kwargs(StealthyFetcher),
    )
    return _scrapling_response_html(response)


def _build_tapology_scrapling_fetch_kwargs(fetcher: Any) -> dict[str, Any]:
    kwargs = {
        "headless": True,
        "timeout": Config.TAPOLOGY_SCRAPLING_TIMEOUT_MS,
        "wait": 1_500,
        "network_idle": False,
        "google_search": True,
        "os_randomize": False,
        "block_webrtc": True,
        "allow_webgl": True,
        "retries": Config.TAPOLOGY_SCRAPLING_RETRIES,
    }

    fetch_signature = inspect.signature(fetcher.fetch)
    supports_extra_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in fetch_signature.parameters.values()
    )
    if supports_extra_kwargs or "solve_cloudflare" in fetch_signature.parameters:
        kwargs["solve_cloudflare"] = True

    return kwargs


class TapologyScraplingWorkerManager:
    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._stderr_task: asyncio.Task | None = None
        self._request_count = 0
        self._lock = asyncio.Lock()
        self._warned_low_hard_timeout = False

    async def fetch(self, stage: str, url: str) -> TapologyFetchResult:
        started_at = time.perf_counter()
        try:
            return await asyncio.wait_for(
                self._fetch_with_lock(stage, url, started_at),
                timeout=self._hard_timeout_seconds(),
            )
        except asyncio.TimeoutError:
            await self.restart()
            return TapologyFetchResult(
                stage=stage,
                url=url,
                status=TAPOLOGY_FETCH_WORKER_TIMEOUT,
                html=None,
                error=f"hard timeout exceeded ({self._hard_timeout_seconds():.1f}s)",
                elapsed_seconds=time.perf_counter() - started_at,
            )
        except Exception as exc:
            await self.restart()
            return TapologyFetchResult(
                stage=stage,
                url=url,
                status=TAPOLOGY_FETCH_PROTOCOL_ERROR,
                html=None,
                error=str(exc),
                elapsed_seconds=time.perf_counter() - started_at,
            )

    async def restart(self) -> None:
        await self.close()
        self._request_count = 0

    async def close(self) -> None:
        process = self._process
        self._process = None
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None

    async def _fetch_with_lock(
        self,
        stage: str,
        url: str,
        started_at: float,
    ) -> TapologyFetchResult:
        async with self._lock:
            delay = random.uniform(*TAPOLOGY_SCRAPLING_DELAY_RANGE)
            logging.debug("Tapology Scrapling worker request delay %.2fs for %s", delay, url)
            await asyncio.sleep(delay)

            process = await self._ensure_process()
            if process.stdin is None or process.stdout is None:
                await self.restart()
                return TapologyFetchResult(
                    stage=stage,
                    url=url,
                    status=TAPOLOGY_FETCH_WORKER_CRASH,
                    html=None,
                    error="worker stdio is unavailable",
                    elapsed_seconds=time.perf_counter() - started_at,
                )

            request_id = uuid.uuid4().hex
            payload = json.dumps({"id": request_id, "stage": stage, "url": url}) + "\n"
            try:
                process.stdin.write(payload.encode("utf-8"))
                await process.stdin.drain()
                response_line = await process.stdout.readline()
            except Exception as exc:
                await self.restart()
                return TapologyFetchResult(
                    stage=stage,
                    url=url,
                    status=TAPOLOGY_FETCH_WORKER_CRASH,
                    html=None,
                    error=str(exc),
                    elapsed_seconds=time.perf_counter() - started_at,
                )

            self._request_count += 1
            if not response_line:
                await self.restart()
                return TapologyFetchResult(
                    stage=stage,
                    url=url,
                    status=TAPOLOGY_FETCH_WORKER_CRASH,
                    html=None,
                    error="worker exited without response",
                    elapsed_seconds=time.perf_counter() - started_at,
                )

            result = self._decode_worker_response(stage, url, request_id, response_line, started_at)
            if self._request_count >= Config.TAPOLOGY_WORKER_MAX_REQUESTS:
                await self.restart()
            return result

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._process and self._process.returncode is None:
            return self._process

        env = os.environ.copy()
        src_dir = str(Path(__file__).resolve().parents[1])
        env["PYTHONPATH"] = (
            src_dir if not env.get("PYTHONPATH") else f"{src_dir}{os.pathsep}{env['PYTHONPATH']}"
        )
        self._process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "data_collector.tapology_scrapling_worker",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._stderr_task = asyncio.create_task(self._drain_stderr(self._process))
        return self._process

    async def _drain_stderr(self, process: asyncio.subprocess.Process) -> None:
        if process.stderr is None:
            return
        while True:
            line = await process.stderr.readline()
            if not line:
                return
            logging.warning("Tapology Scrapling worker stderr: %s", line.decode("utf-8", errors="replace").rstrip())

    def _decode_worker_response(
        self,
        stage: str,
        url: str,
        request_id: str,
        response_line: bytes,
        started_at: float,
    ) -> TapologyFetchResult:
        html_path: str | None = None
        try:
            payload = json.loads(response_line.decode("utf-8"))
            html_path = payload.get("html_path")
            if payload.get("id") != request_id:
                return TapologyFetchResult(
                    stage=stage,
                    url=url,
                    status=TAPOLOGY_FETCH_PROTOCOL_ERROR,
                    html=None,
                    error=f"worker response id mismatch: {payload.get('id')}",
                    elapsed_seconds=time.perf_counter() - started_at,
                )
            html = self._read_html_path(html_path) if html_path else None
            return TapologyFetchResult(
                stage=str(payload.get("stage") or stage),
                url=str(payload.get("url") or url),
                status=str(payload.get("status") or TAPOLOGY_FETCH_PROTOCOL_ERROR),
                html=html,
                error=payload.get("error"),
                elapsed_seconds=float(payload.get("elapsed_seconds") or (time.perf_counter() - started_at)),
            )
        except Exception as exc:
            return TapologyFetchResult(
                stage=stage,
                url=url,
                status=TAPOLOGY_FETCH_PROTOCOL_ERROR,
                html=None,
                error=str(exc),
                elapsed_seconds=time.perf_counter() - started_at,
            )
        finally:
            if html_path:
                Path(html_path).unlink(missing_ok=True)

    def _read_html_path(self, html_path: str) -> str | None:
        path = Path(html_path)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    def _hard_timeout_seconds(self) -> float:
        delay_max = TAPOLOGY_SCRAPLING_DELAY_RANGE[1]
        scrapling_timeout = Config.TAPOLOGY_SCRAPLING_TIMEOUT_MS / 1000
        attempt_count = Config.TAPOLOGY_SCRAPLING_RETRIES + 1
        derived = (
            delay_max
            + scrapling_timeout * attempt_count
            + Config.TAPOLOGY_WORKER_HARD_TIMEOUT_GRACE_SECONDS
        )
        configured = Config.TAPOLOGY_WORKER_HARD_TIMEOUT_SECONDS
        if configured is None:
            return derived
        if configured < derived:
            if not self._warned_low_hard_timeout:
                logging.warning(
                    "TAPOLOGY_WORKER_HARD_TIMEOUT_SECONDS %.1fs is lower than derived %.1fs; using derived",
                    configured,
                    derived,
                )
                self._warned_low_hard_timeout = True
            return derived
        return configured


_TAPOLOGY_SCRAPLING_WORKER = TapologyScraplingWorkerManager()


async def crawl_tapology_with_scrapling_worker(url: str) -> str | None:
    result = await crawl_tapology_with_scrapling_worker_result(
        url,
        stage="unknown",
    )
    return result.html


async def crawl_tapology_with_scrapling_worker_result(
    url: str,
    *,
    stage: str = "unknown",
) -> TapologyFetchResult:
    return await _TAPOLOGY_SCRAPLING_WORKER.fetch(stage, url)


async def _crawl_tapology_with_scrapling_worker_fetch_result(
    stage: str,
    url: str,
) -> TapologyFetchResult:
    return await crawl_tapology_with_scrapling_worker_result(url, stage=stage)


crawl_tapology_with_scrapling_worker.fetch_result = _crawl_tapology_with_scrapling_worker_fetch_result


async def close_tapology_scrapling_worker() -> None:
    await _TAPOLOGY_SCRAPLING_WORKER.close()


def _crawl4ai_result_html(result: Any) -> str | None:
    if not result:
        return None
    if isinstance(result, str):
        return result
    return getattr(result, "html", None) or getattr(result, "cleaned_html", None)


def _scrapling_response_html(response: Any) -> str | None:
    if not response:
        return None

    for attr in ("body", "html_content", "text"):
        value = getattr(response, attr, None)
        if value is None:
            continue
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        value_text = str(value)
        if value_text and value_text != "None":
            return value_text

    return None
