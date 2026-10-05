from __future__ import annotations

from sourcesight.models import Entity, Product


REPORT = {
    "title": "Debt Before Day One",
    "publisher": "Transparentem",
    "report_date": "2026-10",
    "url": "https://transparentem.org/wp-content/uploads/2026/09/Debt-Before-Day-One.pdf",
    "fieldwork": "November 2025-June 2026",
    "interviews": 24,
    "manufacturers_interviewed": 7,
    "source_group": "transparentem-debt-before-day-one-2026",
    "attribution": "User-supplied case material attributed to the Transparentem report; SourceSight did not independently retrieve or verify the PDF or its claims.",
}

_BASE_INDICATORS = ("debt_bondage", "abuse_of_vulnerability")

COMPANIES = (
    {
        "id": "TSM-COMPAL", "name": "Compal Electronics", "product": "Notebook computers", "sector": "electronics", "interviews": 4,
        "workers": "Vietnamese women", "fees": "$2,050-$6,400", "borrowed": "All interviewed workers borrowed",
        "fee_range_usd": (2050, 6400), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed. Separately, the report says 550+ former workers each paid over USD 6,000 and were only partly reimbursed.",
        "fee_range_usd": (2050, 6400), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed; the report separately describes 550+ former workers who each paid over USD 6,000 and were only partly reimbursed.",
        "details": "The report says 550+ former workers paid over $6,000 and were only partly reimbursed.",
        "response": "The report says Compal reported reimbursing current workers and announced a phased plan for former workers.",
        "reliability": "high", "indicators": _BASE_INDICATORS,
        "buyers": ("Amazon", "Dell", "Lenovo", "Delta Electronics", "Google", "Nvidia"),
        "facility_context": "Pingzhen, Taoyuan", "worker_origin_country": "VN",
        "buyer_countries": {"Amazon": "US", "Dell": "US", "Lenovo": "HK", "Delta Electronics": "TW", "Google": "US", "Nvidia": "US"},
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-GARMIN", "name": "Garmin", "product": "GPS devices", "sector": "electronics", "interviews": 4,
        "workers": "Vietnamese women", "fees": "$2,950-$4,050", "borrowed": "All interviewed workers borrowed; 3 remained indebted after 12 months",
        "fee_range_usd": (2950, 4050), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed; three remained indebted after 12 months.",
        "fee_range_usd": (2950, 4050), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed; three remained in debt after 12 months.",
        "details": "The report describes deception and threats, and alleges retaliation by an unnamed Vietnamese recruitment agency.",
        "response": "The report says Garmin reported reimbursing current employees and contacting former employees.",
        "reliability": "high", "indicators": _BASE_INDICATORS + ("deception", "intimidation_and_threats"),
        "buyers": ("Amazon", "Decathlon", "REI", "Best Buy", "Walmart"),
        "facility_context": "Guishan, Taoyuan", "worker_origin_country": "VN",
        "buyer_countries": {"Amazon": "US", "Decathlon": "FR", "REI": "US", "Best Buy": "US", "Walmart": "US"},
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-PEGAVISION", "name": "Pegavision", "product": "Contact lenses", "sector": "medical devices", "interviews": 4,
        "workers": "Vietnamese women", "fees": "$4,500-$5,200", "borrowed": "All interviewed workers borrowed",
        "fee_range_usd": (4500, 5200), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed; one also paid a USD 900 deposit.",
        "monthly_broker_fee_usd": (50, 60),
        "fee_range_usd": (4500, 5200), "fee_paying_workers": 4,
        "debt_evidence": "All four interviewed workers borrowed; one also paid a USD 900 deposit.",
        "monthly_broker_fee_usd": (50, 60),
        "details": "The report describes one $900 deposit and monthly broker fees.",
        "response": "The report says Pegavision committed to a zero-fee policy and reimbursement.",
        "reliability": "high", "indicators": _BASE_INDICATORS,
        "buyers": ("Visioneering Technologies",),
        "facility_context": "Guishan, Taoyuan", "worker_origin_country": "VN",
        "buyer_countries": {"Visioneering Technologies": "US"},
        "ownership_to_verify": ("Pegatron",),
    },
    {
        "id": "TSM-CMC", "name": "China Motor Corporation", "product": "Vehicles", "sector": "automotive", "interviews": 2,
        "workers": "Thai men", "fees": "$3,850-$4,200", "borrowed": "At least one interviewed worker borrowed",
        "fee_range_usd": (3850, 4200), "fee_paying_workers": 2,
        "debt_evidence": "At least one of the two interviewed workers borrowed; the report describes ongoing monthly broker fees.",
        "monthly_broker_fee_usd": (50, 60),
        "fee_range_usd": (3850, 4200), "fee_paying_workers": 2,
        "debt_evidence": "At least one of the two interviewed workers borrowed; the report also describes monthly broker fees.",
        "monthly_broker_fee_usd": (50, 60),
        "details": "The report describes monthly fees.",
        "response": "The report says the company began an internal review; reimbursement status is unclear.",
        "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Mitsubishi Motors", "Vantage Vehicles", "Yulon Group"),
        "facility_context": "Facility locality not supplied", "worker_origin_country": "TH",
        "buyer_countries": {"Mitsubishi Motors": "JP", "Vantage Vehicles": "US", "Yulon Group": "TW"},
        "ownership_to_verify": ("Mitsubishi Motors (reported 14% ownership claim)", "Yulon-linked entities (reported at least 34% claim)"),
    },
    {
        "id": "TSM-AOT", "name": "Advanced Optoelectronic Technology (AOT)", "product": "Optoelectronic components", "sector": "electronics", "interviews": 4,
        "workers": "Filipino workers", "fees": "$1,000-$1,200 for 3 workers", "borrowed": "One worker reportedly took a currency-switch loan",
        "fee_range_usd": (1000, 1200), "fee_paying_workers": 3,
        "debt_evidence": "Three of four interviewed workers paid fees; one described a currency-switch loan that inflated repayment burden.",
        "monthly_broker_fee_usd": (50, 60),
        "fee_range_usd": (1000, 1200), "fee_paying_workers": 3,
        "debt_evidence": "Three of four workers paid fees; one described a currency-switch loan that increased repayment burden.",
        "monthly_broker_fee_usd": (50, 60),
        "details": "The report describes monthly fees. AOT did not respond to the report according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium",
        "indicators": _BASE_INDICATORS + ("deception",),
        "buyers": ("Garmin (former reported connection)", "Samsung (former reported connection)"),
        "facility_context": "Hukou Township, Hsinchu County", "worker_origin_country": "PH",
        "buyer_countries": {"Garmin": "TW", "Samsung": "KR"},
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-DGI", "name": "Digital Generation International (DGI)", "product": "Electronics", "sector": "electronics", "interviews": 3,
        "workers": "Vietnamese women", "fees": "$5,500-$6,200", "borrowed": "2 interviewed workers remained indebted",
        "fee_range_usd": (5500, 6200), "fee_paying_workers": 3,
        "debt_evidence": "Two of three interviewed workers remained indebted; the report also describes renewal and dormitory charges.",
        "monthly_broker_fee_usd": (50, 60),
        "fee_range_usd": (5500, 6200), "fee_paying_workers": 3,
        "debt_evidence": "Two of three interviewed workers remained in debt; the report also describes renewal and dormitory charges.",
        "monthly_broker_fee_usd": (50, 60),
        "details": "The report describes a $1,800 renewal fee and dormitory charges. DGI did not respond according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Delta Electronics", "Foxconn", "Acer (former reported connection)"),
        "facility_context": "Facility locality not supplied", "worker_origin_country": "VN",
        "buyer_countries": {"Delta Electronics": "TW", "Foxconn": "TW", "Acer": "TW"},
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-TSURUMI", "name": "Tsurumi Pump", "product": "Water pumps", "sector": "machinery", "interviews": 3,
        "workers": "Vietnamese men", "fees": "$6,200-$6,300", "borrowed": "All interviewed workers remained indebted",
        "fee_range_usd": (6200, 6300), "fee_paying_workers": 3,
        "debt_evidence": "All three interviewed workers took on debt, sometimes with interest or by mortgaging family land.",
        "fee_range_usd": (6200, 6300), "fee_paying_workers": 3,
        "debt_evidence": "All three interviewed workers took on debt, sometimes with interest or by mortgaging family land.",
        "details": "No response reported according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Technosub",),
        "facility_context": "Pingzhen, Taoyuan", "worker_origin_country": "VN",
        "buyer_countries": {"Technosub": "CA"},
        "ownership_to_verify": ("Tsurumi Manufacturing",),
    },
    {
        "id": "TSM-AGENCY", "name": "Unnamed Vietnamese recruitment agency (Garmin hires)", "product": "", "sector": "electronics", "interviews": 4,
        "workers": "Vietnamese women interviewed about Garmin recruitment", "fees": "See Garmin factory profile",
        "borrowed": "Not separately quantified for the agency profile",
        "details": "The report attributes threats and alleged retaliation to this unnamed agency. No named agency identity or additional allegation is supplied here.",
        "response": "Report-attributed agency behavior; identity remains unnamed and the allegation is not independently verified here.",
        "reliability": "high", "indicators": ("intimidation_and_threats",),
        "buyers": (), "ownership_to_verify": (), "agency_profile": True,
    },
)


class CaseStudySource:
    """Report-attributed real product profiles; unconfirmed buyers are not supply edges."""

    def products(self) -> tuple[Product, ...]:
        return tuple(Product(
            id=company["id"], name=company["product"], brand=company["name"],
            summary=self._product_summary(company),
            root_entity_id=company["id"], edges=(),
        ) for company in COMPANIES if not company.get("agency_profile"))

    @staticmethod
    def _product_summary(company: dict) -> str:
        buyers = ", ".join(company["buyers"]) or "none named"
        summary = (
            f"Report-attributed recruitment-fee investigation at {company['name']}: "
            f"{company['interviews']} worker interviews ({company['workers']}); "
            f"reported fees {company['fees']}. {company['borrowed']}. {company['details']} "
            f"Report-stated company response: {company['response']} "
            f"Possible buyers named in the report (unconfirmed): {buyers}. "
            "No confirmed input map is supplied."
        )
        return summary.replace("$", "USD ")

    def entities(self) -> dict[str, Entity]:
        return {company["id"]: Entity(
            id=company["id"], name=company["name"], country="TW", region="",
            role="Recruitment agency (identity not named by report)" if company.get("agency_profile") else "Manufacturer",
            sector=company["sector"], address="", directors=(), owners=(), upstream_disclosed=None,
        ) for company in COMPANIES}

    def listings(self) -> tuple[dict, ...]:
        return ()

    def enforcement_events(self) -> tuple[dict, ...]:
        return ()

    def sector_baselines(self) -> tuple[dict, ...]:
        sectors = ("electronics", "automotive", "medical devices", "machinery")
        return tuple({
            "source_id": f"REPORT-OVERLAY-TW-{index:02d}", "sector": sector,
            "country": "TW", "score": 0.45, "reliability": "medium",
            "date": "2026-10-01", "source_group": REPORT["source_group"],
            "description": "Case-study overlay derived from the same Transparentem report; not independent corroboration.",
        } for index, sector in enumerate(sectors, 1))

    def trade_profiles(self) -> dict[str, dict]:
        return {}

    def documents(self) -> dict[str, tuple[dict, ...]]:
        return {company["id"]: ({
            "id": f"REPORT-WORKER-{company['id']}", "type": "report-attributed worker interviews",
            "date": "2026-10-01", "reliability": company["reliability"],
            "summary": (
                f"Transparentem report-attributed summary: {company['interviews']} interviews; "
                f"{company['workers']}; reported fees {company['fees']}; {company['borrowed']}. "
                f"{company['details']}"
            ),
            "ilo_indicators": list(company["indicators"]),
            "source_group": REPORT["source_group"],
        },) for company in COMPANIES}


def company_by_id(company_id: str) -> dict:
    return next(company for company in COMPANIES if company["id"] == company_id)


def recruitment_debt_profiles() -> tuple[dict, ...]:
    """Return only fee ranges and debt context explicitly described for interview samples."""
    return tuple({
        "company_id": company["id"],
        "company": company["name"],
        "worker_origin_country": company.get("worker_origin_country", "Unknown"),
        "workers_interviewed": company["interviews"],
        "workers_with_reported_fees": company.get("fee_paying_workers", company["interviews"]),
        "fee_low_usd": company["fee_range_usd"][0],
        "fee_high_usd": company["fee_range_usd"][1],
        "debt_evidence": company["debt_evidence"],
        "monthly_broker_fee_usd": company.get("monthly_broker_fee_usd"),
    } for company in COMPANIES if not company.get("agency_profile"))


def possible_buyer_relationships(company: dict) -> tuple[dict, ...]:
    """Report-named buyer leads with a conditional tier position, never a graph edge."""
    relationships = []
    for raw_name in company["buyers"]:
        former = "(former reported connection)" in raw_name
        name = raw_name.replace("(former reported connection)", "").strip()
        relationships.append({
            "company": name,
            "country": company.get("buyer_countries", {}).get(name),
            "tier_position": "Potential direct buyer (Tier 1 downstream if confirmed)",
            "status": "Former connection reported; not current or confirmed" if former
            else "Possible connection named in report; unconfirmed",
            "propagates_risk": False,
        })
    return tuple(relationships)


def case_geographic_context(company_id: str, country_centroids: dict[str, tuple[float, float]]) -> dict:
    """Build country-level report context without creating material-supplier edges."""
    company = company_by_id(company_id)
    taiwan = country_centroids.get("TW")
    site = {
        "company": company["name"], "country": "TW",
        "reported_locality": company.get("facility_context", "Facility locality not supplied"),
        "latitude": taiwan[0] if taiwan else None, "longitude": taiwan[1] if taiwan else None,
        "position": "Report-named focal manufacturer / study site",
        "source": "Transparentem case material supplied by the user",
    }

    worker_origins, worker_routes = [], []
    origin_code = company.get("worker_origin_country")
    origin_position = country_centroids.get(origin_code)
    if origin_code and origin_position:
        worker_origins.append({
            "country": origin_code, "latitude": origin_position[0], "longitude": origin_position[1],
            "position": "Reported worker-origin country",
            "source": "Transparentem case material supplied by the user",
        })
        if taiwan:
            worker_routes.append({
                "source_position": [origin_position[1], origin_position[0]],
                "target_position": [taiwan[1], taiwan[0]],
                "source_name": origin_code, "target_name": company["name"],
                "relationship": "Report-described worker recruitment corridor; not a material-supplier route",
                "evidence_status": "Report-attributed context",
            })

    markets = {}
    for relationship in possible_buyer_relationships(company):
        country = relationship["country"]
        position = country_centroids.get(country) if country else None
        if not position:
            continue
        market = markets.setdefault(country, {
            "country": country, "latitude": position[0], "longitude": position[1],
            "companies": [], "statuses": [],
            "position": "Potential buyer market; Tier 1 downstream only if confirmed",
        })
        market["companies"].append(relationship["company"])
        market["statuses"].append(relationship["status"])

    buyer_markets, buyer_routes = [], []
    for country, market in sorted(markets.items()):
        market["companies"] = tuple(sorted(set(market["companies"])))
        market["status"] = "Includes former report-named connection" if any(
            status.startswith("Former") for status in market["statuses"]
        ) else "Report-named possible connection(s); unconfirmed"
        buyer_markets.append(market)
        if taiwan and country != "TW":
            buyer_routes.append({
                "source_position": [taiwan[1], taiwan[0]],
                "target_position": [market["longitude"], market["latitude"]],
                "source_name": company["name"], "target_name": f"Potential buyer market ({country})",
                "relationship": "Potential direct downstream buyer market (Tier 1 only if confirmed)",
                "evidence_status": market["status"], "companies": ", ".join(market["companies"]),
            })

    return {
        "site": site, "worker_origins": tuple(worker_origins), "worker_routes": tuple(worker_routes),
        "buyer_markets": tuple(buyer_markets), "buyer_routes": tuple(buyer_routes),
        "upstream_material_tiers": "Upstream material supplier tiers are not identified in the supplied brief or public list screen.",
    }


def report_relationships(company_id: str) -> tuple[dict, ...]:
    """Report-named affiliates and recruiter links; these are not supply edges."""
    company = company_by_id(company_id)
    relationships = []
    if company_id == "TSM-GARMIN":
        relationships.append({
            "id": "TSM-AGENCY", "name": "Unnamed Vietnamese recruitment agency",
            "relationship": "Recruiter for Garmin hires, per report",
            "basis": "The brief attributes fee deception, threats and alleged retaliation to this unnamed agency.",
            "association_weight": 1.0, "country": "VN",
            "locality": "Vietnam (country-centroid context; agency office not identified)",
            "is_investigated": True,
        })
    affiliates = {
        "TSM-PEGAVISION": ({"name": "Pegatron", "weight": 1.0, "basis": "Report names Pegatron as ultimate controller; independent ownership confirmation remains a verification lead."},),
        "TSM-CMC": (
            {"name": "Mitsubishi Motors", "weight": 0.14, "basis": "Report describes a 14% shareholding; this is an ownership link, not a product-supplier edge."},
            {"name": "Yulon Group-linked holders", "weight": 0.34, "basis": "Report says Yulon-linked holders own at least 34%; exact entities and shareholding require verification."},
        ),
        "TSM-TSURUMI": ({"name": "Tsurumi Manufacturing", "weight": 1.0, "basis": "Report describes Tsurumi Pump as a subsidiary; independent ownership confirmation remains a verification lead."},),
    }
    countries = {"Pegatron": "TW", "Mitsubishi Motors": "JP", "Yulon Group-linked holders": "TW", "Tsurumi Manufacturing": "JP"}
    for affiliate in affiliates.get(company_id, ()):
        relationships.append({
            "id": f"AFFILIATE-{company_id}-{_slug(affiliate['name'])}", "name": affiliate["name"],
            "relationship": "Report-named corporate affiliation / ownership lead",
            "basis": affiliate["basis"], "association_weight": affiliate["weight"],
            "country": countries[affiliate["name"]], "locality": "Headquarters not resolved in this view",
            "is_investigated": False,
        })
    return tuple(relationships)


def _slug(value: str) -> str:
    return "-".join(part.lower() for part in value.replace("&", "and").split())