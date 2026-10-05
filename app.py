from __future__ import annotations

import altair as alt
from collections import defaultdict
import pydeck as pdk
import streamlit as st

from sourcesight.data import MockSource
from sourcesight.engine import TIER_ORDER, assess_product
from sourcesight.case_study import COMPANIES, REPORT, CaseStudySource, company_by_id


st.set_page_config(page_title="SourceSight", layout="wide")

TIER_COLORS = {
    "Low": "#65C29A",
    "Watch": "#E2C66F",
    "Elevated": "#F0A15D",
    "High": "#F07878",
}
FLOW_BLUE = "#607A96"
RISK_RED = "#C7666D"
COUNTRY_CENTROIDS = {
    "CN": (35.9, 104.2), "IN": (20.6, 78.9), "VN": (16.0, 106.0),
    "MY": (4.2, 102.0), "TH": (15.8, 101.0),
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
    --muted: #c2c0c6;
    --paper: #09090c;
    --surface: #16161b;
    --line: #354c5c;
    --forest: #9e5b68;
    --teal: #607a96;
    --copper: #c7666d;
}
.stApp, [data-testid="stAppViewContainer"] { background: var(--paper); color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; }
[data-testid="stHeader"] { background: rgba(9,9,12,.97); }
[data-testid="stSidebar"] { background: #111115; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: #f5f5f7; }
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-baseweb="popover"] * { color: #f5f5f7; }
[data-baseweb="select"] > div { background: #202027; border-color: #607a96; }
h1, h2, h3, h4, p, label, li { color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; letter-spacing: 0; }
h1 { font-size: 2.35rem; font-weight: 700; }
[data-testid="stMetric"] {
    background: var(--surface); border: 1px solid var(--line); border-top: 3px solid var(--teal);
  border-radius: 5px; padding: 14px 16px; min-height: 108px;
}
[data-testid="stMetricLabel"] { color: var(--muted); font-size: .82rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: clamp(1.2rem, 2vw, 1.8rem); overflow-wrap: anywhere; }
[data-testid="stAlert"] { border-radius: 4px; background: #21191d; border: 1px solid #69545c; color: #f5f5f7; }
[data-testid="stAlert"] p { color: #f5f5f7; }
[data-testid="stTabs"] button { color: #b0c0b7; }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--forest); border-bottom-color: var(--copper); }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 4px; }
[data-testid="stMarkdownContainer"] a { color: #8fa7c1; }
[data-testid="stCaptionContainer"] { color: #c2c0c6; }
[data-testid="stSelectbox"] [data-baseweb="select"] { background: #202027; }
[data-testid="stExpander"] { background: #15151a; border-color: var(--line); }
.stButton button, [data-testid="stDownloadButton"] button { background: #354c5c; color: #fff; border-color: #607a96; }
.eyebrow { color: var(--copper); font: 500 .76rem 'DM Mono', monospace; text-transform: uppercase; }
@media (max-width: 700px) {
  .block-container { padding: 4.2rem 1rem 2rem; }
  h1 { font-size: 1.8rem; }
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
    points = nodes.mark_circle(size=360, stroke="#16161b", strokeWidth=2).encode(
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
    ).configure_view(stroke=None, fill="#16161b").configure(
        background="#16161b", autosize={"type": "fit", "contains": "padding"},
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
            "location": f"{region}, {country}" if region != "Country level" else country,
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
        st.warning("These are report-named possible or former connections, not confirmed customers, contracts, or supply-chain edges. They do not propagate risk in SourceSight.")
        buyers = company["buyers"]
        if buyers:
            rows = [{"x": 0, "y": index, "x2": 1, "y2": index,
                     "supplier": company["name"], "buyer": buyer,
                     "status": "Former reported connection" if "(former reported connection)" in buyer else "Possible connection; unconfirmed",
                     "buyer_label": buyer.replace(" (former reported connection)", "")}
                    for index, buyer in enumerate(buyers)]
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
                height=max(190, 42 * len(rows))).configure_view(stroke=None, fill="#16161b").configure(
                    background="#09090c"), use_container_width=True, theme=None)
            st.dataframe([{"Possible buyer": buyer.replace(" (former reported connection)", ""),
                           "Report wording status": "Former reported connection" if "(former reported connection)" in buyer else "Possible connection; unconfirmed"}
                          for buyer in buyers], width="stretch", hide_index=True)
        else:
            st.info("No buyer connection is supplied for this unnamed agency profile.")

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
        st.markdown("#### Free-source request runner")
        st.write("No network requests run when this app loads. After reviewing source terms, run the bounded CLI manually from the repository:")
        st.code("python -m sourcesight.data_requests --source dol_goods\npython -m sourcesight.data_requests --source opensanctions", language="bash")
        st.write("The runner uses HTTPS allowlisted endpoints, a 20-second timeout, a 20 MB response limit, and a 24-hour local cache. It requests the DOL 2024 goods-list XLSX and bounded OpenSanctions OFAC and U.N. Security Council CSV datasets. Results are saved under `.cache/source_requests/` with source attribution.")
        st.markdown("#### Paid providers")
        st.warning("Sayari and Tradeverifyd are not configured or called. The supplied request plan estimates about 28 Sayari and 21 Tradeverifyd calls; pricing was not provided, so no cost estimate can be responsibly stated. Do not run paid queries without credentials, an approved budget, and an explicit operator action.")
        st.caption("No API keys are collected, displayed, logged, or stored by this case-study view.")


@st.cache_resource
def load_source():
    return MockSource()


with st.sidebar:
    workspace = st.selectbox("Workspace", ("Fictional demo", "Featured case study"))

if workspace == "Featured case study":
    render_case_study()
    st.stop()

st.markdown('<div class="eyebrow">Supply chain intelligence / fictional prototype</div>', unsafe_allow_html=True)
st.title("SourceSight")
st.caption("Follow product inputs upstream. See where indicators appear and what evidence supports them.")
st.warning(
    "FICTIONAL MOCK DATA ONLY. Scores and indicators prioritize questions for human review. "
    "They are not findings that forced labor occurred, legal determinations, or allegations about real entities."
)

try:
    source = load_source()
    products = source.products()
    product_by_name = {f"{product.name} - {product.brand}": product for product in products}
    with st.sidebar:
        st.header("Assessment")
        selected_label = st.selectbox("Product", tuple(product_by_name))
        st.caption("Fictional fixtures. No live sources or API key required.")
    product = product_by_name[selected_label]
    assessment = assess_product(source, product.id)
    entities = source.entities()
except Exception:
    st.error("The mock assessment could not be loaded. Check the fixture records and try again.")
    st.stop()

st.subheader(product.name)
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

map_tab, geo_tab, evidence_tab, scoring_tab = st.tabs(
    ["Supply map", "Geographic view", "Supplier evidence", "How scoring works"])

with map_tab:
    st.markdown("#### Supplier network")
    st.caption("Raw inputs flow left to finished product. Node labels are supplier IDs; hover for full details. Color shows own tier; copper rings and links mark the product's highest-risk route.")
    risk_edges = set(zip(assessment.risk_path, assessment.risk_path[1:]))
    if product.edges:
        st.altair_chart(supply_network_chart(product, entities, assessment), use_container_width=True, theme=None)
    else:
        st.info("This product has no mapped input edges yet.")

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
        ).properties(height=125).configure_view(stroke=None, fill="#16161b").configure(
            background="#09090c").configure_axis(
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
    st.caption("Edges run upstream to downstream. Share scales inherited score, not tier; no share is exempt.")

with geo_tab:
    st.markdown("#### Supplier geography")
    st.caption("Region markers show supplier concentration. Curved links follow each mapped input from supplier to buyer; gold links mark the inherited-risk route.")
    geo_points = geographic_supplier_points(entities, assessment)
    geo_links = geographic_supply_links(product, entities, assessment)
    if geo_points:
        legend = " ".join(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px;">'
            f'<span style="width:10px;height:10px;border-radius:50%;background:{TIER_COLORS[tier]};display:inline-block"></span>'
            f'{tier}</span>' for tier in ("Low", "Watch", "Elevated", "High"))
        st.markdown(f'<div style="color:#c4d0c8;font-size:.86rem;margin-bottom:8px">Highest own tier: {legend}</div>',
                    unsafe_allow_html=True)
        flow_legend = (
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 0 8px;color:#c4d0c8;font-size:.86rem">'
            f'<span style="width:22px;border-top:2px solid {FLOW_BLUE};display:inline-block"></span>Mapped input flow'
            f'<span style="width:22px;border-top:3px solid {RISK_RED};display:inline-block;margin-left:14px"></span>Inherited-risk route'
            f'</span>'
        )
        st.markdown(flow_legend, unsafe_allow_html=True)
        arc_layer = pdk.Layer(
            "ArcLayer", data=geo_links,
            get_source_position="source_position", get_target_position="target_position",
            get_source_color="color", get_target_color="color", get_width="width",
            width_min_pixels=1, width_max_pixels=5, get_tilt=18,
            great_circle=True, pickable=True, auto_highlight=True, opacity=0.82,
        )
        marker_layer = pdk.Layer(
            "ScatterplotLayer", data=geo_points,
            get_position="[longitude, latitude]", get_fill_color="color",
            get_line_color=[229, 238, 232, 210], get_radius="radius",
            radius_min_pixels=9, radius_max_pixels=26, line_width_min_pixels=1,
            stroked=True, pickable=True, auto_highlight=True, opacity=0.9,
        )
        geo_deck = pdk.Deck(
            layers=[arc_layer, marker_layer],
            initial_view_state=pdk.ViewState(latitude=25, longitude=98, zoom=2.35, pitch=0, bearing=0),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={"html": "<b>{source_name}</b> → <b>{target_name}</b><br/>{input} · {share_label}<br/>On inherited-risk route: {on_risk_path}<hr/><b>{location}</b><br/>Highest own tier: {own_tier}<br/>Highest effective tier: {effective_tier}<br/>Mapped suppliers ({count}):<br/>{supplier_names}",
                     "style": {"backgroundColor": "#182320", "color": "#e8eee9", "border": "1px solid #52635a"}},
        )
        st.pydeck_chart(geo_deck, use_container_width=True, height=520, key="supplier_geography")
        st.caption("Location is approximate. The fictional fixtures provide regions, not facility coordinates; markers must not be interpreted as verified sites.")
        with st.expander("Inspect mapped regions and suppliers"):
            st.dataframe([{
                "Approximate area": point["location"], "Suppliers mapped": point["count"],
                "Highest own tier": point["own_tier"], "Highest effective tier": point["effective_tier"],
                "Suppliers": point["supplier_names"].replace("<br/>", "; "),
            } for point in geo_points], width="stretch", hide_index=True)
    else:
        st.info("No mapped supplier regions are available for this product.")

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
    ).properties(height=180).configure_view(stroke=None, fill="#16161b").configure(
        background="#09090c").configure_axis(
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

with scoring_tab:
    st.markdown("#### Evidence pillars")
    st.write("Exposure, listed-entity linkage, trade-flow anomalies, worker indicators, and supplier transparency are assessed independently. Signals within one pillar combine using noisy-OR; they do not count as multiple converging pillars.")
    st.markdown("#### Illustrative tier rules")
    st.write("High: a direct listing-name match, at least three non-transparency pillars scoring 0.40 or more, or two such pillars with composite score at least 0.85. Elevated: two pillars converge or composite is at least 0.60. Watch: one pillar converges or composite is at least 0.30. Otherwise Low.")
    st.markdown("#### Inherited risk and confidence")
    st.write("A buyer inherits the most serious tier among mapped inputs with no minimum-share exemption. Input share scales inherited score as upstream effective score * (0.6 + 0.4 * share), but does not lower tier. Confidence is a separate evidence-completeness heuristic. Transparency affects composite and confidence, never convergence.")
    st.markdown("#### Claim labels and limitations")
    st.write("FACT identifies a recorded source claim, INFERENCE a derived relationship or pattern, and LEAD a lower-reliability or exploratory indicator. These labels do not establish truth. Missing evidence is not evidence of absence. Records and thresholds are fictional and illustrative; this app does not make legal, investigative, or forced-labor findings.")