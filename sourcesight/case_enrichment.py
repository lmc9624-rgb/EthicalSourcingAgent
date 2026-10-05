from __future__ import annotations

import csv
import json
from pathlib import Path
import re

from sourcesight import data_requests
from sourcesight.case_study import COMPANIES


CASE_LIST_DATASETS = (
    {
        "id": "us_dhs_uflpa",
        "name": "U.S. DHS UFLPA Entity List",
        "scope": "Entities subject to the U.S. Uyghur Forced Labor Prevention Act",
        "publisher": "U.S. Department of Homeland Security via OpenSanctions",
    },
    {
        "id": "us_cbp_forced_labor",
        "name": "U.S. CBP Withhold Release Orders and Findings",
        "scope": "U.S. Customs and Border Protection forced-labor orders and findings",
        "publisher": "U.S. Customs and Border Protection via OpenSanctions",
    },
    {
        "id": "c4ads_xinjiang",
        "name": "C4ADS Long Shadows (Xinjiang)",
        "scope": "C4ADS research dataset concerning companies linked to the XPCC",
        "publisher": "Center for Advanced Defense Studies via OpenSanctions",
    },
)

_GENERIC_SUFFIXES = {
    "inc", "incorporated", "corp", "corporation", "company", "co", "limited", "ltd",
    "llc", "plc", "sa", "ag", "gmbh",
}


def _normalize_name(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    while words and words[-1] in _GENERIC_SUFFIXES:
        words.pop()
    return " ".join(words)


def case_companies() -> tuple[str, ...]:
    """Return manufacturers and report-named buyers, with former labels removed."""
    names = set()
    for company in COMPANIES:
        if company.get("agency_profile"):
            continue
        names.add(company["name"])
        for buyer in company["buyers"]:
            names.add(re.sub(r"\s*\([^)]*\)\s*$", "", buyer).strip())
    return tuple(sorted(names, key=str.casefold))


def _record_names(row: dict[str, str]) -> set[str]:
    names = {row.get("name", "")}
    names.update(alias.strip() for alias in row.get("aliases", "").split("|") if alias.strip())
    return {_normalize_name(name) for name in names if _normalize_name(name)}


def screen_case_companies(cache_dir: Path | None = None, refresh: bool = False) -> dict:
    """Screen exact normalized names/aliases against public list snapshots.

    Name hits are review leads only. This routine deliberately does not alter
    assessment tiers because a text match is not confirmed entity resolution.
    """
    cache_dir = cache_dir or data_requests.DEFAULT_CACHE_DIR
    candidates = case_companies()
    candidate_keys = {_normalize_name(name): name for name in candidates}
    results = {name: {"matches": [], "datasets": {}} for name in candidates}
    snapshots = []

    for dataset in CASE_LIST_DATASETS:
        dataset_id = dataset["id"]
        record = {
            "name": dataset["name"],
            "publisher": dataset["publisher"],
            "url": f"https://data.opensanctions.org/datasets/latest/{dataset_id}/targets.simple.csv",
            "filename": f"opensanctions_{dataset_id}_targets.simple.csv",
            "hosts": ("data.opensanctions.org",),
        }
        path, cached = data_requests._download(record, cache_dir, refresh=refresh)
        metadata_path = data_requests._metadata_path(path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}

        hit_names = set()
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                for normalized in _record_names(row) & candidate_keys.keys():
                    company_name = candidate_keys[normalized]
                    hit_names.add(company_name)
                    results[company_name]["matches"].append({
                        "dataset": dataset["name"],
                        "listed_name": row.get("name", ""),
                        "entity_id": row.get("id", ""),
                        "match_basis": "Exact normalized name or listed alias; identity unconfirmed",
                        "source_url": record["url"],
                    })
        for company_name in candidates:
            results[company_name]["datasets"][dataset_id] = (
                "Exact name/alias candidate" if company_name in hit_names
                else "No exact match in this snapshot"
            )
        snapshots.append({
            **dataset,
            "dataset_id": dataset_id,
            "source_url": record["url"],
            "retrieved_at": metadata.get("retrieved_at", "unknown"),
            "cached": cached,
        })

    return {
        "companies": results,
        "snapshots": snapshots,
        "disclaimer": (
            "OpenSanctions exact-name/alias screening only. A candidate is not a confirmed identity or finding; "
            "absence of an exact match does not establish that an entity is clear. Matches do not change SourceSight tiers."
        ),
    }