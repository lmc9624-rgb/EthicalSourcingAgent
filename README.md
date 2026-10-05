# SourceSight

**Repository:** [github.com/lmc9624-rgb/EthicalSourcingAgent](https://github.com/lmc9624-rgb/EthicalSourcingAgent)

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

**Current local preview:** [http://localhost:8505](http://localhost:8505) (available while the SourceSight preview server is running on this machine). For a new local run, use the URL printed by Streamlit.

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

The case-study **Data requests** panel also has an explicit **Run public list screening** action. It downloads/caches public OpenSanctions CSV snapshots for the U.S. DHS UFLPA Entity List, U.S. CBP forced-labor orders, and C4ADS Long Shadows (Xinjiang), then checks manufacturer and report-named buyer names against listed names and aliases. Requests do not run on app load. Results are exact normalized name/alias candidates only, not identity resolution, and never change assessment tiers. A no-match means no exact name/alias was present in that downloaded snapshot, not that a company is cleared. OpenSanctions data is CC BY-NC 4.0; commercial use requires a separate license.

## Current features

- Existing Product selector populated by seven report-backed products: notebooks, GPS devices, contact lenses, vehicles, optoelectronics, electronics, and water pumps.
- Product choices use manufacturer-plus-production titles, such as “Compal Electronics | Notebook PC Manufacturing.”
- Report-attributed worker interview and fee summaries, company responses, illustrative assessments, verification leads, and an explicitly unnamed Garmin recruitment agency profile.
- Report-named possible buyers shown as potential direct downstream customers (Tier 1 only if the relationship is verified); ownership claims are shown separately and are not product-flow tiers. Neither relationship type creates an edge or propagates risk.
- Manual OpenSanctions screening against three public forced-labor/research datasets, with snapshot provenance, exact-name/alias candidate results, and identity-review caveats.
- Deterministic `DataSource`/`CaseStudySource` interface for the app and `MockSource` regression fixtures; possible buyers remain unconfirmed narrative data and no synthetic edges are created.
- Explainable exposure, listed-entity/network linkage, capacity and enforcement-timed trade volume/route-mix patterns, worker-indicator, and transparency signals with source IDs and FACT/INFERENCE/LEAD labels. Route changes are flagged as observable temporal patterns, not evidence of intentional diversion.
- Original noisy-OR aggregation and threshold-count convergence, illustrative tiers, separate evidence confidence, and share-scaled downstream risk paths.
- Interactive upstream-to-product supplier network with tier-colored nodes, hover details, and a highlighted inherited-risk route; exact route records remain available on demand.
- Dark, high-contrast reading theme using the mauve, rose, coral, and steel-blue palette with black/white surfaces and text; green Low and red High risk signals remain distinct.
- Geographic view separates the report-named Taiwan study site, worker-origin countries, and possible buyer markets. Country-centroid markers are approximate display context, not facility or headquarters coordinates. Worker arcs are labor-corridor context; buyer arcs are unconfirmed report leads, not material-supplier edges. Open list screening returned no exact-name candidates, and no upstream material tiers are identified.
- Geographic view is interactive: selecting an investigated manufacturer or report-linked recruiter/affiliate displays the report-attributed conduct and exposure score. The Garmin recruiter is scored from its own report-tagged indicators; Mitsubishi/Yulon/Tsurumi parent or affiliate entries show association-weighted exposure only, not independent violation scores. Finished-product import routes are not included in this map yet.
- Map symbols distinguish investigated manufacturers (orange circles) from report-contacted possible buyer markets (blue diamonds); recruiter/affiliate, worker-origin, and port-context nodes remain separately styled.
- Geographic view includes a recruitment-debt lens comparing report-stated per-worker fee ranges, fee-paying interview counts, worker-origin countries, and debt notes. It does not multiply sample ranges into workforce totals or extrapolate beyond the interview sample.
- Supply map includes a geographic report-link view for the selected investigated manufacturer, recruiter/corporate-affiliation leads, and separate possible-buyer markets, with locations and location precision. Report claims remain distinguished from confirmed supplier edges.
- Sidebar includes an agentic PDF investigation intake preview. File selection is presentational only; PDF extraction, entity resolution, and report scoring are not implemented and uploaded reports do not affect assessments.
- Supplier tier distribution and comparative evidence-pillar charts, plus responsive two-column summary metrics on mobile.
- Risk-ordered supplier selection, provenance, ILO indicator display, and a user-readable scoring explanation.
- Focused offline tests for the hoodie, solar, and tuna acceptance behaviors and validation/propagation edge cases.

## Status and limitations

The app data is based on user-supplied summaries attributed to the October 2026 Transparentem report. SourceSight could not extract or independently verify the PDF. The original scoring model counts thresholded pillars but does not account for source dependence. The Taiwan sector overlay and worker indicators both derive from the same report; their convergence must not be read as independent corroboration. Report-named buyer connections and ownership claims remain unverified leads and never become confirmed propagation edges. Company response and non-response summaries are report-attributed; non-response does not increase claim reliability. Current enforcement/list status is unknown because no live lookup has run.

The app includes manually invoked bounded downloads for public DOL and OpenSanctions sources. Its case-screening action compares names against UFLPA, CBP, and C4ADS snapshots, but does not establish identity or incorporate candidate matches into scoring. No open source reviewed here provides independently verified supplier-buyer links for the companies in this report; report-named relationships remain leads. Paid Sayari and Tradeverifyd adapters and credentials are not present in this checkout. The app does not create downloadable memos, use an AI analyst, verify worker accounts, reconcile chain of custody, or provide legal conclusions. All score thresholds are illustrative and require expert validation before real-world use. Risk tiers are prioritization cues only and must not be used for automated adverse action.

The geographic basemap uses CARTO/OpenStreetMap-derived tiles. Reported place names such as Pingzhen, Taoyuan are shown as text only; plotted points remain country centroids rather than facility or company-headquarters coordinates. The case brief does not identify upstream material supplier tiers, and no open data source checked here confirms extra company links. The map does not convert these leads into supplier edges.
