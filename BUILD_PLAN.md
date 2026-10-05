# SourceSight: Build Plan

This plan sequences SourceSight from a runnable mock-data MVP to a production-ready decision-support product. Build and validate the deterministic backend before relying on its results in the interface. Add live data only after the mock workflow, evidence provenance, and human-review boundaries are stable.

## Build principles

- Deliver a working vertical slice at each milestone; keep the application runnable throughout.
- Freeze the data contracts before frontend and backend work integrate.
- Keep signal detection, scoring, propagation, presentation, and memo writing in separate layers.
- Add tests with each behavior, not as a final cleanup step.
- Treat every score as explainable decision support. Never frame an indicator or tier as a finding of forced labor.
- Keep the initial dataset fictional. Do not add API secrets or real allegations to the repository.

## Phase 0: Repository and product baseline

**Build:** Open and inspect the target repository (`lm9624-rgb/Lola`), confirm its existing framework, instructions, branch protections, and CI before introducing SourceSight files. Agree on the initial product scope: local Streamlit app, fictional JSON fixtures, three demo products, deterministic scoring, and optional AI memo writing. Preserve the concept and functional specification as the current product references.

**Exit checks:** The target repository and branch are confirmed; the project structure and existing conventions are known; the MVP and non-goals are recorded; secrets are not present in tracked files.

**Deliverable:** A repository plan and implementation checklist. Do not overwrite existing repository work to make it resemble the proposed structure.

## Phase 1: Runnable application skeleton

**Build:** Establish or adapt the Python package structure, dependency file, Streamlit entry point, startup instructions, and VS Code run/debug configuration. Add a minimal health view that starts without live credentials. Define a single command for launching the app and a single command for tests.

**Exit checks:** A clean environment can install dependencies, start the app, and run the test command. The app clearly identifies itself as a mock-data demonstration. The core experience works without an Anthropic key.

**Deliverable:** A runnable shell with no scoring behavior embedded in UI code.

## Phase 2: Data contracts and mock source

**Build:** Implement typed or clearly documented contracts for products, entities, supply edges, listings, enforcement events, sector-risk rows, trade profiles, documents, and signals. Implement `DataSource` and `MockSource` so the engine depends on an interface rather than JSON file paths. Add fixture validation for required keys, valid entity references, shares in the range 0-1, valid dates, and recognized reliability and ILO-indicator values. Ensure product supply maps are directed acyclic graphs; report invalid maps instead of recursing indefinitely.

Keep provenance fields attached to each evidence item: source identifier, source type, date where available, reliability, summary, and claim kind as derived by the engine.

**Exit checks:** All three demo products load through the source interface. Invalid fixture references and malformed inputs fail with useful messages. A test source can be injected without changing the scoring code.

**Deliverable:** Stable domain and data-source contracts for parallel backend and UI work.

## Phase 3: Signal detectors

**Build:** Implement one detector per evidence pillar in `signals.py`: sector/geography exposure, listed-entity linkage, trade anomalies, worker indicators, and transparency. Keep each detector deterministic and return the same `Signal` structure with strength, FACT/INFERENCE/LEAD kind, detail, source IDs, and next investigative step. Centralize tunable thresholds and weights; mark mock-specific values as illustrative.

Add focused tests for exact matches, fuzzy matches near the threshold, network links at one and two hops, missing trade data, short date series, no/low-reliability documents, and disclosed versus undisclosed upstream sources.

**Exit checks:** Each detector can be tested independently; missing optional evidence yields no signal rather than a crash; every emitted signal has usable provenance and a valid strength.

**Deliverable:** A tested evidence layer that does not assign supplier tiers.

## Phase 4: Supplier scoring and confidence

**Build:** Implement pillar aggregation, weighted composite calculation, convergence counting, tier assignment, tier reasons, and confidence in `engine.py`. Preserve the distinction between own risk and confidence. Convergence counts independent non-transparency pillars, not signal volume. Make direct listing matches and all tier thresholds explicit and covered by tests.

Test boundary values immediately below, at, and above each threshold. Verify that several signals in one pillar do not increase the convergence count, transparency can affect composite/confidence but never convergence, and a direct listing match yields High.

**Exit checks:** Identical inputs always produce identical assessments. A reviewer can trace the tier to pillar values, signals, and a plain-language tier reason. Threshold changes cause intentional, test-visible behavior changes.

**Deliverable:** A pure and explainable assessment for one supplier.

## Phase 5: Product graph and downstream propagation

**Build:** Assess all entities in a product map, resolve upstream entities before buyers, propagate the strongest input tier without a share-based exemption, scale only the inherited score by the configured input-share formula, and retain the path back to the source of risk. Define handling for multiple suppliers at the same tier, ties in propagated score, cycles, missing entities, and a root supplier with its own direct risk.

Add product-level tests for the hoodie, solar, and tuna fixtures, plus small synthetic graphs for multi-hop propagation, multiple branches, low-share inputs, and root-owned risk.

**Exit checks:** The final product tier and path are deterministic and correct on all fixtures. A 10% input still transfers its tier. Cyclic or incomplete graphs produce a clear validation error rather than hanging or silently dropping risk.

**Deliverable:** A complete `ProductAssessment` suitable for presentation and memo generation.

## Phase 6: Core interface

**Build:** Connect Streamlit to the assessment API and implement the product selector, product summary, supply map, supplier-evidence view, and scoring explanation. The map shows upstream inputs, shares, own-risk colors, inherited-risk outlines, and the root product's highlighted risk route. The evidence view sorts suppliers by own tier and score and exposes confidence, convergence, pillar values, indicators, source IDs, claim kinds, details, and follow-up steps.

Keep all tier colors and explanatory labels consistent. Clearly distinguish own tier from inherited/effective tier. Provide readable empty and error states when evidence or a product map is incomplete. Do not expose raw exception traces to normal users.

**Exit checks:** A user can move from product-level risk to the originating supplier and inspect the evidence without leaving the app. The interface never hides source IDs or presents missing evidence as a clean result. Validate the graph at desktop and narrow viewport widths.

**Deliverable:** A usable end-to-end risk exploration workflow without AI.

## Phase 7: Memo generation and optional AI analyst

**Build:** Implement the deterministic rule-based memo first. It should summarize the product tier and path, elevated/high suppliers, Watch suppliers, cited evidence, recommendations, and claim-label definitions. Include a non-finding disclaimer, generation date, and mock-data notice. Provide a Markdown download.

After the deterministic version is stable, add the optional AI analyst behind explicit configuration. Give it read-only tools for supplier listing, evidence retrieval, and risk-path retrieval. Do not allow it to alter scores or invent source IDs. Handle missing credentials and API errors cleanly, fall back to the rule-based memo, and keep credentials out of UI output and logs. Test tool arguments, unknown supplier IDs, maximum-turn behavior, API failures, and memo fallback.

**Exit checks:** Rule-based memo works offline. AI can only read the assessed data and cite its source identifiers. AI failure never blocks assessment or memo download.

**Deliverable:** A shareable, traceable memo workflow with an optional analyst assist.

## Phase 8: Integrated quality, usability, and release

**Build:** Run the full automated suite, type/lint checks if configured, and a manual end-to-end review of each fixture. Confirm the outputs match the acceptance criteria in `SPECIFICATION.md`: hoodie risk reaches E05 while E06 stays Low; S04 has the expected trade signals and High tier while S06 stays Watch; T05 surfaces worker indicators while T06 stays Low. Check that each memo avoids treating indicators as findings.

Review accessibility and usability of labels, graph contrast, keyboard navigation, download naming, progress/error states, and narrow screens. Confirm setup instructions work from a fresh environment. Add a brief model-limitations and mock-data notice where users will see it.

**Exit checks:** Tests pass from a clean checkout; all three demo workflows can be completed; the app is startable by a new contributor; no secrets or unintended data are tracked. Review the Git diff and publish only intended task files to the confirmed repository branch.

**Deliverable:** Tagged or otherwise documented mock-data MVP release, depending on repository practice.

## Phase 9: Live-data readiness (separate approval)

Do not begin live integrations as part of the mock MVP by default. First validate the model with intended users and domain experts. Then, one source at a time, implement a production `DataSource` adapter with authentication, licensing review, provenance, timestamps, source-quality handling, rate limits, and failure behavior. Keep connectors replaceable and avoid changing score semantics as a side effect of switching providers.

Calibrate thresholds against reviewed cases; assess false positives, false negatives, stale records, entity-resolution errors, and uncertainty communication. Add a human-review and correction process before any real supplier assessment is used for operational decisions. Do not launch automated adverse action, supplier blacklisting, or legal conclusions from model scores.

**Exit checks:** Data rights and security are reviewed; identity-resolution performance and threshold calibration are documented; users can inspect and contest sources; operational governance and human review are in place.

## Dependency order at a glance

```text
Repository baseline
  -> Runnable app shell
  -> Data contracts + mock source
  -> Signal detectors
  -> Supplier scoring
  -> Product propagation
  -> Core interface
  -> Rule memo -> Optional AI analyst
  -> Integrated QA and MVP release
  -> Separately approved live-data readiness
```

The frontend can begin low-fidelity layout work after the domain contracts are agreed in Phase 2. Final wiring should wait until `ProductAssessment` and path semantics are stable. Signal detectors can be developed in parallel after the `Signal` contract is fixed, but scoring, propagation, and UI integration depend on their tested outputs.
