# SourceSight Backlog

**Inputs:** [`SPECIFICATION.md`](SPECIFICATION.md) and [`BUILD_PLAN.md`](BUILD_PLAN.md). The repository does not currently contain `PLAN.md` or a `BACKLOG.md` template; this backlog uses `BUILD_PLAN.md` and a conventional Now / Next / Later layout. The specification uses numbered sections rather than requirement IDs, so the stable `US-xx` and `FR-xx` references below map backlog tasks to those sections.

## Milestones

- **M0 - Runnable foundation:** repository conventions are respected and the mock-data app can be installed, launched, and tested locally. Maps to Build Plan Phases 0-1.
- **M1 - Deterministic assessment engine:** mock records are validated, suppliers are scored, and risk paths are propagated with tests. Maps to Build Plan Phases 2-5.
- **M2 - Analyst workflow:** users inspect the map/evidence and generate a memo. Maps to Build Plan Phases 6-7.
- **M3 - Release and live-data readiness:** integrated quality/release, followed by separately approved live-source readiness. Maps to Build Plan Phases 8-9.

## Traceability Index

| ID | Specification coverage |
|---|---|
| US-01 | §3 product investigation workflow; §6.1 supply map |
| US-02 | §3 supplier inspection; §6.2 supplier evidence |
| US-03 | §3, §6.3 memo workflow and download |
| FR-01 | §4 product, entity, evidence, and `DataSource` contracts |
| FR-02 | §4 source provenance and fixture data integrity; §8 data integrity |
| FR-03 | §5.1-5.2 exposure and listed-entity linkage signals |
| FR-04 | §5.1-5.2 trade-flow anomaly signals |
| FR-05 | §5.1-5.2 worker indicators and transparency signals |
| FR-06 | §5.3 pillar aggregation, convergence, tiers, and confidence |
| FR-07 | §5.4 downstream propagation and risk path |
| FR-08 | §6.4 scoring explanation |
| FR-09 | §6.3 rule-based memo and Markdown download |
| FR-10 | §6.3 optional AI analyst and fallback behavior |
| FR-11 | §7 fictional fixture acceptance expectations |
| FR-12 | §8 explainability, privacy, resilience, and auditability |
| FR-13 | §9 production validation, live data, and human review |

## Now

Only M0 and M1 work is listed here. Items are ordered by dependency; the first item is the highest-value next action.

### 1. [M0] Create a runnable Streamlit application shell

**Type:** Infrastructure · **Estimate:** 2-4 hours · **Build Plan:** Phase 1 · **Spec:** infrastructure; FR-12

Create the app entry point and minimal home view. It must launch without an Anthropic key, clearly identify the fictional mock-data demo, and keep scoring out of the UI layer.

**Acceptance criteria**
- **Given** a clean Python environment with the documented dependencies installed, **when** the developer launches the app using the documented command, **then** the Streamlit page opens without requiring an API key.
- **Given** the app is running, **when** the home view is displayed, **then** it identifies the data as fictional mock data and makes no claim that a supplier has been found to use forced labor.
- **Given** no product assessment implementation is wired yet, **when** the shell loads, **then** it displays a clear placeholder rather than failing or inventing a risk result.

### 2. [M0] Add reproducible setup, launch, and test commands

**Type:** Infrastructure · **Estimate:** 2-3 hours · **Build Plan:** Phase 1 · **Spec:** infrastructure; FR-12

Add dependency declarations and contributor-facing setup instructions, plus one documented command each for app launch and automated tests. Add VS Code run/test configuration only if consistent with repository conventions.

**Acceptance criteria**
- **Given** a fresh checkout, **when** a contributor follows the documented setup steps, **then** dependencies install and the launch command starts the shell.
- **Given** the same checkout, **when** the documented test command runs, **then** it discovers and executes the project tests.
- **Given** an environment without `ANTHROPIC_API_KEY`, **when** setup and tests run, **then** no secret is required and no credential is written to tracked files.

### 3. [M1] Define assessment contracts and the mock data-source interface

**Type:** Functional · **Estimate:** 3-4 hours · **Build Plan:** Phase 2 · **Spec:** FR-01, FR-02

Define the product, entity, edge, evidence, and signal shapes and implement an injectable `DataSource` contract with a JSON-backed mock implementation. Preserve source IDs and document reliability/date metadata.

**Acceptance criteria**
- **Given** the three fixture products and their referenced entities, **when** loaded through `MockSource`, **then** callers can retrieve products, entities, listings, enforcement events, sector baselines, trade profiles, and documents without reading JSON directly in scoring code.
- **Given** an alternate test data source implementing the contract, **when** it is passed to the assessment entry point, **then** the assessment can use it without modifying detector logic.
- **Given** a document with provenance metadata, **when** it is returned by the source, **then** its identifier, type, date, reliability, and summary remain available to downstream signals.

### 4. [M1] Validate mock records and supply-map graphs

**Type:** Functional · **Estimate:** 2-4 hours · **Build Plan:** Phase 2 · **Spec:** FR-02

Validate required fixture fields, entity references, share bounds, dates, reliability values, ILO tags, and acyclic supply maps. Produce actionable validation errors for malformed fixtures.

**Acceptance criteria**
- **Given** a valid fixture set, **when** validation runs, **then** all three product maps pass and every edge refers to existing entities with a share from 0 through 1.
- **Given** an edge references an unknown entity or has an out-of-range share, **when** validation runs, **then** it reports the product and invalid field instead of silently omitting the edge.
- **Given** a cyclic supply map or an unknown ILO/reliability value, **when** validation runs, **then** it reports a clear error before assessment or propagation begins.

### 5. [M1] Implement exposure and listed-entity linkage signals

**Type:** Functional · **Estimate:** 3-4 hours · **Build Plan:** Phase 3 · **Spec:** FR-03

Implement sector/geography specificity, name normalization and fuzzy listing matches, and the bounded ownership/director/address network search. Emit explainable signals with source IDs and claim kinds.

**Acceptance criteria**
- **Given** an entity with multiple matching sector baselines, **when** exposure detection runs, **then** it selects the most specific matching row.
- **Given** an entity that directly matches a listing, **when** linkage detection runs, **then** it emits a strength-1 FACT signal citing the listing ID.
- **Given** an unlisted entity connected to a listed entity within two network hops, **when** linkage detection runs, **then** it emits an INFERENCE signal describing the chain and calculated edge strength; links beyond the configured hop limit do not produce a signal.

### 6. [M1] Implement trade-flow anomaly signals

**Type:** Functional · **Estimate:** 2-4 hours · **Build Plan:** Phase 3 · **Spec:** FR-04

Detect capacity exceedance, volume surges around enforcement events, and recent below-floor prices using the specification's illustrative thresholds. Missing or short series must be handled without exceptions.

**Acceptance criteria**
- **Given** monthly exports exceed capacity by more than the configured threshold, **when** trade detection runs, **then** it emits an INFERENCE signal showing observed volume, estimated capacity, and ratio.
- **Given** sufficient before/after months show a qualifying increase after an enforcement event, **when** trade detection runs, **then** it emits a signal citing the event and trade source.
- **Given** no trade profile or too few months for a comparison, **when** trade detection runs, **then** it returns no unsupported anomaly and does not fail.

### 7. [M1] Implement worker-indicator and transparency signals

**Type:** Functional · **Estimate:** 2-4 hours · **Build Plan:** Phase 3 · **Spec:** FR-05

Combine ILO indicator weights with document reliability and detect undisclosed upstream sourcing. Retain document provenance and distinguish FACT from LEAD according to reliability.

**Acceptance criteria**
- **Given** a high-reliability document with recognized ILO tags, **when** worker detection runs, **then** it emits a FACT signal with indicator labels and source ID.
- **Given** a medium- or low-reliability document with recognized tags, **when** worker detection runs, **then** it emits a LEAD signal with strength reduced by the documented reliability multiplier.
- **Given** an entity that does not disclose upstream sources, **when** transparency detection runs, **then** it emits a transparency signal whose strength reflects whether mapped inputs exist; a disclosing entity emits none.

### 8. [M1] Implement supplier aggregation, tiers, and confidence

**Type:** Functional · **Estimate:** 3-4 hours · **Build Plan:** Phase 4 · **Spec:** FR-06

Aggregate signal strengths within pillars and into the weighted composite; calculate convergence, direct-listing override, tier/reason, and confidence separately. Cover threshold boundaries with focused tests.

**Acceptance criteria**
- **Given** several signals in one pillar, **when** convergence is calculated, **then** that pillar contributes at most one convergence count.
- **Given** transparency is the only pillar above the hit threshold, **when** the tier is calculated, **then** it does not count toward convergence, while its documented composite contribution remains included.
- **Given** inputs at, below, and above each configured tier boundary or a direct listing match, **when** assessment runs, **then** the expected tier and plain-language reason are returned deterministically.
- **Given** evidence completeness changes but signal strength does not, **when** confidence is recalculated, **then** confidence may change independently of the risk tier.

### 9. [M1] Propagate risk through product inputs

**Type:** Functional · **Estimate:** 3-4 hours · **Build Plan:** Phase 5 · **Spec:** FR-07

Resolve suppliers upstream-first, inherit the most serious input tier without a minimum-share exemption, scale only the inherited score by input share, and preserve the path back to the source.

**Acceptance criteria**
- **Given** an upstream supplier with non-Low risk and a mapped buyer edge with a 10% share, **when** propagation runs, **then** the buyer inherits the supplier's tier while the inherited score is share-scaled.
- **Given** multiple upstream paths, **when** propagation runs, **then** it chooses the most serious inherited tier and returns a path ending at the originating risk source.
- **Given** a cyclic map, **when** propagation is invoked, **then** validation blocks it with a clear error rather than recursing indefinitely.

### 10. [M1] Lock expected behavior with product-level regression tests

**Type:** Functional · **Estimate:** 2-3 hours · **Build Plan:** Phases 3-5 · **Spec:** FR-11

Add regression tests for the three fictional fixtures and synthetic edge cases for low-share propagation, multiple branches, and direct root risk.

**Acceptance criteria**
- **Given** the hoodie fixture, **when** it is assessed, **then** product risk is High through E05 and E06 remains Low.
- **Given** the solar fixture, **when** it is assessed, **then** S04 has the capacity and post-enforcement surge signals and is High, while S06 remains Watch.
- **Given** the tuna fixture, **when** it is assessed, **then** T05 is Elevated with debt-bondage indicators and T06 remains Low.

## Next

Only M2 work is listed here. Implement after M1 contracts and `ProductAssessment` path semantics are stable.

### [M2] Render supply-map entities and input edges

**Spec:** US-01 · **Build Plan:** Phase 6 · **Estimate:** 2-3 hours.

Render every product entity and upstream-to-downstream edge, including the entity name, role, country, supplied input, and input share.

### [M2] Show product tier and inherited-risk route

**Spec:** US-01 · **Build Plan:** Phase 6 · **Estimate:** 2-3 hours.

Style nodes by own tier, distinguish inherited risk, highlight the root product's path, and show the effective product tier and upstream source.

### [M2] Add risk-ordered supplier selection and summary

**Spec:** US-02 · **Build Plan:** Phase 6 · **Estimate:** 2-3 hours.

Sort suppliers by own tier and composite score. Show the selected supplier's identity, own tier and reason, inherited tier/path, convergence, and confidence.

### [M2] Show pillar scores and evidence details

**Spec:** US-02 · **Build Plan:** Phase 6 · **Estimate:** 2-3 hours.

Display all five pillar scores, ILO indicators, and signals with claim kind, source IDs, strength, details, and next steps.

### [M2] Explain scoring and handle incomplete evidence

**Spec:** FR-08, FR-12 · **Build Plan:** Phase 6 · **Estimate:** 2-3 hours.

Explain pillars, thresholds, claim labels, confidence, and propagation. Add useful empty/error states without presenting missing evidence as a clean result or exposing raw exception traces.

### [M2] Assemble the rule-based memo

**Spec:** US-03, FR-09, FR-12 · **Build Plan:** Phase 7 · **Estimate:** 2-3 hours.

Generate a deterministic memo with product tier/path, suppliers of concern, Watch suppliers, cited evidence, recommended next steps, mock-data notice, date, claim-label definitions, and explicit non-finding language.

### [M2] Add memo download and offline regression coverage

**Spec:** US-03, FR-09, FR-11 · **Build Plan:** Phase 7 · **Estimate:** 2-3 hours.

Provide a Markdown download and test that memos for all three fixtures are generated without AI and never assert forced labor as a finding.

### [M2] Implement read-only AI investigation tools

**Spec:** FR-10, FR-12 · **Build Plan:** Phase 7 · **Estimate:** 2-3 hours.

Implement supplier-list, supplier-evidence, and risk-path tools over the completed assessment. Return source IDs and never permit tools to modify scores.

### [M2] Connect optional AI memo generation and fallback

**Spec:** FR-10, FR-12 · **Build Plan:** Phase 7 · **Estimate:** 2-3 hours.

Add the configured AI workflow, keep secrets out of logs/output, handle missing credentials and API/tool failures, and preserve the rule-based memo as fallback.

## Later

M3 and production-readiness tasks stay out of Now. Live integrations require separate approval.

### [M3] Verify clean-checkout installation and regression suite

**Spec:** FR-11, FR-12 · **Build Plan:** Phase 8 · **Estimate:** 2-3 hours.

Run setup, launch, and full automated tests from a clean checkout; record results and fix release-blocking failures.

### [M3] Review usability and release safeguards

**Spec:** FR-11, FR-12 · **Build Plan:** Phase 8 · **Estimate:** 2-3 hours.

Verify keyboard navigation, graph contrast, responsive layout, visible mock-data and limitations notices, and useful user-facing error states; record release evidence and outstanding defects.

### [M3] Approve a live-source provider and data scope

**Type:** Infrastructure · **Spec:** FR-13 · **Build Plan:** Phase 9 · **Estimate:** 2-3 hours.

Produce a signed-off provider/data-scope decision that identifies an initial data domain, access method, licensing constraints, authentication owner, and outage expectations. This is a bounded decision deliverable, not open-ended research. Do not start connector work until approval exists.

### [M3] Implement the first approved `DataSource` adapter

**Type:** Infrastructure · **Spec:** FR-01, FR-02, FR-13 · **Build Plan:** Phase 9 · **Estimate:** 2-4 hours per approved data domain.

Implement one replaceable provider adapter for the approved data domain, retaining source provenance and timestamps and handling rate limits, incomplete responses, and provider outages without changing scoring semantics. Create separate backlog tasks for each additional data domain.

### [M3] Calibrate thresholds against a reviewed case set

**Spec:** FR-12, FR-13 · **Build Plan:** Phase 9 · **Estimate:** 2-4 hours per calibration iteration.

Deliver a documented reviewed-case set, threshold comparison, false-positive/false-negative analysis, and proposed versioned configuration changes with regression tests. Do not ship threshold changes without reviewer approval.

### [M3] Document human review and evidence correction procedure

**Spec:** FR-12, FR-13 · **Build Plan:** Phase 9 · **Estimate:** 2-3 hours.

Deliver an operational procedure that identifies who reviews assessments, how stale or disputed evidence is flagged and corrected, how decisions are recorded, and how the process prevents automated adverse action from model scores.
