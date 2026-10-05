from __future__ import annotations

import altair as alt
import streamlit as st

from sourcesight.data import MockSource
from sourcesight.engine import TIER_ORDER, assess_product


st.set_page_config(page_title="SourceSight", layout="wide")

TIER_COLORS = {
    "Low": "#3F806B",
    "Watch": "#C28D32",
    "Elevated": "#D66A45",
    "High": "#A43D3D",
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root {
  --ink: #1d302d;
  --muted: #60716c;
  --paper: #f4f3ed;
  --surface: #fffefa;
  --line: #d9ded6;
  --forest: #204d43;
  --teal: #397d73;
  --copper: #c36d48;
}
.stApp { background: var(--paper); color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; }
[data-testid="stHeader"] { background: rgba(244,243,237,.94); }
[data-testid="stSidebar"] { background: #203f38; }
[data-testid="stSidebar"] * { color: #f4f3ed; }
[data-testid="stSidebar"] [data-baseweb="select"] * { color: var(--ink); }
h1, h2, h3 { color: var(--ink); font-family: 'DM Sans', 'Avenir Next', sans-serif; letter-spacing: 0; }
h1 { font-size: 2.35rem; font-weight: 700; }
[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--line); border-top: 3px solid var(--teal);
  border-radius: 5px; padding: 14px 16px; min-height: 108px;
}
[data-testid="stMetricLabel"] { color: var(--muted); font-size: .82rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: clamp(1.2rem, 2vw, 1.8rem); overflow-wrap: anywhere; }
[data-testid="stAlert"] { border-radius: 4px; }
[data-testid="stTabs"] button { color: var(--muted); }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--forest); border-bottom-color: var(--copper); }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 4px; }
.eyebrow { color: var(--copper); font: 500 .76rem 'DM Mono', monospace; text-transform: uppercase; }
.chart-note { color: var(--muted); font-size: .86rem; }
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
        color=alt.condition("datum.on_path", alt.value("#c36d48"), alt.value("#b8c3bb")),
        strokeDash=alt.condition("datum.on_path", alt.value([1, 0]), alt.value([5, 4])),
    )
    nodes = alt.Chart(alt.Data(values=node_rows))
    halos = nodes.transform_filter("datum.path").mark_circle(size=620, filled=False, stroke="#c36d48", strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
    )
    points = nodes.mark_circle(size=360, stroke="#fffefa", strokeWidth=2).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        color=alt.Color("tier:N", scale=alt.Scale(domain=list(TIER_COLORS), range=list(TIER_COLORS.values())),
                        legend=alt.Legend(title="Own risk tier", orient="top")),
        tooltip=[alt.Tooltip("name:N", title="Supplier"), alt.Tooltip("role:N", title="Role"),
                 alt.Tooltip("location:N", title="Location"), alt.Tooltip("tier:N", title="Own tier"),
                 alt.Tooltip("effective_tier:N", title="Effective tier"),
                 alt.Tooltip("score:Q", title="Evidence score", format=".2f")],
    )
    labels = nodes.mark_text(dy=23, font="DM Sans", fontSize=11, fontWeight=500, color="#354943").encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
        text=alt.Text("label:N"),
    )
    chart = alt.layer(links, halos, points, labels).properties(
        height=max(360, 74 * max((len(items) for items in layers.values()), default=1)),
        padding={"left": 20, "right": 24, "top": 14, "bottom": 18},
    ).configure_view(stroke=None).configure(autosize={"type": "fit", "contains": "padding"})
    return chart


@st.cache_resource
def load_source():
    return MockSource()


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

map_tab, evidence_tab, scoring_tab = st.tabs(["Supply map", "Supplier evidence", "How scoring works"])

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
        ).properties(height=125).configure_view(stroke=None)
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
    pillar_palette = {"exposure": "#397d73", "linkage": "#386f91", "trade": "#c36d48",
                      "worker": "#a43d3d", "transparency": "#9a813e"}
    pillar_rows = [{"Pillar": pillar.title(), "Score": score, "Color": pillar_palette[pillar]}
                   for pillar, score in result.pillar_scores.items()]
    pillar_bars = alt.Chart(alt.Data(values=pillar_rows)).mark_bar(size=19, cornerRadiusEnd=3).encode(
        x=alt.X("Score:Q", title="Pillar score", scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%", tickCount=5)),
        y=alt.Y("Pillar:N", title=None, sort=list(result.pillar_scores.keys())),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("Pillar:N"), alt.Tooltip("Score:Q", format=".0%")],
    ).properties(height=180).configure_view(stroke=None)
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