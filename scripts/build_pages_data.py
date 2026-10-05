"""Export the report-backed assessment data for the static GitHub Pages UI."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sourcesight.case_study import (  # noqa: E402
    COMPANIES,
    REPORT,
    CaseStudySource,
    possible_buyer_relationships,
    recruitment_debt_profiles,
    report_relationships,
)
from sourcesight.engine import TIER_ORDER, _tier, assess_product  # noqa: E402
from sourcesight.signals import PILLAR_WEIGHTS, PILLARS, detect_signals, noisy_or  # noqa: E402


COUNTRY_CENTROIDS = {
    "CN": [35.9, 104.2], "IN": [20.6, 78.9], "VN": [16.0, 106.0],
    "MY": [4.2, 102.0], "TH": [15.8, 101.0], "TW": [23.7, 120.96],
    "PH": [12.9, 121.8], "US": [37.1, -95.7], "HK": [22.3, 114.2],
    "FR": [46.2, 2.2], "JP": [36.2, 138.3], "KR": [36.4, 127.8],
    "CA": [56.1, -106.3],
}
TAIWAN_LOCALITIES = {
    "Pingzhen, Taoyuan": [24.945752, 121.218359],
    "Guishan, Taoyuan": [24.992517, 121.337767],
    "Hukou Township, Hsinchu County": [24.900599, 121.046839],
}
PIN_OFFSETS = {
    "TSM-COMPAL": [-0.018, -0.018], "TSM-TSURUMI": [0.018, 0.018],
    "TSM-GARMIN": [0.018, -0.018], "TSM-PEGAVISION": [-0.018, 0.018],
}
PORTS = [
    {"name": "Keelung Port", "location": "Keelung, Taiwan", "lat": 25.1307, "lon": 121.7392},
    {"name": "Taipei Port", "location": "New Taipei City, Taiwan", "lat": 25.155, "lon": 121.385},
    {"name": "Taichung Port", "location": "Taichung, Taiwan", "lat": 24.279, "lon": 120.523},
    {"name": "Kaohsiung Port", "location": "Kaohsiung, Taiwan", "lat": 22.615, "lon": 120.283},
]


def _agency_assessment(source: CaseStudySource) -> dict:
    entity_id = "TSM-AGENCY"
    signals = detect_signals(entity_id, source, mapped_inputs=False)
    scores = {
        pillar: noisy_or([signal.strength for signal in signals if signal.pillar == pillar])
        for pillar in PILLARS
    }
    composite = noisy_or([scores[pillar] * PILLAR_WEIGHTS[pillar] for pillar in PILLARS])
    convergence = sum(scores[pillar] >= 0.4 for pillar in PILLARS if pillar != "transparency")
    tier, reason = _tier(False, convergence, composite)
    return {"score": round(composite * 100, 1), "tier": tier, "reason": reason,
            "signals": [_signal_data(signal) for signal in signals]}


def _signal_data(signal) -> dict:
    return {
        "pillar": signal.pillar,
        "title": signal.title,
        "strength": round(signal.strength, 3),
        "claim": signal.claim_kind,
        "detail": signal.detail,
        "source_ids": list(signal.source_ids),
        "next_step": signal.next_step,
    }


def build_data() -> dict:
    source = CaseStudySource()
    products = {item.id: item for item in source.products()}
    recruiter_assessment = _agency_assessment(source)
    output = {
        "report": REPORT,
        "country_centroids": COUNTRY_CENTROIDS,
        "taiwan_localities": TAIWAN_LOCALITIES,
        "pin_offsets": PIN_OFFSETS,
        "ports": PORTS,
        "profiles": [],
        "recruiter": {
            "id": "TSM-AGENCY",
            "name": "Unnamed Vietnamese recruitment agency",
            "country": "VN",
            "location": "Office location not identified in the brief",
            "relationship": "The report attributes fee deception, threats, and alleged retaliation involving Garmin hires to an unnamed recruiter.",
            **recruiter_assessment,
        },
    }

    for company in COMPANIES:
        if company.get("agency_profile"):
            continue
        assessment = assess_product(source, company["id"])
        result = assessment.suppliers[company["id"]]
        score = round(result.composite_score * 100, 1)
        affiliations = []
        for relationship in report_relationships(company["id"]):
            investigated = relationship["is_investigated"]
            own_score = recruiter_assessment["score"] if investigated else None
            linked_score = own_score if own_score is not None else round(
                score * relationship["association_weight"], 1
            )
            affiliations.append({
                **relationship,
                "own_score": own_score,
                "linked_score": linked_score,
                "tier": recruiter_assessment["tier"] if investigated else "Association-weighted exposure",
            })
        locality_position = TAIWAN_LOCALITIES.get(company["facility_context"], COUNTRY_CENTROIDS["TW"])
        offset = PIN_OFFSETS.get(company["id"], [0, 0])
        position = [locality_position[0] + offset[0], locality_position[1] + offset[1]]
        profile = {
            "id": company["id"],
            "name": company["name"],
            "product": company["product"],
            "sector": company["sector"],
            "interviews": company["interviews"],
            "workers": company["workers"],
            "worker_origin_country": company.get("worker_origin_country", "Unknown"),
            "fees": company["fees"],
            "fee_low_usd": company.get("fee_range_usd", [None, None])[0],
            "fee_high_usd": company.get("fee_range_usd", [None, None])[1],
            "fee_paying_workers": company.get("fee_paying_workers", company["interviews"]),
            "debt_evidence": company.get("debt_evidence", company["borrowed"]),
            "monthly_broker_fee_usd": company.get("monthly_broker_fee_usd"),
            "details": company["details"],
            "response": company["response"],
            "facility_context": company["facility_context"],
            "position": position,
            "location_precision": "OSM locality centroid; not factory coordinates" if company["facility_context"] in TAIWAN_LOCALITIES else "Taiwan country centroid; locality not supplied",
            "score": score,
            "tier": result.own_tier,
            "tier_reason": result.tier_reason,
            "confidence": result.confidence,
            "confidence_score": round(result.confidence_score, 2),
            "convergence": result.convergence,
            "pillar_scores": {key: round(value, 3) for key, value in result.pillar_scores.items()},
            "ilo_indicators": list(result.ilo_indicators),
            "signals": [_signal_data(signal) for signal in result.signals],
            "buyers": list(possible_buyer_relationships(company)),
            "affiliations": affiliations,
            "upstream_edges": [
                {"supplier": edge.source, "buyer": edge.target, "input": edge.input_name, "share": edge.share}
                for edge in products[company["id"]].edges
            ],
        }
        output["profiles"].append(profile)

    output["debt_comparison"] = list(recruitment_debt_profiles())
    return output


if __name__ == "__main__":
    output_path = ROOT / "docs" / "data.json"
    output_path.write_text(json.dumps(build_data(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT)}")