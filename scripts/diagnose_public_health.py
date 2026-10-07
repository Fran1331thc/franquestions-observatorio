"""One-shot diagnostic for the public Streamlit health endpoint.

This script performs a small number of read-only requests.  It records status,
timing and redirect locations, while deliberately omitting response headers
that could contain cookies or other sensitive values.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def sanitize_body(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").replace("\r", "").strip()
    return " ".join(text.split())[:160]


def sanitize_url(url: str) -> str:
    """Keep routing evidence without retaining query values or fragments."""
    parts = urllib.parse.urlsplit(url)
    query_keys = [key for key, _ in urllib.parse.parse_qsl(parts.query)]
    safe_query = "&".join(f"{key}=<redacted>" for key in query_keys)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, safe_query, ""))


def probe(url: str, timeout: float, max_redirects: int) -> dict[str, object]:
    started = time.perf_counter()
    current = url
    redirects: list[dict[str, object]] = []
    status: int | None = None
    body = ""
    error = ""

    opener = urllib.request.build_opener(NoRedirect())
    try:
        for _ in range(max_redirects + 1):
            request = urllib.request.Request(
                current,
                headers={"User-Agent": "FranQuestions-health-diagnostic/1.0"},
            )
            try:
                response = opener.open(request, timeout=timeout)
                status = response.status
                body = sanitize_body(response.read(512))
                break
            except urllib.error.HTTPError as exc:
                status = exc.code
                location = exc.headers.get("Location")
                if status in {301, 302, 303, 307, 308} and location:
                    next_url = urllib.parse.urljoin(current, location)
                    redirects.append(
                        {
                            "status": status,
                            "from": sanitize_url(current),
                            "to": sanitize_url(next_url),
                        }
                    )
                    current = next_url
                    continue
                body = sanitize_body(exc.read(512))
                error = f"HTTP {status}"
                break
        else:
            error = f"more than {max_redirects} redirects"
    except Exception as exc:  # diagnostic boundary
        error = f"{type(exc).__name__}: {exc}"

    duration_ms = round((time.perf_counter() - started) * 1000)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timestamp_costa_rica": datetime.now(ZoneInfo("America/Costa_Rica")).isoformat(
            timespec="seconds"
        ),
        "requested_url": sanitize_url(url),
        "final_url": sanitize_url(current),
        "http_status": status,
        "body_excerpt": body,
        "duration_ms": duration_ms,
        "redirect_count": len(redirects),
        "redirects": redirects,
        "result": "pass" if status == 200 and body == "ok" else "fail",
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max-redirects", type=int, default=50)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=0.0)
    args = parser.parse_args()
    failed = False
    for url in args.urls:
        passed = False
        for attempt in range(1, args.attempts + 1):
            result = probe(url, args.timeout, args.max_redirects)
            result["attempt"] = attempt
            result["attempts"] = args.attempts
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if result["result"] == "pass":
                passed = True
                break
            if attempt < args.attempts:
                time.sleep(args.retry_delay)
        failed = failed or not passed
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
