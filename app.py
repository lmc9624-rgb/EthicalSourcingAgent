from __future__ import annotations

import altair as alt
from collections import defaultdict
import math
import pydeck as pdk
import streamlit as st

from sourcesight.engine import TIER_ORDER, _tier, assess_product
from sourcesight.case_study import (
    COMPANIES, REPORT, CaseStudySource, case_geographic_context, company_by_id,
    possible_buyer_relationships, recruitment_debt_profiles, report_relationships,
)
from sourcesight.case_enrichment import screen_case_companies
from sourcesight.signals import PILLAR_WEIGHTS, PILLARS, detect_signals, noisy_or


st.set_page_config(page_title="SourceSight", layout="wide")

TIER_COLORS = {
    "Low": "#65C29A",
    "Watch": "#E2C66F",
    "Elevated": "#F0A15D",
    "High": "#F07878",
}
PROFILE_TITLES = {
    "TSM-COMPAL": "Notebook PC Manufacturing",
    "TSM-GARMIN": "GPS Device Manufacturing",
    "TSM-PEGAVISION": "Contact Lens Manufacturing",
    "TSM-CMC": "Vehicle Manufacturing",
    "TSM-AOT": "Optoelectronic Component Manufacturing",
    "TSM-DGI": "Electronics Manufacturing",
    "TSM-TSURUMI": "Water Pump Manufacturing",
}
FLOW_BLUE = "#607A96"
RISK_RED = "#C7666D"
COUNTRY_CENTROIDS = {
    "CN": (35.9, 104.2), "IN": (20.6, 78.9), "VN": (16.0, 106.0),
    "MY": (4.2, 102.0), "TH": (15.8, 101.0), "TW": (23.7, 120.96),
    "PH": (12.9, 121.8), "US": (37.1, -95.7), "HK": (22.3, 114.2),
    "FR": (46.2, 2.2), "JP": (36.2, 138.3), "KR": (36.4, 127.8), "CA": (56.1, -106.3),
}
TAIWAN_LOCALITIES = {
    "Pingzhen, Taoyuan": (24.945752, 121.218359),
    "Guishan, Taoyuan": (24.992517, 121.337767),
    "Hukou Township, Hsinchu County": (24.900599, 121.046839),
}
MAP_MARKER_OFFSETS = {
    "TSM-COMPAL": (-0.018, -0.018),
    "TSM-TSURUMI": (0.018, 0.018),
    "TSM-GARMIN": (0.018, -0.018),
    "TSM-PEGAVISION": (-0.018, 0.018),
}
REGION_CENTROIDS = {
    ("CN", "Xinjiang"): (42.0, 85.0),
    ("CN", "Ningxia"): (37.3, 106.2),
    ("CN", "Inner Mongolia"): (43.4, 112.0),
    ("CN", "Jiangsu"): (32.9, 119.5),
    ("IN", "Maharashtra"): (19.7, 75.7),
    ("IN", "Gujarat"): (22.3, 72.6),
    ("IN", "Tamil Nadu"): (11.1, 78.7),
    ("VN", "Dong Nai"): (11.1, 107.2),
    ("VN", "Binh Duong"): (11.2, 106.7),
    ("MY", "Selangor"): (3.1, 101.5),
    ("MY", "Penang"): (5.4, 100.3),
    ("TH", "Chonburi"): (13.3, 101.0),
    ("TH", "Rayong"): (12.7, 101.3),
    ("TH", "Trat"): (12.2, 102.5),
    ("TH", "Phuket"): (7.9, 98.3),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root {
    --ink: #f5f5f7;
    --muted: #d8d9df;
    --paper: #071A2B;
    --surface: #10263A;
    --line: #31516B;
    --forest: #9e5b68;
    --teal: #607a96;
    --copper: #c7666d;
}
.stApp, [data-testid="stAppViewContainer"] { background: var(--paper); color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; font-size: 1rem; }
[data-testid="stHeader"] { background: rgba(7,26,43,.97); }
[data-testid="stSidebar"] { background: #091D30; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: #f5f5f7; }
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-baseweb="popover"] * { color: #f5f5f7; }
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * { color: #111318 !important; }
[data-baseweb="select"] > div { background: #202027; border-color: #607a96; }
h1, h2, h3, h4, p, label, li { color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; letter-spacing: 0; }
h1 { font-size: 2.35rem; font-weight: 700; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] label { color: #F1F2F4; font-size: 1rem; line-height: 1.62; overflow-wrap: anywhere; }
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 { line-height: 1.35; overflow-wrap: anywhere; }
[data-testid="stMetric"] {
    background: var(--surface); border: 1px solid var(--line); border-top: 3px solid var(--teal);
  border-radius: 5px; padding: 14px 16px; min-height: 108px;
}
[data-testid="stMetricLabel"] { color: var(--muted); font-size: .92rem; line-height: 1.4; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: clamp(1.2rem, 2vw, 1.8rem); overflow-wrap: anywhere; }
[data-testid="stAlert"] { border-radius: 4px; background: #1b1718 !important; border: 1px solid #69545c; color: #f5f5f7; }
[data-testid="stAlert"] p { color: #F5F5F7 !important; font-size: .98rem; line-height: 1.55; }
[data-testid="stTabs"] button,
[data-testid="stTabs"] button p { color: #FFFFFF !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #FFFFFF !important; border-bottom-color: var(--copper); }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 4px; }
[data-testid="stMarkdownContainer"] a { color: #B9D3FF !important; text-decoration: underline; text-underline-offset: 2px; }
[data-testid="stCaptionContainer"] { color: #D2D4DA !important; font-size: .92rem; line-height: 1.5; }
[data-testid="stCaptionContainer"] p { color: #D2D4DA !important; font-size: .92rem; line-height: 1.5; overflow-wrap: anywhere; }
[data-testid="stSelectbox"] [data-baseweb="select"] { background: #202027; }
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"],
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] *,
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] small { color: #111318 !important; }
[data-testid="stFileUploader"] [data-testid="stWidgetLabel"],
[data-testid="stFileUploader"] [data-testid="stWidgetLabel"] * { color: #FFFFFF !important; }
[data-testid="stExpander"] { background: #15151a; border-color: var(--line); }
.stButton button, [data-testid="stDownloadButton"] button { background: #354c5c; color: #fff; border-color: #607a96; }
.eyebrow { color: var(--copper); font: 500 .76rem 'DM Mono', monospace; text-transform: uppercase; }
.brand-lockup { display: flex; align-items: center; gap: 12px; margin: 2px 0 18px; }
.brand-mark { width: 42px; height: 42px; flex: 0 0 42px; }
.brand-wordmark { color: #FFFFFF; font: 700 1.18rem 'DM Sans', 'Avenir Next', sans-serif; line-height: 1.1; }
.brand-kicker { color: #B9D3FF; font: 500 .72rem 'DM Mono', monospace; margin-top: 4px; }
.page-heading { color: #FFFFFF; font: 700 2rem 'DM Sans', 'Avenir Next', sans-serif; line-height: 1.2; margin: 0 0 7px; overflow-wrap: anywhere; }
.page-deck { color: #D8E2EE; font-size: 1rem; line-height: 1.55; margin: 0 0 14px; max-width: 850px; }
@media (max-width: 700px) {
    .block-container { padding: 3.5rem 1rem 2rem; }
    h1 { font-size: 1.8rem; }
    .brand-lockup { margin-bottom: 14px; }
    .brand-mark { width: 36px; height: 36px; flex-basis: 36px; }
    .brand-wordmark { font-size: 1.08rem; }
    .page-heading { font-size: 1.55rem; }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] label { font-size: .98rem; line-height: 1.58; }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p { font-size: .9rem; line-height: 1.48; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .55rem; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: calc(50% - .35rem) !important; min-width: calc(50% - .35rem) !important;
        flex: 1 1 calc(50% - .35rem) !important;
    }
  [data-testid="stMetric"] { min-height: 94px; padding: 10px 12px; }
  [data-testid="stMetricValue"] { font-size: 1.28rem; }
}
</style>
""", unsafe_allow_html=True)

def supply_network_chart(product, entities, assessment):
    """Build a directed upstream-to-product network with tier and route encoding."""
    incoming = {entity_id: [] for entity_id in assessment.suppliers}
    outgoing = {entity_id: [] for entity_id in assessment.suppliers}
    for edge in product.edges:
        incoming[edge.target].append(edge.source)
        outgoing[edge.source].append(edge.target)

    depth = {entity_id: 0 for entity_id in assessment.suppliers if not incoming[entity_id]}
    pending = set(assessment.suppliers) - set(depth)
    while pending:
        ready = [entity_id for entity_id in pending
                 if all(source in depth for source in incoming[entity_id])]
        if not ready:
            break
        for entity_id in ready:
            depth[entity_id] = max((depth[source] + 1 for source in incoming[entity_id]), default=0)
            pending.remove(entity_id)

    layers = {}
    for entity_id in assessment.suppliers:
        layers.setdefault(depth.get(entity_id, 0), []).append(entity_id)
    positions = {}
    max_depth = max(layers, default=0)
    for layer, entity_ids in layers.items():
        entity_ids.sort(key=lambda item: entities[item].name)
        for index, entity_id in enumerate(entity_ids):
            positions[entity_id] = {
                "x": 0.08 + (0.84 * layer / max_depth if max_depth else 0.42),
                "y": (index + 1) / (len(entity_ids) + 1),
            }

    path_edges = set(zip(assessment.risk_path, assessment.risk_path[1:]))
    edge_rows = []
    for edge in product.edges:
        source, target = positions[edge.source], positions[edge.target]
        upstream = entities[edge.source]
        edge_rows.append({
            "x": source["x"], "y": source["y"], "x2": target["x"], "y2": target["y"],
            "input": edge.input_name, "share": edge.share,
            "from_name": upstream.name, "to_name": entities[edge.target].name,
            "on_path": (edge.source, edge.target) in path_edges,
        })

    node_rows = []
    for entity_id, position in positions.items():
        entity, result = entities[entity_id], assessment.suppliers[entity_id]
        node_rows.append({
            **position, "entity_id": entity_id, "name": entity.name, "role": entity.role,
            "location": ", ".join(part for part in (entity.region, entity.country) if part),
            "tier": result.own_tier, "effective_tier": result.effective_tier,
            "score": result.composite_score, "path": entity_id in assessment.risk_path,
            "inherited": bool(result.inherited_tier),
            "label": entity_id,
        })

    base = alt.Chart(alt.Data(values=edge_rows)).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        x2="x2:Q", y2="y2:Q",
        tooltip=[alt.Tooltip("from_name:N", title="Supplier"), alt.Tooltip("to_name:N", title="Buyer"),
                 alt.Tooltip("input:N", title="Input"), alt.Tooltip("share:Q", title="Input share", format=".0%")],
    )
    links = base.mark_rule(strokeWidth=2).encode(
        color=alt.condition("datum.on_path", alt.value(RISK_RED), alt.value(FLOW_BLUE)),
        strokeDash=alt.condition("datum.on_path", alt.value([1, 0]), alt.value([5, 4])),
    )
    nodes = alt.Chart(alt.Data(values=node_rows))
    halos = nodes.transform_filter("datum.path").mark_circle(size=620, filled=False, stroke=RISK_RED, strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
    )
    points = nodes.mark_circle(size=360, stroke="#10263A", strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        color=alt.Color("tier:N", scale=alt.Scale(domain=list(TIER_COLORS), range=list(TIER_COLORS.values())),
                        legend=alt.Legend(title="Own risk tier", orient="top")),
        tooltip=[alt.Tooltip("name:N", title="Supplier"), alt.Tooltip("role:N", title="Role"),
                 alt.Tooltip("location:N", title="Location"), alt.Tooltip("tier:N", title="Own tier"),
                 alt.Tooltip("effective_tier:N", title="Effective tier"),
                 alt.Tooltip("score:Q", title="Evidence score", format=".2f")],
    )
    labels = nodes.mark_text(dy=23, font="DM Sans", fontSize=11, fontWeight=500, color="#f5f5f7").encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        text=alt.Text("label:N"),
    )
    chart = alt.layer(links, halos, points, labels).properties(
        height=max(360, 74 * max((len(items) for items in layers.values()), default=1)),
        padding={"left": 20, "right": 24, "top": 14, "bottom": 18},
    ).configure_view(stroke=None, fill="#10263A").configure(
        background="#071A2B", autosize={"type": "fit", "contains": "padding"},
    ).configure_axis(gridColor="#354c5c", labelColor="#c2c0c6", titleColor="#f5f5f7",
                     domainColor="#607a96").configure_legend(labelColor="#f5f5f7", titleColor="#f5f5f7")
    return chart


def geographic_supplier_points(entities, assessment):
    """Aggregate fictional suppliers at approximate region or country centroids."""
    groups = defaultdict(list)
    for entity_id, result in assessment.suppliers.items():
        entity = entities[entity_id]
        coordinate = REGION_CENTROIDS.get((entity.country, entity.region))
        coordinate = coordinate or COUNTRY_CENTROIDS.get(entity.country)
        if coordinate is None:
            continue
        groups[(entity.country, entity.region or "Country level")].append((entity, result))

    points = []
    for (country, region), suppliers in groups.items():
        highest_tier = max((result.own_tier for _, result in suppliers), key=TIER_ORDER.get)
        latitude, longitude = REGION_CENTROIDS.get((country, region)) or COUNTRY_CENTROIDS[country]
        hex_color = TIER_COLORS[highest_tier].lstrip("#")
        color = [int(hex_color[index:index + 2], 16) for index in (0, 2, 4)] + [225]
        points.append({
            "latitude": latitude, "longitude": longitude,
            "location": f"{region}, {country}" if region != "Country level" else f"Country level, {country}",
            "position": "Assessed supplier country-level location",
            "companies": "; ".join(entity.name for entity, _ in suppliers),
            "status": f"Highest own tier: {highest_tier}",
            "count": len(suppliers), "radius": 22000 + 10000 * min(len(suppliers) - 1, 4),
            "own_tier": highest_tier, "effective_tier": max(
                (result.effective_tier for _, result in suppliers), key=TIER_ORDER.get),
            "supplier_names": "<br/>".join(f"{entity.name} ({entity.id})" for entity, _ in suppliers),
            "color": color,
        })
    return points


def geographic_supply_links(product, entities, assessment):
    """Create map arcs for each supplier-to-buyer input relationship."""
    risk_edges = set(zip(assessment.risk_path, assessment.risk_path[1:]))
    links = []
    for edge in product.edges:
        source_entity = entities[edge.source]
        target_entity = entities[edge.target]
        source_position = REGION_CENTROIDS.get((source_entity.country, source_entity.region))
        source_position = source_position or COUNTRY_CENTROIDS.get(source_entity.country)
        target_position = REGION_CENTROIDS.get((target_entity.country, target_entity.region))
        target_position = target_position or COUNTRY_CENTROIDS.get(target_entity.country)
        if source_position is None or target_position is None:
            continue

        on_risk_path = (edge.source, edge.target) in risk_edges
        color = RISK_RED if on_risk_path else FLOW_BLUE
        color_rgb = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
        links.append({
            "source_position": [source_position[1], source_position[0]],
            "target_position": [target_position[1], target_position[0]],
            "source_name": source_entity.name,
            "target_name": target_entity.name,
            "input": edge.input_name,
            "share": edge.share,
            "share_label": f"{edge.share:.0%}",
            "on_risk_path": on_risk_path,
            "color": color_rgb,
            "width": 4 if on_risk_path else 2,
        })
    return links


def investigation_map_data(source):
    """Prepare selectable report entities; affiliate scores are linked exposure, not own findings."""
    nodes, links, detail_by_id = [], [], {}
    company_by_name = {company["name"]: company for company in COMPANIES}
    manufacturer_ids = {company["id"] for company in COMPANIES if not company.get("agency_profile")}
    assessments = {company_id: assess_product(source, company_id) for company_id in manufacturer_ids}

    def own_score_for_report_entity(entity_id):
        signals = detect_signals(entity_id, source, mapped_inputs=False)
        pillar_scores = {
            pillar: noisy_or([signal.strength for signal in signals if signal.pillar == pillar])
            for pillar in PILLARS
        }
        composite = noisy_or([pillar_scores[pillar] * PILLAR_WEIGHTS[pillar] for pillar in PILLARS])
        convergence = sum(pillar_scores[pillar] >= 0.4 for pillar in PILLARS if pillar != "transparency")
        tier, _ = _tier(False, convergence, composite)
        return composite, tier

    def add_node(node_id, name, node_type, country, locality, position, own_score, linked_score,
                 tier, color, issue, source_note, investigated):
        lat, lon = position
        tooltip_issue = issue.replace("$", "USD ")
        if len(tooltip_issue) > 180:
            tooltip_issue = tooltip_issue[:177].rsplit(" ", 1)[0] + "..."
        node = {
            "node_id": node_id, "name": name, "node_type": node_type, "country": country,
            "locality": locality, "latitude": lat, "longitude": lon, "own_score": own_score,
            "linked_score": linked_score, "tier": tier, "color": color,
            "issue": issue.replace("$", "USD "), "tooltip_issue": tooltip_issue,
            "source_note": source_note,
            "investigated": investigated,
        }
        if node_type == "Report-contacted possible buyer market":
            node["symbol"] = "◆"
            marker_radius = 0.85
            longitude_radius = marker_radius / max(0.35, abs(math.cos(math.radians(lat))))
            node["marker_polygon"] = [
                [lon, lat + marker_radius],
                [lon + longitude_radius, lat],
                [lon, lat - marker_radius],
                [lon - longitude_radius, lat],
            ]
        nodes.append(node)
        detail_by_id[node_id] = {
            "name": name, "node_type": node_type, "country": country, "locality": locality,
            "own_score": own_score, "linked_score": linked_score, "tier": tier,
            "issue": issue, "source_note": source_note, "investigated": investigated,
        }

    origin_companies = defaultdict(list)
    for company in COMPANIES:
        if company.get("agency_profile"):
            continue
        assessment = assessments[company["id"]]
        result = assessment.suppliers[company["id"]]
        position = TAIWAN_LOCALITIES.get(company["facility_context"], COUNTRY_CENTROIDS["TW"])
        if company["id"] in MAP_MARKER_OFFSETS:
            latitude_offset, longitude_offset = MAP_MARKER_OFFSETS[company["id"]]
            position = position[0] + latitude_offset, position[1] + longitude_offset
        locality = company["facility_context"]
        if company["id"] in MAP_MARKER_OFFSETS:
            locality += " (visual pin offset within district for separate selection)"
        if position == COUNTRY_CENTROIDS["TW"]:
            locality += " (country-centroid point; exact site not geocoded)"
        else:
            locality += " (OSM township/district centroid; not factory coordinates)"
        score = round(result.composite_score * 100, 1)
        add_node(
            company["id"], company["name"], "Investigated manufacturer", "TW", locality,
            position, score, score, result.own_tier,
            [240, 161, 93, 240],
            f"{company['interviews']} interviews ({company['workers']}); reported fees {company['fees']}. "
            f"{company['borrowed']}. {company['details']}",
            "Transparentem case material supplied by the user; not independently verified by SourceSight.",
            True,
        )
        origin = company.get("worker_origin_country")
        if origin in COUNTRY_CENTROIDS:
            origin_lat, origin_lon = COUNTRY_CENTROIDS[origin]
            origin_companies[origin].append(company["name"])
            links.append({
                "source_position": [origin_lon, origin_lat],
                "target_position": [position[1], position[0]],
                "source_name": origin, "target_name": company["name"],
                "relationship": "Report-described worker recruitment corridor; not a goods route",
                "color": [114, 175, 209, 145], "width": 2,
            })

        for relationship in report_relationships(company["id"]):
            affiliate_country = relationship["country"]
            affiliate_position = COUNTRY_CENTROIDS[affiliate_country]
            recruiter_result = own_score_for_report_entity(relationship["id"]) if relationship["is_investigated"] else None
            recruiter_own_score, recruiter_tier = recruiter_result if recruiter_result else (None, None)
            linked_score = round(
                (recruiter_own_score * 100 if recruiter_own_score is not None
                 else score * relationship["association_weight"]), 1
            )
            if recruiter_own_score is not None:
                recruiter_score_display = round(recruiter_own_score * 100, 1)
                affiliate_color_hex = TIER_COLORS[recruiter_tier].lstrip("#")
                affiliate_color = [int(affiliate_color_hex[index:index + 2], 16) for index in (0, 2, 4)] + [235]
                tier_label = recruiter_tier
                kind = "Investigated recruiter"
            else:
                recruiter_score_display = None
                affiliate_color = [226, 198, 111, 235]
                tier_label = f"Linked exposure · {linked_score:.1f}/100"
                kind = "Report-named affiliate"
            add_node(
                relationship["id"], relationship["name"], kind, affiliate_country,
                relationship["locality"], affiliate_position, recruiter_score_display, linked_score,
                tier_label, affiliate_color,
                relationship["basis"],
                "Association score = investigated company score × report-described link weight. "
                "It is not an independent allegation, confirmed supplier edge, or separate company finding.",
                relationship["is_investigated"],
            )
            links.append({
                "source_position": [position[1], position[0]],
                "target_position": [affiliate_position[1], affiliate_position[0]],
                "source_name": company["name"], "target_name": relationship["name"],
                "relationship": relationship["relationship"],
                "color": [226, 198, 111, 160], "width": 2,
            })

    contacted_buyers_by_country = defaultdict(list)
    for company in COMPANIES:
        if company.get("agency_profile"):
            continue
        for buyer in possible_buyer_relationships(company):
            country = buyer.get("country")
            if country in COUNTRY_CENTROIDS:
                contacted_buyers_by_country[country].append({
                    "company": buyer["company"], "manufacturer": company["name"],
                    "status": buyer["status"],
                })

    for country, contacts in sorted(contacted_buyers_by_country.items()):
        latitude, longitude = COUNTRY_CENTROIDS[country]
        buyer_names = sorted({contact["company"] for contact in contacts})
        manufacturers = sorted({contact["manufacturer"] for contact in contacts})
        node_id = f"CONTACTED-BUYERS-{country}"
        add_node(
            node_id, f"Contacted buyers · {country}", "Report-contacted possible buyer market",
            country, "Buyer country from brief; country centroid, not headquarters or shipment destination",
            (latitude, longitude), None, None, "Possible connections; not scored", None,
            f"Report-contacted possible or former buyers in this country: {', '.join(buyer_names)}. "
            f"Linked manufacturers: {', '.join(manufacturers)}. These are unconfirmed buyer leads, not confirmed sales or shipments.",
            "Buyer names and reported countries are from the user-supplied Transparentem case material; point is a country centroid.",
            False,
        )
        for manufacturer in manufacturers:
            manufacturer_record = next(item for item in COMPANIES if item["name"] == manufacturer)
            position = TAIWAN_LOCALITIES.get(manufacturer_record["facility_context"], COUNTRY_CENTROIDS["TW"])
            if manufacturer_record["id"] in MAP_MARKER_OFFSETS:
                latitude_offset, longitude_offset = MAP_MARKER_OFFSETS[manufacturer_record["id"]]
                position = position[0] + latitude_offset, position[1] + longitude_offset
            links.append({
                "source_position": [position[1], position[0]],
                "target_position": [longitude, latitude],
                "source_name": manufacturer, "target_name": f"Contacted buyers · {country}",
                "relationship": "Possible buyer connection named in the report; unconfirmed",
                "color": [96, 122, 150, 145], "width": 2,
            })

    for country, companies in sorted(origin_companies.items()):
        latitude, longitude = COUNTRY_CENTROIDS[country]
        origin_id = f"WORKER-HOME-{country}"
        add_node(
            origin_id, f"Worker home country: {country}", "Reported worker-origin country",
            country, "Country-centroid context; worker home localities not supplied",
            (latitude, longitude), None, None, "Context only", [114, 175, 209, 235],
            f"The brief reports interviewed migrant workers originating from {country}. "
            f"Related investigated manufacturers: {', '.join(sorted(companies))}. "
            "This point describes worker migration origins, not a goods supplier or a finding about the country.",
            "Transparentem case material supplied by the user; exact worker home locations are not provided.",
            False,
        )

    return nodes, links, detail_by_id, assessments


def _selected_map_node(chart_state):
    try:
        objects = chart_state.selection.get("objects", {})
        for selected_objects in objects.values():
            if selected_objects:
                return selected_objects[0].get("node_id")
    except (AttributeError, TypeError):
        return None
    return None


def render_investigation_legend():
    entries = (
        ("#F0A15D", "●", "Investigated manufacturer (orange)", "marker"),
        ("#E2C66F", "●", "Report-linked recruiter / affiliate", "marker"),
        ("#72AFD1", "●", "Worker-origin country", "marker"),
        ("#607A96", "◆", "Contacted buyer; possible connection", "marker"),
        ("#E2C66F", "", "Report-stated recruiter / affiliate link", "line"),
        ("#72AFD1", "", "Worker recruitment corridor", "line"),
        ("#607A96", "", "Possible buyer link; unconfirmed", "line"),
    )
    legend_items = []
    for color, symbol, label, kind in entries:
        glyph = (
            f'<span style="color:{color};font-size:17px;line-height:1">{symbol}</span>'
            if kind == "marker" else
            f'<span style="width:23px;border-top:2px solid {color};display:inline-block"></span>'
        )
        legend_items.append(
            f'<span style="display:inline-flex;align-items:center;gap:7px;margin:0 16px 7px 0;color:#c2c0c6">'
            f'{glyph}{label}</span>'
        )
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;align-items:center;margin:4px 0 8px">'
        + "".join(legend_items) + "</div>", unsafe_allow_html=True,
    )


def render_case_list_screen():
    st.markdown("#### Open forced-labor list screening")
    st.write("Manually screen manufacturers and report-named buyers against public OpenSanctions snapshots of the U.S. DHS UFLPA Entity List, U.S. CBP forced-labor orders, and C4ADS Long Shadows (Xinjiang). This is list exposure context, not a supplier graph or a screen for Taiwan recruitment fees.")
    st.warning("Sayari and Tradeverifyd adapters and credentials are not present in this checkout. No paid-provider requests are made.")
    if st.button("Run public list screening", key="run_case_list_screen"):
        with st.spinner("Downloading or reading cached list snapshots and matching exact names/aliases..."):
            try:
                st.session_state["case_list_screen"] = screen_case_companies()
                st.session_state.pop("case_list_screen_error", None)
            except Exception as exc:
                st.session_state["case_list_screen_error"] = f"{type(exc).__name__}: {exc}"
    if st.session_state.get("case_list_screen_error"):
        st.error("The public list screen did not complete: " + st.session_state["case_list_screen_error"])
    screen = st.session_state.get("case_list_screen")
    if screen:
        st.warning(screen["disclaimer"])
        st.dataframe([{
            "Company": name,
            "UFLPA": result["datasets"]["us_dhs_uflpa"],
            "CBP forced labor": result["datasets"]["us_cbp_forced_labor"],
            "C4ADS Xinjiang": result["datasets"]["c4ads_xinjiang"],
            "Exact candidates": "; ".join(
                f"{match['listed_name']} ({match['dataset']})" for match in result["matches"]
            ) or "None",
        } for name, result in screen["companies"].items()], width="stretch", hide_index=True)
        st.caption("Snapshots: " + " · ".join(
            f"{item['name']} retrieved {item['retrieved_at']}" for item in screen["snapshots"]
        ))
        st.caption("OpenSanctions data is CC BY-NC 4.0; commercial use requires a separate data license. Exact-name screening can miss aliases and does not verify identity.")


def render_case_study():
    st.markdown('<div class="eyebrow">Featured investigation / report-attributed case study</div>', unsafe_allow_html=True)
    st.title("Debt Before Day One")
    st.caption("Transparentem · Report dated October 2026 · Fieldwork November 2025-June 2026")
    st.warning(
        "Report-attributed allegations; not independently verified by SourceSight. "
        "Indicators are not findings that forced labor occurred."
    )
    st.markdown(
        f"Source: [{REPORT['publisher']} report]({REPORT['url']}). "
        f"This case uses user-supplied report details; SourceSight could not extract or independently verify the PDF. "
        f"The report describes {REPORT['interviews']} interviews across {REPORT['manufacturers_interviewed']} Taiwan manufacturers."
    )

    source = CaseStudySource()
    products = {product.id: product for product in source.products()}
    entities = source.entities()
    labels = {company["id"]: company["name"] for company in COMPANIES}
    selected_id = st.selectbox("Report profile", tuple(labels), format_func=labels.get)
    company = company_by_id(selected_id)
    assessment = assess_product(source, selected_id)
    result = assessment.suppliers[selected_id]
    entity = entities[selected_id]

    st.subheader(company["name"])
    st.caption(f"{entity.role} · Taiwan · Report interviews: {company['interviews']} · No facility address supplied")
    metrics = st.columns(4)
    metrics[0].metric("Illustrative own tier", result.own_tier)
    metrics[1].metric("Reported fee range", company["fees"])
    metrics[2].metric("Reported interviews", company["interviews"])
    metrics[3].metric("Evidence confidence", f"{result.confidence} ({result.confidence_score:.2f})")
    st.info("Enforcement and sanctions-list status: unknown. No live list lookup has been run.")
    st.markdown(f"**Debt and recruitment account:** {company['borrowed']}. {company['details']}")
    st.markdown(f"**Company / report response:** {company['response']}")
    if company.get("agency_profile"):
        st.caption("The report does not name this recruitment agency. It is kept separate from Garmin and is not assigned an employer identity or any unsupplied allegation.")

    assessment_tab, buyers_tab, verify_tab, requests_tab = st.tabs(
        ["Evidence assessment", "Possible buyer connections", "To verify", "Data requests"])
    with assessment_tab:
        st.markdown("#### Reported ILO indicators")
        st.write(", ".join(item.replace("_", " ").title() for item in result.ilo_indicators)
                 if result.ilo_indicators else "No indicators tagged in the supplied report summary.")
        st.markdown("#### Calculated assessment")
        score_a, score_b = st.columns(2)
        score_a.metric("Composite score", f"{result.composite_score:.3f}")
        score_b.metric("Converging pillars", f"{result.convergence} / 4")
        st.write(result.tier_reason)
        st.caption(
            "Illustrative original-model output, not a legal or investigative determination. "
            "The 0.45 Taiwan sector overlay and worker indicators both derive from this same report. "
            "The original model counts thresholded pillars without source-dependence adjustment, so the two pillars are not independent corroboration. "
            "No enforcement/list match or confirmed supply edge is modeled."
        )
        st.markdown("#### Evidence and provenance")
        st.dataframe([{
            "Claim": signal.claim_kind, "Pillar": signal.pillar.title(), "Signal": signal.title,
            "Strength": f"{signal.strength:.2f}", "Detail": signal.detail,
            "Source IDs": ", ".join(signal.source_ids),
        } for signal in result.signals], width="stretch", hide_index=True)
        st.caption("FACT means the report made a documented claim; it does not mean SourceSight established the underlying allegation as true. Non-response does not increase reliability.")
        st.markdown("#### Geographic context")
        st.caption("Report material supplied for this case identifies Taiwan, but no administrative region or facility address. The marker is an approximate Taiwan-wide centroid, not a facility location.")
        map_data = [{"latitude": 23.7, "longitude": 120.96, "label": "Taiwan · approximate country-level centroid"}]
        marker = pdk.Layer(
            "ScatterplotLayer", data=map_data, get_position="[longitude, latitude]",
            get_fill_color=[240, 161, 93, 220], get_radius=45000,
            radius_min_pixels=12, radius_max_pixels=20, pickable=True,
        )
        st.pydeck_chart(pdk.Deck(
            layers=[marker], initial_view_state=pdk.ViewState(latitude=23.7, longitude=120.96, zoom=5.2),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"text": "{label}"},
        ), use_container_width=True, height=330)

    with buyers_tab:
        st.markdown("#### Reported possible connections")
        st.warning("These report-named links are not confirmed customers, contracts, or supply-chain edges. The direct buyer position is Tier 1 downstream only if the relationship is verified; no link propagates risk in SourceSight.")
        buyer_relationships = possible_buyer_relationships(company)
        if buyer_relationships:
            rows = [{"x": 0, "y": index, "x2": 1, "y2": index,
                     "supplier": company["name"], "buyer": item["company"],
                     "status": item["status"], "buyer_label": item["company"]}
                    for index, item in enumerate(buyer_relationships)]
            chart = alt.Chart(alt.Data(values=rows)).encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
                y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.7, max(1, len(rows) - 0.3)]), axis=None),
                x2="x2:Q", y2="y2:Q",
                tooltip=[alt.Tooltip("supplier:N"), alt.Tooltip("buyer:N"), alt.Tooltip("status:N")],
            )
            links = chart.mark_rule(stroke="#E2C66F", strokeWidth=2, strokeDash=[6, 5])
            points = alt.Chart(alt.Data(values=rows)).mark_circle(size=100, color="#F0A15D").encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
                y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.7, max(1, len(rows) - 0.3)]), axis=None),
            )
            left_labels = alt.Chart(alt.Data(values=rows)).mark_text(align="right", dx=-12, color="#F5F5F7", fontSize=11).encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
                y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.7, max(1, len(rows) - 0.3)]), axis=None),
                text="supplier:N",
            )
            right_labels = alt.Chart(alt.Data(values=rows)).mark_text(align="left", dx=12, color="#F5F5F7", fontSize=11).encode(
                x=alt.X("x2:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
                y=alt.Y("y2:Q", scale=alt.Scale(domain=[-0.7, max(1, len(rows) - 0.3)]), axis=None),
                text="buyer_label:N",
            )
            st.altair_chart(alt.layer(links, points, left_labels, right_labels).properties(
                height=max(190, 42 * len(rows))).configure_view(stroke=None, fill="#10263A").configure(
                    background="#071A2B"), use_container_width=True, theme=None)
            st.dataframe([{"Company": item["company"], "Supply-chain position": item["tier_position"],
                           "Report wording status": item["status"]} for item in buyer_relationships],
                         width="stretch", hide_index=True)
        else:
            st.info("No buyer connection is supplied for this unnamed agency profile.")
        if company["ownership_to_verify"]:
            st.markdown("#### Separate ownership leads")
            st.caption("Ownership is a corporate-control relationship, not a supplier tier or product-flow edge. These claims still require independent verification.")
            for lead in company["ownership_to_verify"]:
                st.markdown(f"- {lead}")

    with verify_tab:
        checks = [
            "Obtain the original report and source-level documentation; verify dates, sample descriptions, and fee amounts.",
            "Request worker-safe, independently documented recruitment-fee and repayment records, including former workers.",
            "Confirm current company remediation status and distinguish reported commitments from completed reimbursement.",
            "Run current, identity-reviewed sanctions and enforcement list checks; status is unknown until then.",
            "Verify whether any named possible buyer relationship is current, direct, and product-specific before mapping an edge.",
        ]
        if company["ownership_to_verify"]:
            checks.append("Verify report-attributed ownership claims against current corporate filings: " + "; ".join(company["ownership_to_verify"]) + ".")
        if company.get("agency_profile"):
            checks.append("Identify the recruitment agency only through safe, lawful, independently sourced records; the report does not name it.")
        for check in checks:
            st.markdown(f"- {check}")
        st.caption("Requests are verification leads, not established facts. Company non-response is not evidence that a claim is true.")

    with requests_tab:
        render_case_list_screen()
        st.markdown("#### Other free-source requests")
        st.write("No network requests run when this app loads. After reviewing source terms, run the bounded CLI manually from the repository:")
        st.code("python -m sourcesight.data_requests --source dol_goods\npython -m sourcesight.data_requests --source opensanctions", language="bash")
        st.write("The existing runner uses HTTPS allowlisted endpoints, a 20-second timeout, a 20 MB response limit, and a 24-hour local cache. It requests the DOL 2024 goods-list XLSX and OpenSanctions OFAC and U.N. Security Council CSV datasets. Results are saved under `.cache/source_requests/` with source attribution.")
        st.markdown("#### Paid providers")
        st.warning("Sayari and Tradeverifyd adapters and credentials are not present in this checkout, so no paid queries can be run. The supplied request plan estimates about 28 Sayari and 21 Tradeverifyd calls; pricing was not provided, so no cost estimate can be responsibly stated. Do not run paid queries without credentials, an approved budget, and an explicit operator action.")
        st.caption("No API keys are collected, displayed, logged, or stored by this case-study view.")


@st.cache_resource
def load_source():
    return CaseStudySource()


st.markdown("""
<div class="brand-lockup">
    <svg class="brand-mark" viewBox="0 0 48 48" role="img" aria-label="SourceSight mark">
        <path d="M5 24c5.2-8.4 11.5-12.6 19-12.6S37.8 15.6 43 24c-5.2 8.4-11.5 12.6-19 12.6S10.2 32.4 5 24Z" fill="none" stroke="#B9D3FF" stroke-width="2.5"/>
        <circle cx="24" cy="24" r="6.5" fill="#F0A15D"/>
        <path d="M24 17.5V8M18.4 27.2l-7 5M29.6 27.2l7 5" fill="none" stroke="#65C29A" stroke-width="2.2" stroke-linecap="round"/>
        <circle cx="24" cy="7" r="2.5" fill="#65C29A"/>
        <circle cx="10" cy="33" r="2.5" fill="#65C29A"/>
        <circle cx="38" cy="33" r="2.5" fill="#65C29A"/>
    </svg>
    <div>
        <div class="brand-wordmark">SourceSight</div>
        <div class="brand-kicker">SUPPLY-CHAIN HUMAN RIGHTS MONITOR</div>
    </div>
</div>
<div class="page-heading">Recruitment Debt in Taiwan's Supply Chains</div>
<div class="page-deck">Explore worker-reported recruitment fees, investigated manufacturers, and report-named supply-chain connections.</div>
""", unsafe_allow_html=True)
st.warning(
    "REPORT-ATTRIBUTED CASE MATERIAL. The report details were supplied by the user and have not been independently verified by SourceSight. "
    "Possible buyers are unconfirmed and are not treated as supply-chain edges. Scores are review aids, not findings that forced labor occurred."
)
st.caption(f"Source: [{REPORT['publisher']}, {REPORT['title']}]({REPORT['url']}) · October 2026 · 24 interviews across 7 manufacturers")

try:
    source = load_source()
    products = source.products()
    product_by_name = {
        f"{product.brand} | {PROFILE_TITLES.get(product.id, product.name + ' Manufacturing')}": product
        for product in products
    }
    with st.sidebar:
        st.header("Assessment")
        selected_label = st.selectbox("Product", tuple(product_by_name))
        st.caption("Seven report-backed product profiles. Buyer mentions remain possible/unconfirmed; no live list lookup has run.")
        st.divider()
        st.subheader("Agentic report analysis")
        uploaded_brief = st.file_uploader("Upload investigation brief (PDF)", type=["pdf"], key="additional_brief_pdf")
        if st.button("Generate map from report", key="pdf_analysis_preview",
                     help="Prototype control only; the selected PDF is not processed."):
            st.info("Report-to-map generation is a prototype only. The PDF was not read and no map or assessment was created.")
        if uploaded_brief is not None:
            st.caption(f"Selected file: {uploaded_brief.name}. It is not analyzed or included in scoring.")
        else:
            st.caption("PDF-to-map analysis is not implemented; this control is a UI preview only.")
    product = product_by_name[selected_label]
    assessment = assess_product(source, product.id)
    entities = source.entities()
except Exception:
    st.error("The assessment could not be loaded. Check the report data and try again.")
    st.stop()

st.subheader(f"{product.brand} | {PROFILE_TITLES.get(product.id, product.name + ' Manufacturing')}")
st.write(product.summary)
metric_tier, metric_own, metric_source, metric_confidence = st.columns(4)
metric_tier.metric("Product effective tier", assessment.effective_tier)
metric_own.metric("Root entity own tier", assessment.own_tier)
metric_source.metric("Highest-risk source", entities[assessment.risk_source_id].name if assessment.risk_source_id else "None identified")
root_result = assessment.suppliers[product.root_entity_id]
metric_confidence.metric("Root evidence confidence", f"{root_result.confidence} ({root_result.confidence_score:.2f})")
if assessment.risk_path:
    st.info("Risk route: " + " -> ".join(entities[entity_id].name for entity_id in assessment.risk_path))
else:
    st.info("No non-Low own-risk source is present on the mapped product path in the available fixture data.")

geo_tab, map_tab, evidence_tab, scoring_tab = st.tabs(
    ["Geographic view", "Supply map", "Supplier evidence", "How scoring works"],
)

with map_tab:
    st.markdown("#### Supplier network")
    st.caption("Raw inputs flow left to finished product. Node labels are supplier IDs; hover for full details. Color shows own tier; coral rings and links mark the product's highest-risk route.")
    risk_edges = set(zip(assessment.risk_path, assessment.risk_path[1:]))
    if product.edges:
        st.altair_chart(supply_network_chart(product, entities, assessment), use_container_width=True, theme=None)
    else:
        st.info("No confirmed supplier-input edges are supplied for this reported product. Possible buyers are shown in the product summary only; they are not treated as confirmed customers or propagated risk.")

    report_links = report_relationships(product.root_entity_id)
    st.markdown("#### Company affiliations and report-linked markets")
    st.caption("Gold arcs are recruiter/corporate-affiliation claims from the brief. Blue arcs are report-named possible or former buyers, not confirmed customer or product-supply relationships.")
    all_map_nodes, all_map_arcs, _, _ = investigation_map_data(source)
    root_node = next(node for node in all_map_nodes if node["node_id"] == product.root_entity_id)
    affiliation_nodes = [node for node in all_map_nodes
                         if node["node_id"] in {item["id"] for item in report_links}]
    buyer_relationships = possible_buyer_relationships(company_by_id(product.root_entity_id))
    buyer_markets = {}
    for buyer in buyer_relationships:
        country = buyer["country"]
        if not country or country not in COUNTRY_CENTROIDS:
            continue
        market = buyer_markets.setdefault(country, {
            "country": country, "latitude": COUNTRY_CENTROIDS[country][0],
            "longitude": COUNTRY_CENTROIDS[country][1], "companies": [],
            "node_id": f"POSSIBLE-BUYER-MARKET-{country}",
            "name": f"Possible buyer market · {country}",
            "node_type": "Report-named buyer market; unconfirmed",
            "locality": "Country-centroid context, not buyer headquarters",
            "own_score": None, "linked_score": None, "tier": "Unconfirmed lead",
            "color": [96, 122, 150, 220],
        })
        market["companies"].append(buyer["company"])

    supply_map_nodes = [root_node, *affiliation_nodes, *buyer_markets.values()]
    supply_map_arcs = [arc for arc in all_map_arcs if arc["source_name"] == product.brand]
    for country, market in buyer_markets.items():
        supply_map_arcs.append({
            "source_position": [root_node["longitude"], root_node["latitude"]],
            "target_position": [market["longitude"], market["latitude"]],
            "source_name": product.brand, "target_name": market["name"],
            "relationship": "Possible buyer(s) named in the report; unconfirmed",
            "color": [96, 122, 150, 155], "width": 2,
        })
    if supply_map_arcs:
        affiliation_arc_data = [arc for arc in supply_map_arcs
                                if any(item["name"] == arc["target_name"] for item in report_links)]
        buyer_arc_data = [arc for arc in supply_map_arcs if arc not in affiliation_arc_data]
        map_layers = []
        if affiliation_arc_data:
            map_layers.append(pdk.Layer(
                "ArcLayer", data=affiliation_arc_data, id="reported-affiliations",
                get_source_position="source_position", get_target_position="target_position",
                get_source_color=[226, 198, 111, 190], get_target_color=[226, 198, 111, 190],
                get_width="width", width_min_pixels=1, width_max_pixels=4,
                great_circle=True, pickable=True, auto_highlight=True,
            ))
        if buyer_arc_data:
            map_layers.append(pdk.Layer(
                "ArcLayer", data=buyer_arc_data, id="possible-buyer-links",
                get_source_position="source_position", get_target_position="target_position",
                get_source_color="color", get_target_color="color", get_width="width",
                width_min_pixels=1, width_max_pixels=3, great_circle=True,
                pickable=True, auto_highlight=True,
            ))
        map_layers.append(pdk.Layer(
            "ScatterplotLayer", data=supply_map_nodes, id="supply-map-affiliated-companies",
            get_position="[longitude, latitude]", get_fill_color="color",
            get_line_color=[245, 245, 247, 220], get_radius=38000,
            radius_min_pixels=8, radius_max_pixels=20, stroked=True, pickable=True,
            auto_highlight=True,
        ))
        st.pydeck_chart(pdk.Deck(
            layers=map_layers,
            initial_view_state=pdk.ViewState(latitude=28, longitude=145, zoom=0.5, pitch=0, bearing=0),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"html": "<b>{name}</b><br/>{node_type}<br/>{locality}, {country}<br/>Own score: {own_score}<br/>Linked exposure: {linked_score}<br/>{tier}",
                     "style": {"backgroundColor": "#182320", "color": "#e8eee9", "border": "1px solid #52635a"}},
        ), use_container_width=True, height=390, key=f"supply_map_affiliates_{product.id}")

    st.markdown("#### Report-linked companies and locations")
    affiliate_score_by_id = {node["node_id"]: node for node in affiliation_nodes}
    relationship_rows = [{
        "Company": product.brand,
        "Connection": "Investigated manufacturer in the Transparentem brief",
        "Report location": f"{root_node['locality']}, {root_node['country']}",
        "Location precision": "Township/district centroid or country-level context",
        "Report status": "Investigated in the supplied brief",
        "Exposure": f"{root_node['linked_score']:.1f}/100",
    }]
    for relationship in report_links:
        node = affiliate_score_by_id[relationship["id"]]
        relationship_rows.append({
            "Company": relationship["name"], "Connection": relationship["relationship"],
            "Report location": f"{relationship['locality']}, {relationship['country']}",
            "Location precision": "Country-centroid context; headquarters/facility not confirmed",
            "Report status": "Investigated in report" if relationship["is_investigated"]
            else "Affiliation claim; independent confirmation pending",
            "Exposure": f"Own {node['own_score']:.1f}/100" if node["own_score"] is not None
            else f"Linked only {node['linked_score']:.1f}/100",
        })
    for buyer in buyer_relationships:
        relationship_rows.append({
            "Company": buyer["company"],
            "Connection": "Possible downstream buyer named in the report",
            "Report location": f"Country-level market context, {buyer['country'] or 'unknown'}",
            "Location precision": "Not a verified buyer headquarters or shipment destination",
            "Report status": buyer["status"],
            "Exposure": "Not scored; link is unconfirmed",
        })
    st.dataframe(relationship_rows, width="stretch", hide_index=True)
    st.caption("Only the Taiwan manufacturer/recruiter evidence is scored as investigated. Affiliate exposure is a prioritization link, not evidence that the affiliate committed a violation. Buyer references are separate unconfirmed leads and are not supply-chain edges.")

    tier_counts = {tier: sum(result.own_tier == tier for result in assessment.suppliers.values())
                   for tier in TIER_COLORS}
    distribution = [{"Tier": tier, "Suppliers": count} for tier, count in tier_counts.items() if count]
    if distribution:
        st.markdown("#### Supplier exposure by tier")
        tier_chart = alt.Chart(alt.Data(values=distribution)).mark_bar(size=24, cornerRadiusEnd=3).encode(
            x=alt.X("Suppliers:Q", title="Suppliers", scale=alt.Scale(domain=[0, max(tier_counts.values()) + 1]),
                     axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Tier:N", title=None, sort=["High", "Elevated", "Watch", "Low"]),
            color=alt.Color("Tier:N", scale=alt.Scale(domain=list(TIER_COLORS), range=list(TIER_COLORS.values())),
                            legend=None),
            tooltip=[alt.Tooltip("Tier:N"), alt.Tooltip("Suppliers:Q")],
        ).properties(height=125).configure_view(stroke=None, fill="#10263A").configure(
            background="#071A2B").configure_axis(
                gridColor="#354c5c", labelColor="#c2c0c6", titleColor="#f5f5f7", domainColor="#607a96")
        st.altair_chart(tier_chart, use_container_width=True, theme=None)

    with st.expander("Inspect exact supplier routes"):
        st.caption("Exact source, buyer, input, and share for each mapped connection.")
        edge_rows = []
        for edge in product.edges:
            upstream, buyer = entities[edge.source], entities[edge.target]
            upstream_result, buyer_result = assessment.suppliers[edge.source], assessment.suppliers[edge.target]
            edge_rows.append({
                "Route": "Highlighted risk path" if (edge.source, edge.target) in risk_edges else "Mapped",
                "Upstream supplier": f"{upstream.name} ({upstream.id})",
                "Role / country": f"{upstream.role} / {upstream.country}",
                "Input": edge.input_name,
                "Input share": f"{edge.share:.0%}",
                "Supplier own tier": upstream_result.own_tier,
                "Buyer own tier": buyer_result.own_tier,
            })
        st.dataframe(edge_rows, width="stretch", hide_index=True)
    if product.edges:
        st.caption("Edges run upstream to downstream. Share scales inherited score, not tier; no share is exempt.")

with geo_tab:
    st.markdown("#### Supplier geography")
    map_nodes, relationship_arcs, detail_by_id, company_assessments = investigation_map_data(source)
    render_investigation_legend()
    buyer_map_nodes = [node for node in map_nodes if node["node_type"] == "Report-contacted possible buyer market"]
    company_map_nodes = [node for node in map_nodes if node["node_type"] != "Report-contacted possible buyer market"]
    node_layer = pdk.Layer(
        "ScatterplotLayer", data=company_map_nodes, id="investigation-entities",
        get_position="[longitude, latitude]", get_fill_color="color",
        get_line_color=[245, 245, 247, 230], get_radius=42000,
        radius_min_pixels=9, radius_max_pixels=22, line_width_min_pixels=1,
        stroked=True, pickable=True, auto_highlight=True,
    )
    buyer_symbol_layer = pdk.Layer(
        "PolygonLayer", data=buyer_map_nodes, id="investigation-contacted-buyers",
        get_polygon="marker_polygon", get_fill_color=[96, 122, 150, 255],
        get_line_color=[245, 245, 247, 255], line_width_min_pixels=2,
        stroked=True, filled=True, extruded=False, pickable=True, auto_highlight=True,
    )
    arc_layer = pdk.Layer(
        "ArcLayer", data=relationship_arcs, id="investigation-relationships",
        get_source_position="source_position", get_target_position="target_position",
        get_source_color="color", get_target_color="color", get_width="width",
        width_min_pixels=1, width_max_pixels=3, great_circle=True,
        pickable=True, auto_highlight=True, opacity=0.78,
    )
    deck = pdk.Deck(
        layers=[arc_layer, buyer_symbol_layer, node_layer],
        initial_view_state=pdk.ViewState(latitude=27, longitude=126, zoom=1.1, pitch=0, bearing=0),
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={"html": "<b>{name}</b><br/>{node_type}<br/>{locality}, {country}<br/><b>Report concern:</b> {tooltip_issue}<br/><b>Exposure:</b> {linked_score}/100 · {tier}<br/>{source_note}",
                 "style": {"backgroundColor": "#182320", "color": "#e8eee9", "border": "1px solid #52635a"}},
    )
    chart_state = st.pydeck_chart(
        deck, use_container_width=True, height=560, key="interactive_case_investigation_map",
        on_select="rerun", selection_mode="single-object",
    )
    selected_node_id = _selected_map_node(chart_state)
    selected_node_id = selected_node_id if selected_node_id in detail_by_id else product.root_entity_id
    selected_detail = detail_by_id[selected_node_id]
    st.markdown("#### Selected investigation point")
    summary_cols = st.columns(4)
    summary_cols[0].metric("Entity", selected_detail["name"])
    summary_cols[1].metric("Map role", selected_detail["node_type"])
    summary_cols[2].metric(
        "Exposure score", f"{selected_detail['linked_score']:.1f} / 100"
        if selected_detail["linked_score"] is not None else "Not scored",
    )
    summary_cols[3].metric("Risk tier", selected_detail["tier"])
    st.write(selected_detail["issue"].replace("$", "USD "))
    st.caption(selected_detail["source_note"])
    st.caption("The score is a prioritization aid derived from report-tagged evidence. It is not a finding of legal liability or proof that forced labor occurred.")
    st.markdown("#### Map entities")
    st.dataframe([{
        "Entity": node["name"], "Role": node["node_type"], "Country": node["country"],
        "Report locality / coordinate basis": node["locality"],
        "Own score": "Not scored" if node["own_score"] is None else f"{node['own_score']:.1f}/100",
        "Linked exposure": "Not scored" if node["linked_score"] is None else f"{node['linked_score']:.1f}/100",
        "Tier label": node["tier"],
    } for node in map_nodes], width="stretch", hide_index=True)
    st.caption("Taiwan site pins use OpenStreetMap township/district centroids for Pingzhen, Guishan, and Hukou, not facility coordinates. Other places use country centroids; locations not supplied in the brief are explicitly marked unresolved. Affiliate linked exposure is the investigated company's score multiplied by the report-stated relationship weight. No live trade-route data is included.")

    st.markdown("#### Recruitment-debt lens")
    debt_profiles = recruitment_debt_profiles()
    st.caption("A case-specific view of worker-reported recruitment fees and debt signals. Bars show each report's individual fee range, with fee-paying interview counts and debt notes in the tooltip/table. The ranges are not multiplied by interview counts and are not extrapolated to the workforce.")
    debt_order = [item["company"] for item in sorted(debt_profiles, key=lambda item: item["fee_low_usd"])]
    debt_chart = alt.Chart(alt.Data(values=list(debt_profiles))).mark_rule(
        strokeWidth=9, strokeCap="round", color="#F0A15D",
    ).encode(
        x=alt.X("fee_low_usd:Q", title="Reported individual fee range (USD)",
                scale=alt.Scale(domain=[0, 7000]), axis=alt.Axis(format="$,.0f", tickCount=6)),
        x2=alt.X2("fee_high_usd:Q"),
        y=alt.Y("company:N", title=None, sort=debt_order,
                axis=alt.Axis(labelColor="#f5f5f7", labelLimit=260)),
        tooltip=[
            alt.Tooltip("company:N", title="Investigated manufacturer"),
            alt.Tooltip("worker_origin_country:N", title="Worker-origin country"),
            alt.Tooltip("workers_with_reported_fees:Q", title="Interviewees reporting fees"),
            alt.Tooltip("workers_interviewed:Q", title="Total workers interviewed"),
            alt.Tooltip("fee_low_usd:Q", title="Fee low (USD)", format="$,.0f"),
            alt.Tooltip("fee_high_usd:Q", title="Fee high (USD)", format="$,.0f"),
            alt.Tooltip("debt_evidence:N", title="Report-described debt evidence"),
        ],
    ).properties(height=235).configure_view(stroke=None, fill="#10263A").configure(
        background="#071A2B").configure_axis(
            gridColor="#354c5c", labelColor="#c2c0c6", titleColor="#f5f5f7", domainColor="#607a96")
    st.altair_chart(debt_chart, use_container_width=True, theme=None)
    st.dataframe([{
        "Investigated company": item["company"],
        "Worker-origin country": item["worker_origin_country"],
        "Fee interview sample": f"{item['workers_with_reported_fees']} of {item['workers_interviewed']}",
        "Reported fee range per worker": f"USD {item['fee_low_usd']:,}–{item['fee_high_usd']:,}",
        "Debt evidence in brief": item["debt_evidence"],
        "Monthly broker fee reported": (
            f"USD {item['monthly_broker_fee_usd'][0]}–{item['monthly_broker_fee_usd'][1]}"
            if item["monthly_broker_fee_usd"] else "Not quantified for this company in the supplied summary"
        ),
    } for item in debt_profiles], width="stretch", hide_index=True)

with evidence_tab:
    st.markdown("#### Supplier evidence")
    ranked_ids = sorted(assessment.suppliers, key=lambda entity_id: (
        -TIER_ORDER[assessment.suppliers[entity_id].own_tier],
        -assessment.suppliers[entity_id].composite_score, entities[entity_id].name,
    ))
    selected_id = st.selectbox(
        "Supplier", ranked_ids,
        format_func=lambda entity_id: f"{entities[entity_id].name} - {assessment.suppliers[entity_id].own_tier}",
    )
    entity, result = entities[selected_id], assessment.suppliers[selected_id]
    st.markdown(f"##### {entity.name}")
    st.caption(f"{entity.role} / {entity.country}{', ' + entity.region if entity.region else ''} / {entity.id}")
    st.write(f"**Own tier: {result.own_tier}.** {result.tier_reason}")
    score_col, convergence_col, confidence_col, inherited_col = st.columns(4)
    score_col.metric("Composite score", f"{result.composite_score:.3f}")
    convergence_col.metric("Converging pillars", f"{result.convergence} / 4")
    confidence_col.metric("Evidence confidence", f"{result.confidence} ({result.confidence_score:.2f})")
    inherited_col.metric("Inherited tier", result.inherited_tier or "None")
    if result.inherited_tier:
        st.caption("Inherited path: " + " -> ".join(entities[item].name for item in result.risk_path))
    st.markdown("**Risk evidence by pillar**")
    pillar_palette = {"exposure": "#65C29A", "linkage": "#72AFD1", "trade": "#F0A15D",
                      "worker": "#F07878", "transparency": "#E2C66F"}
    pillar_rows = [{"Pillar": pillar.title(), "Score": score, "Color": pillar_palette[pillar]}
                   for pillar, score in result.pillar_scores.items()]
    pillar_bars = alt.Chart(alt.Data(values=pillar_rows)).mark_bar(size=19, cornerRadiusEnd=3).encode(
        x=alt.X("Score:Q", title="Pillar score", scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%", tickCount=5)),
        y=alt.Y("Pillar:N", title=None, sort=list(result.pillar_scores.keys())),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("Pillar:N"), alt.Tooltip("Score:Q", format=".0%")],
    ).properties(height=180).configure_view(stroke=None, fill="#10263A").configure(
        background="#071A2B").configure_axis(
            gridColor="#354c5c", labelColor="#c2c0c6", titleColor="#f5f5f7", domainColor="#607a96")
    st.altair_chart(pillar_bars, use_container_width=True, theme=None)
    st.caption("Scores range from 0 to 1. Convergence threshold: 0.40 for the four non-transparency pillars.")
    st.markdown("**Reported ILO indicators**")
    st.write(", ".join(item.replace("_", " ").title() for item in result.ilo_indicators)
             if result.ilo_indicators else "No ILO indicators are tagged in available documents for this entity.")
    st.markdown("**Signals and provenance**")
    if result.signals:
        st.dataframe([{
            "Claim": signal.claim_kind, "Pillar": signal.pillar.title(), "Signal": signal.title,
            "Strength": f"{signal.strength:.2f}", "Detail": signal.detail,
            "Source IDs": ", ".join(signal.source_ids), "Next step": signal.next_step,
        } for signal in result.signals], width="stretch", hide_index=True)
    else:
        st.info("No risk signals were found for this supplier in the available fictional data.")

    selected_company = company_by_id(selected_id)
    st.markdown("#### Report-named potential downstream companies")
    st.caption("The report names possible or former connections. Each would be a potential direct buyer (Tier 1 downstream) only if confirmed; none is a confirmed edge or propagates risk.")
    relationships = possible_buyer_relationships(selected_company)
    if relationships:
        st.dataframe([{
            "Company": item["company"], "Supply-chain position": item["tier_position"],
            "Report status": item["status"],
        } for item in relationships], width="stretch", hide_index=True)
    if selected_company["ownership_to_verify"]:
        st.caption("Separate ownership leads (not product-flow tiers): " + "; ".join(selected_company["ownership_to_verify"]))
    render_case_list_screen()

with scoring_tab:
    st.markdown("#### Evidence pillars")
    st.write("Exposure, listed-entity linkage, trade-flow anomalies, worker indicators, and supplier transparency are assessed independently. Signals within one pillar combine using noisy-OR; they do not count as multiple converging pillars.")
    st.markdown("#### Illustrative tier rules")
    st.write("High: a direct listing-name match, at least three non-transparency pillars scoring 0.40 or more, or two such pillars with composite score at least 0.85. Elevated: two pillars converge or composite is at least 0.60. Watch: one pillar converges or composite is at least 0.30. Otherwise Low.")
    st.markdown("#### Inherited risk and confidence")
    st.write("A buyer inherits the most serious tier among mapped inputs with no minimum-share exemption. Input share scales inherited score as upstream effective score * (0.6 + 0.4 * share), but does not lower tier. Confidence is a separate evidence-completeness heuristic. Transparency affects composite and confidence, never convergence.")
    st.markdown("#### Claim labels and limitations")
    st.write("FACT identifies a recorded source claim, INFERENCE a derived relationship or pattern, and LEAD a lower-reliability or exploratory indicator. These labels do not establish truth. Missing evidence is not evidence of absence. Records and thresholds are fictional and illustrative; this app does not make legal, investigative, or forced-labor findings.")