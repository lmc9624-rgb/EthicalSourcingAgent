from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from time import time
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
CACHE_SECONDS = 24 * 60 * 60
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "source_requests"

SOURCES = {
    "dol_goods": ({
        "name": "U.S. Department of Labor List of Goods Produced by Child Labor or Forced Labor",
        "publisher": "U.S. Department of Labor, Bureau of International Labor Affairs",
        "url": "https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/TVPRA_List_2024.xlsx",
        "filename": "dol_tvpra_list_2024.xlsx",
        "hosts": ("www.dol.gov", "dol.gov"),
    },),
    "opensanctions": (
        {
            "name": "OpenSanctions U.S. OFAC SDN dataset (nested CSV)",
            "publisher": "OpenSanctions",
            "url": "https://data.opensanctions.org/datasets/latest/us_ofac_sdn/targets.nested.csv",
            "filename": "opensanctions_us_ofac_sdn_targets.nested.csv",
            "hosts": ("data.opensanctions.org",),
        },
        {
            "name": "OpenSanctions U.N. Security Council sanctions dataset (nested CSV)",
            "publisher": "OpenSanctions",
            "url": "https://data.opensanctions.org/datasets/latest/un_sc_sanctions/targets.nested.csv",
            "filename": "opensanctions_un_sc_sanctions_targets.nested.csv",
            "hosts": ("data.opensanctions.org",),
        },
    ),
}


class _AllowedRedirects(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: tuple[str, ...]):
        self.allowed_hosts = set(allowed_hosts)

    def redirect_request(self, request, response, code, message, headers, new_url):
        parsed = urlparse(new_url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise ValueError("Redirect target is outside the configured HTTPS host allowlist")
        return super().redirect_request(request, response, code, message, headers, new_url)


def _metadata_path(output_path: Path) -> Path:
    return output_path.with_suffix(output_path.suffix + ".source.json")


def _limit_description() -> str:
    if MAX_RESPONSE_BYTES >= 1024 * 1024:
        return f"{MAX_RESPONSE_BYTES // (1024 * 1024)} MB"
    return f"{MAX_RESPONSE_BYTES} bytes"


def _fresh_cache(output_path: Path) -> bool:
    metadata_path = _metadata_path(output_path)
    if not output_path.is_file() or not metadata_path.is_file():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        retrieved = datetime.fromisoformat(metadata["retrieved_at"]).timestamp()
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return 0 <= time() - retrieved < CACHE_SECONDS


def _download(record: dict, cache_dir: Path, refresh: bool = False) -> tuple[Path, bool]:
    output_path = cache_dir / record["filename"]
    if not refresh and _fresh_cache(output_path):
        return output_path, True

    parsed = urlparse(record["url"])
    if parsed.scheme != "https" or parsed.hostname not in record["hosts"]:
        raise ValueError("Configured endpoint is outside the HTTPS host allowlist")

    cache_dir.mkdir(parents=True, exist_ok=True)
    request = Request(record["url"], headers={"User-Agent": "SourceSight bounded source request/1.0"})
    opener = build_opener(_AllowedRedirects(record["hosts"]))
    temporary_path = None
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            final = urlparse(response.geturl())
            if final.scheme != "https" or final.hostname not in record["hosts"]:
                raise ValueError("Response URL is outside the configured HTTPS host allowlist")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise ValueError(f"Response exceeds the configured {_limit_description()} limit")
            with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as temporary:
                temporary_path = Path(temporary.name)
                total = 0
                while chunk := response.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        raise ValueError(f"Response exceeds the configured {_limit_description()} limit")
                    temporary.write(chunk)
        os.replace(temporary_path, output_path)
        metadata = {
            "source": record["name"], "publisher": record["publisher"],
            "source_url": record["url"],
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "bytes": output_path.stat().st_size,
            "notice": "Downloaded source material; not an identity match or a SourceSight finding.",
        }
        metadata_path = _metadata_path(output_path)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=cache_dir, delete=False) as temporary:
            temporary.write(json.dumps(metadata, indent=2) + "\n")
            metadata_temp_path = Path(temporary.name)
        os.replace(metadata_temp_path, metadata_path)
        return output_path, False
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manually fetch bounded public data sources; never called automatically by the app.")
    parser.add_argument("--source", choices=tuple(SOURCES), required=True)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--refresh", action="store_true", help="Ignore a fresh 24-hour cache and request again")
    args = parser.parse_args(argv)

    print("Check publisher terms and permitted use before requesting or using this data.")
    try:
        for record in SOURCES[args.source]:
            path, cached = _download(record, args.cache_dir, refresh=args.refresh)
            state = "cache" if cached else "downloaded"
            print(f"{state}: {record['name']} ({record['publisher']})")
            print(f"  Source: {record['url']}")
            print(f"  File: {path}")
            print(f"  Attribution: {_metadata_path(path)}")
    except Exception as exc:
        print(f"Request stopped safely: {type(exc).__name__}: {exc}")
        return 2
    print("Downloads are source material only; no entity resolution or risk finding was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())