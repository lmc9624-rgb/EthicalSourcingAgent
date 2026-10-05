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
        "details": "The report says 550+ former workers paid over $6,000 and were only partly reimbursed.",
        "response": "The report says Compal reported reimbursing current workers and announced a phased plan for former workers.",
        "reliability": "high", "indicators": _BASE_INDICATORS,
        "buyers": ("Amazon", "Dell", "Lenovo", "Delta Electronics", "Google", "Nvidia"),
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-GARMIN", "name": "Garmin", "product": "GPS devices", "sector": "electronics", "interviews": 4,
        "workers": "Vietnamese women", "fees": "$2,950-$4,050", "borrowed": "All interviewed workers borrowed; 3 remained indebted after 12 months",
        "details": "The report describes deception and threats, and alleges retaliation by an unnamed Vietnamese recruitment agency.",
        "response": "The report says Garmin reported reimbursing current employees and contacting former employees.",
        "reliability": "high", "indicators": _BASE_INDICATORS + ("deception", "intimidation_and_threats"),
        "buyers": ("Amazon", "Decathlon", "REI", "Best Buy", "Walmart"),
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-PEGAVISION", "name": "Pegavision", "product": "Contact lenses", "sector": "medical devices", "interviews": 4,
        "workers": "Vietnamese women", "fees": "$4,500-$5,200", "borrowed": "All interviewed workers borrowed",
        "details": "The report describes one $900 deposit and monthly broker fees.",
        "response": "The report says Pegavision committed to a zero-fee policy and reimbursement.",
        "reliability": "high", "indicators": _BASE_INDICATORS,
        "buyers": ("Visioneering Technologies",),
        "ownership_to_verify": ("Pegatron",),
    },
    {
        "id": "TSM-CMC", "name": "China Motor Corporation", "product": "Vehicles", "sector": "automotive", "interviews": 2,
        "workers": "Thai men", "fees": "$3,850-$4,200", "borrowed": "At least one interviewed worker borrowed",
        "details": "The report describes monthly fees.",
        "response": "The report says the company began an internal review; reimbursement status is unclear.",
        "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Mitsubishi Motors", "Vantage Vehicles", "Yulon Group"),
        "ownership_to_verify": ("Mitsubishi Motors (reported 14% ownership claim)", "Yulon-linked entities (reported at least 34% claim)"),
    },
    {
        "id": "TSM-AOT", "name": "Advanced Optoelectronic Technology (AOT)", "product": "Optoelectronic components", "sector": "electronics", "interviews": 4,
        "workers": "Filipino workers", "fees": "$1,000-$1,200 for 3 workers", "borrowed": "One worker reportedly took a currency-switch loan",
        "details": "The report describes monthly fees. AOT did not respond to the report according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium",
        "indicators": _BASE_INDICATORS + ("deception",),
        "buyers": ("Garmin", "Samsung (former reported connection)"),
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-DGI", "name": "Digital Generation International (DGI)", "product": "Electronics", "sector": "electronics", "interviews": 3,
        "workers": "Vietnamese women", "fees": "$5,500-$6,200", "borrowed": "2 interviewed workers remained indebted",
        "details": "The report describes a $1,800 renewal fee and dormitory charges. DGI did not respond according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Delta Electronics", "Foxconn", "Acer (former reported connection)"),
        "ownership_to_verify": (),
    },
    {
        "id": "TSM-TSURUMI", "name": "Tsurumi Pump", "product": "Water pumps", "sector": "machinery", "interviews": 3,
        "workers": "Vietnamese men", "fees": "$6,200-$6,300", "borrowed": "All interviewed workers remained indebted",
        "details": "No response reported according to the supplied case material.",
        "response": "No response reported.", "reliability": "medium", "indicators": _BASE_INDICATORS,
        "buyers": ("Technosub",),
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