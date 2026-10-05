from __future__ import annotations

import streamlit as st

from sourcesight.data import MockSource
from sourcesight.engine import TIER_ORDER, assess_product


st.set_page_config(page_title="SourceSight", layout="wide")


@st.cache_resource
def load_source():
    return MockSource()


st.title("SourceSight")
st.caption("Supply-chain risk exploration. Deterministic fictional-data prototype.")
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
    st.markdown("#### Mapped suppliers and inputs")
    risk_path = set(assessment.risk_path)
    edge_rows = []
    for edge in product.edges:
        upstream, buyer = entities[edge.source], entities[edge.target]
        upstream_result, buyer_result = assessment.suppliers[edge.source], assessment.suppliers[edge.target]
        edge_rows.append({
            "Route": "Highlighted risk path" if edge.source in risk_path and edge.target in risk_path else "Mapped",
            "Upstream supplier": f"{upstream.name} ({upstream.id})",
            "Role / country": f"{upstream.role} / {upstream.country}",
            "Input": edge.input_name,
            "Input share": f"{edge.share:.0%}",
            "Supplier own tier": upstream_result.own_tier,
            "Buyer own tier": buyer_result.own_tier,
        })
    if edge_rows:
        st.dataframe(edge_rows, width="stretch", hide_index=True)
    else:
        st.info("This product has no mapped input edges yet.")
    st.markdown("#### Entities")
    entity_rows = []
    for entity_id, result in assessment.suppliers.items():
        entity = entities[entity_id]
        entity_rows.append({
            "Entity": f"{entity.name} ({entity_id})", "Role": entity.role,
            "Country / region": f"{entity.country} / {entity.region}", "Own tier": result.own_tier,
            "Inherited tier": result.inherited_tier or "None", "Effective tier": result.effective_tier,
            "On product risk path": "Yes" if entity_id in risk_path else "No",
        })
    st.dataframe(entity_rows, width="stretch", hide_index=True)
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
    st.markdown("**Pillar scores**")
    pillar_columns = st.columns(5)
    for column, (pillar, score) in zip(pillar_columns, result.pillar_scores.items()):
        column.metric(pillar.title(), f"{score:.2f}")
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