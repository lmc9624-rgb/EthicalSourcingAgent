# SourceSight

SourceSight is a local supply-chain risk exploration prototype for reviewing fictional product maps, supplier evidence signals, and possible upstream risk paths. It is decision support for human review, not an investigative or legal determination.

> **Fictional mock data only.** Every entity, person, source, document, event, and score in this repository is invented for demonstration. An indicator or risk tier is not a finding that forced labor occurred and is not an allegation about a real company. The model's thresholds are illustrative and are not calibrated for operational decisions.

## Run locally

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL when it starts, normally <http://localhost:8501>. No API key or live-data credentials are needed.

## Run tests

```bash
python -m pytest -q
```

The test suite runs offline and checks the three fictional cases, fixture integrity and graph constraints, tier boundaries, source injection, and downstream propagation.

## Current features

- Product selector for the hoodie, solar, and tuna demonstration supply chains.
- Deterministic `DataSource`/`MockSource` contracts and validation of entity references, shares, evidence dates, reliability, ILO tags, and directed-acyclic supply maps.
- Explainable exposure, listed-entity/network linkage, trade, worker-indicator, and transparency signals with source IDs and FACT/INFERENCE/LEAD labels.
- Noisy-OR aggregation, independent convergence, illustrative tiers, separate evidence confidence, and share-scaled downstream risk paths.
- Interactive upstream-to-product supplier network with tier-colored nodes, hover details, and a highlighted inherited-risk route; exact route records remain available on demand.
- Dark, high-contrast reading theme with complementary cyan/gold secondary accents while preserving green Low and red High risk signals.
- Geographic view aggregates fictional suppliers at approximate region centroids and draws curved supplier-to-buyer input links. Cyan marks mapped flows, gold marks the inherited-risk route, and marker color shows the highest own-risk tier; locations are not facility coordinates.
- Supplier tier distribution and comparative evidence-pillar charts, plus responsive two-column summary metrics on mobile.
- Risk-ordered supplier selection, provenance, ILO indicator display, and a user-readable scoring explanation.
- Focused offline tests for the hoodie, solar, and tuna acceptance behaviors and validation/propagation edge cases.

## Status and limitations

This is the first runnable M0/M1 product slice with an initial evidence interface. It uses only the checked-in fictional JSON fixture. It does not retrieve live records, create downloadable memos, use an AI analyst, establish supplier identity, verify worker accounts, reconcile chain of custody, or provide legal conclusions. All demo thresholds, baselines, and records need expert validation before any real-world use. Risk tiers are prioritization cues only and must not be used for automated adverse action.

The geographic basemap uses online CARTO tiles. Supplier markers are grouped by approximate region/country centroids from the fictional fixture and are not facility coordinates; the region summary remains available below the map.
