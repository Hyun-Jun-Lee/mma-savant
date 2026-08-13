import json
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from data_collector.crawler import _fetch_tapology_with_scrapling


def main() -> int:
    if len(sys.argv) > 1:
        _fetch_and_write(
            request_id="debug",
            stage=sys.argv[2] if len(sys.argv) > 2 else "debug",
            url=sys.argv[1],
        )
        return 0

    for line in sys.stdin:
        raw_line = line.strip()
        if not raw_line:
            continue

        request_id: str | None = None
        stage = "unknown"
        url = ""
        try:
            payload = json.loads(raw_line)
            request_id = str(payload.get("id") or "")
            stage = str(payload.get("stage") or "unknown")
            url = str(payload["url"])
            _fetch_and_write(request_id=request_id, stage=stage, url=url)
        except Exception:
            _write_response(
                {
                    "id": request_id,
                    "stage": stage,
                    "url": url,
                    "status": "fetch_exception",
                    "html_path": None,
                    "error": traceback.format_exc(),
                    "elapsed_seconds": 0,
                }
            )

    return 0


def _fetch_and_write(*, request_id: str | None, stage: str, url: str) -> None:
    started_at = time.perf_counter()
    html_path: str | None = None
    try:
        html = _fetch_tapology_with_scrapling(url)
        elapsed = time.perf_counter() - started_at
        if not html:
            _write_response(
                {
                    "id": request_id,
                    "stage": stage,
                    "url": url,
                    "status": "empty_response",
                    "html_path": None,
                    "error": None,
                    "elapsed_seconds": elapsed,
                }
            )
            return

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="tapology_",
            suffix=".html",
            delete=False,
        ) as handle:
            handle.write(html)
            html_path = handle.name

        _write_response(
            {
                "id": request_id,
                "stage": stage,
                "url": url,
                "status": "succeeded",
                "html_path": html_path,
                "error": None,
                "elapsed_seconds": elapsed,
            }
        )
    except Exception:
        if html_path:
            _unlink_quietly(html_path)
        _write_response(
            {
                "id": request_id,
                "stage": stage,
                "url": url,
                "status": "fetch_exception",
                "html_path": None,
                "error": traceback.format_exc(),
                "elapsed_seconds": time.perf_counter() - started_at,
            }
        )


def _write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _unlink_quietly(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
