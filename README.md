# SourceSight

SourceSight is a local supply-chain risk exploration prototype. The existing Product selector now lists seven manufacturer/product profiles from user-supplied material attributed to Transparentem's Taiwan investigation. SourceSight did not independently retrieve or verify the original PDF. The original fictional hoodie, solar, and tuna records remain in offline regression tests. This is decision support for human review, not an investigative or legal determination.

> **Featured case limitation.** Report-attributed allegations are not independently verified by SourceSight. Named possible buyers are unconfirmed connections, not customers or mapped supply-chain edges. List status remains unknown until an explicit current lookup is performed. Indicators and risk tiers are not findings that forced labor occurred. The model's thresholds are illustrative and are not calibrated for operational decisions.
>
> **Data limits.** Report-described allegations and company responses are shown with attribution, not as independently verified findings. Report-named buyers remain possible/unconfirmed and are never treated as supply edges. The report does not provide facility coordinates or upstream disclosure status; those remain unknown. The app does not run live lookups on load.

## Run locally

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL when it starts, normally <http://localhost:8501>. No API key or live-data credentials are needed. The app does not make external data requests on load.

## Run tests

```bash
python -m pytest -q
```

The test suite runs offline and checks the seven report-backed product choices and the original three fictional scoring cases, graph constraints, tier boundaries, source injection, and downstream propagation.

## Explicit public-data requests

After reviewing each publisher's terms and permitted use, the bounded CLI can manually download the U.S. Department of Labor goods-list XLSX and OpenSanctions CSV datasets:

```bash
python -m sourcesight.data_requests --source dol_goods
python -m sourcesight.data_requests --source opensanctions
```

The runner uses fixed HTTPS endpoints and host allowlists, a 20-second timeout, a 20 MB per-file response limit, and a 24-hour cache under `.cache/source_requests/`. Each file has a companion JSON record containing publisher, endpoint, retrieval time, and attribution. `--refresh` explicitly bypasses a fresh cache. These downloads are source material only: the app does not automatically parse them into entity matches or findings. No free-source request runs on app load.

Sayari and Tradeverifyd are not integrated or configured. The supplied request plan estimates approximately 28 Sayari and 21 Tradeverifyd calls; pricing was not supplied, so costs cannot be estimated here. Do not make paid calls without credentials, an approved budget, and explicit operator action.

## Current features

- Existing Product selector populated by seven report-backed products: notebooks, GPS devices, contact lenses, vehicles, optoelectronics, electronics, and water pumps.
- Report-attributed worker interview and fee summaries, company responses, illustrative assessments, verification leads, and an explicitly unnamed Garmin recruitment agency profile.
- Deterministic `DataSource`/`CaseStudySource` interface for the app and `MockSource` regression fixtures; possible buyers remain unconfirmed narrative data and no synthetic edges are created.
- Explainable exposure, listed-entity/network linkage, capacity and enforcement-timed trade volume/route-mix patterns, worker-indicator, and transparency signals with source IDs and FACT/INFERENCE/LEAD labels. Route changes are flagged as observable temporal patterns, not evidence of intentional diversion.
- Original noisy-OR aggregation and threshold-count convergence, illustrative tiers, separate evidence confidence, and share-scaled downstream risk paths.
- Interactive upstream-to-product supplier network with tier-colored nodes, hover details, and a highlighted inherited-risk route; exact route records remain available on demand.
- Dark, high-contrast reading theme using the mauve, rose, coral, and steel-blue palette with black/white surfaces and text; green Low and red High risk signals remain distinct.
- Geographic view uses an approximate Taiwan-wide marker because report material contains no facility locations; it does not fabricate facility pins or buyer links.
- Supplier tier distribution and comparative evidence-pillar charts, plus responsive two-column summary metrics on mobile.
- Risk-ordered supplier selection, provenance, ILO indicator display, and a user-readable scoring explanation.
- Focused offline tests for the hoodie, solar, and tuna acceptance behaviors and validation/propagation edge cases.

## Status and limitations

The app data is based on user-supplied summaries attributed to the October 2026 Transparentem report. SourceSight could not extract or independently verify the PDF. The original scoring model counts thresholded pillars but does not account for source dependence. The Taiwan sector overlay and worker indicators both derive from the same report; their convergence must not be read as independent corroboration. Report-named buyer connections and ownership claims remain unverified leads and never become confirmed propagation edges. Company response and non-response summaries are report-attributed; non-response does not increase claim reliability. Current enforcement/list status is unknown because no live lookup has run.

The app includes a manually invoked bounded download runner for public DOL and OpenSanctions sources, but it does not match entities, assess list status, or incorporate downloaded records. Paid Sayari and Tradeverifyd integrations are not implemented. The app does not create downloadable memos, use an AI analyst, verify worker accounts, reconcile chain of custody, or provide legal conclusions. All score thresholds are illustrative and require expert validation before real-world use. Risk tiers are prioritization cues only and must not be used for automated adverse action.

The geographic basemap uses online CARTO tiles. The report-backed profiles use an approximate Taiwan-wide centroid, not facility coordinates; the report supplies no facility addresses or administrative regions.
