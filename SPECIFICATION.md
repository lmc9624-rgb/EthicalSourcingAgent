# SourceSight: Product Specification

**Status:** MVP behavior specification
**Product type:** Browser-based supply-chain risk exploration tool
**Primary user:** Human-rights, responsible-sourcing, compliance, procurement, and investigative teams

## 1. Purpose and scope

SourceSight helps a reviewer examine potential forced-labor risk associated with a specific product and its mapped supply chain. It connects a product's inputs to supplier records and evidence, scores suppliers across multiple evidence pillars, traces higher-risk inputs toward the finished product, and produces a shareable assessment memo.

The product is decision support. It identifies risk indicators, not findings that forced labor occurred. A qualified human reviewer is responsible for assessing evidence, resolving identity matches, seeking corroboration, and deciding what action is appropriate. Scores and thresholds in the MVP are illustrative and are not legal determinations.

The current MVP is a local Streamlit application backed by fictional JSON data. It demonstrates the product workflow and scoring model; it is not a production due-diligence system and does not fetch live records by default.

## 2. Users and jobs to be done

- **Responsible-sourcing and human-rights teams** need to identify which mapped products and upstream suppliers merit deeper review.
- **Compliance and legal teams** need a traceable account of what evidence supports a concern, what is inferred, and what remains unverified.
- **Procurement and category managers** need concrete requests to send suppliers, such as origin documentation, production records, or clarification of subcontracting.
- **Investigators and analysts** need to inspect links between entities, trade patterns, worker-level reports, enforcement lists, and a product's bill of materials.

The tool assumes the user has a product record and at least a partial supplier/input map. It is intended to prioritize and structure inquiry, not replace audits, worker engagement, legal advice, or a complete human-rights due-diligence program.

## 3. Core product workflow

1. The user opens the app and chooses one of the available products in the sidebar.
2. SourceSight loads the product's mapped suppliers and edges, evaluates each supplier's available evidence, calculates own-risk scores and tiers, and propagates risk from inputs to buyers.
3. The user reviews the product-level tier and risk path, then inspects the supply map to see suppliers, inputs, shares, own tiers, and the path through which inherited risk travels.
4. The user selects suppliers in risk order and reviews pillar scores, confidence, ILO indicators, evidence, sources, and suggested next steps.
5. The user generates a rule-based memo, or optionally uses the AI analyst when an Anthropic API key is configured. The memo can be downloaded as Markdown.

The UI contains four views: **Supply map**, **Supplier evidence**, **Memo**, and **How scoring works**. The sidebar includes the product selector and a persistent notice that the current data is fictional. When configured, it also indicates whether the AI analyst is available.

## 4. Product and supply-chain data

A product record contains an identifier, name, brand, summary, root entity identifier, and a list of supply edges. Each edge identifies the supplier (`from`), buyer (`to`), supplied input, and the supplier's share of that input. Edges point upstream-to-downstream, from material source toward the finished product. Shares are proportions from 0 to 1 and describe the share of that input represented by the source, not a legal de minimis threshold.

Each entity record includes a stable identifier, name, country, region, role, sector, registered address, directors, parent ownership records, and whether upstream sources are disclosed. Evidence records may include enforcement-list entries, enforcement events, sector/geography baselines, monthly trade profiles, and documents. Documents include source identifiers, type, date, reliability, summary, and any pre-tagged ILO indicators.

All scoring inputs are accessed through a `DataSource` interface. The MVP's `MockSource` reads local JSON files. A future source implementation may provide equivalent product, entity, listing, enforcement, sector-risk, trade-profile, and document methods. Replacing the data source must not silently change scoring semantics.

## 5. Supplier evidence and scoring

### 5.1 Evidence pillars

Each supplier is evaluated on five pillars:

| Pillar | MVP evidence |
|---|---|
| Sector and geography exposure | Sector/country/region risk baselines; the most specific matching row is selected. |
| Links to listed entities | Fuzzy name matches to listed entities and corporate-network proximity through ownership, shared directors, or shared addresses. |
| Trade-flow anomalies | Exports above estimated capacity, export surges around enforcement events, and prices below an illustrative legal-labor cost floor. |
| Worker-level indicators | Documents pre-tagged with one or more of the 11 ILO forced-labor indicators. |
| Supplier transparency | Whether the supplier discloses upstream sources; a refusal or missing disclosure creates a transparency signal. |

Every signal has a pillar, title, strength from 0 to 1, claim kind (`FACT`, `INFERENCE`, or `LEAD`), explanatory detail, source identifiers, and an optional recommended next step. High-reliability worker documents are labeled FACT; medium- and low-reliability worker documents are labeled LEAD. Derived ownership proximity and trade patterns are labeled INFERENCE. These labels describe the kind of claim, not a final judgment about a supplier.

### 5.2 Signal detection rules in the prototype

- **Exposure:** match the entity's sector and any non-empty country/region constraints. If multiple rows match, use the row with the greatest country/region specificity.
- **Listed-entity linkage:** normalize company names and compare them with a fuzzy similarity threshold of 0.82. A direct match produces a strength-1 signal. The corporate graph then searches up to two hops. Ownership edges have strength 0.8 when ownership is at least 50%, otherwise 0.6; shared-director edges have strength 0.55; shared-address edges have strength 0.5. Multi-hop signal strength is the product of edge strengths.
- **Trade anomalies:** compare peak monthly exports with stated monthly capacity; a ratio above 1.15 creates a capacity signal. Compare up to three available months before and after an enforcement-event date; a 1.25x or greater increase creates a surge signal. A price-floor signal is created when one or more of the latest three monthly prices are below the configured floor. These are illustrative pattern detectors, not proof of evasion or illegal labor.
- **Worker indicators:** combine ILO indicator weights using noisy-OR, then multiply by document reliability. Most indicator weights are 0.3; restriction of movement, debt bondage, retention of identity documents, and withholding of wages weigh 0.5; physical and sexual violence weighs 0.6; excessive overtime weighs 0.2. Reliability multipliers are 1.0 (high), 0.75 (medium), and 0.5 (low).
- **Transparency:** when upstream sources are not disclosed, emit a signal with strength 0.6 if the entity has mapped inputs, or 0.4 otherwise. Transparency contributes to the composite but does not count toward convergence.

Noisy-OR aggregation is used for multiple signals within a pillar and for the weighted pillar contributions to the composite. For values $v_i$ in the range [0, 1], noisy-OR is $1 - \prod_i (1-v_i)$. Pillar weights are exposure 0.5, linkage 0.9, trade 0.7, worker 0.9, and transparency 0.3.

### 5.3 Convergence, tiers, and confidence

Convergence counts how many of the four non-transparency pillars (exposure, linkage, trade, worker) have a pillar score of at least 0.4. Multiple signals in the same pillar may increase its score but count as only one converging pillar.

Tiers are assigned in this order:

1. **High** for a direct listing match, three or more converging pillars, or two converging pillars with a composite score of at least 0.85.
2. **Elevated** for two converging pillars, or a composite score of at least 0.6.
3. **Watch** for one converging pillar or a composite score of at least 0.3.
4. **Low** otherwise.

Confidence is calculated separately from risk. It starts at 0.25 and adds 0.2 when trade data exists, 0.2 when documents exist, 0.15 when upstream sources are disclosed, and 0.2 when there is at least one non-exposure FACT signal. Confidence is High at 0.75 or above, Medium at 0.5 or above, and Low otherwise. Confidence describes evidence-base completeness under this heuristic; it is not the probability that a claim is true.

### 5.4 Downstream propagation

Suppliers are assessed before their buyers. A buyer inherits the most serious tier available from any mapped input, with no minimum-share exemption. Input share scales the propagated score using `upstream effective score * (0.6 + 0.4 * share)`; it does not downgrade the inherited tier. The product's effective tier is the more serious of the root entity's own tier and its inherited tier. SourceSight retains an upstream path so the user can trace inherited risk to its originating supplier.

## 6. User-facing requirements

### 6.1 Supply map

- Display all entities and edges in upstream-to-downstream order.
- Show entity name, role, country, and own-risk tier on each node.
- Use color to encode own tier and a distinct emphasized outline when the entity inherits a higher tier than its own.
- Emphasize edges on the root product's inherited-risk path.
- Label each edge with the input and share.
- Display a tier legend and product-level effective tier, including the upstream source and path when risk is inherited.

### 6.2 Supplier evidence

- List suppliers ordered by own tier and composite score, highest first.
- For the selected supplier, show role and location, own tier and reason, composite score, convergence count, and confidence.
- If risk is inherited, show its tier and input path.
- Show all five pillar scores, reported ILO indicators, and evidence signals.
- For every signal, show claim kind, pillar, title, strength, detail, source IDs, and next step when available.
- If there are no signals, state that no risk signals were found in available data.

### 6.3 Memo and AI analyst

The rule-based memo is available without an API key. It includes product identity and summary, generation date, effective product tier, highest-risk path, suppliers with own tier Elevated or High, Watch-tier suppliers, cited signals, and recommended next steps derived from sufficiently strong signals. It must state that it identifies risk indicators rather than findings of forced labor and must explain FACT, INFERENCE, and LEAD labels. The user can download the memo as a `.md` file.

The optional Claude analyst receives read-only tools to list suppliers, retrieve one supplier's evidence, and retrieve the risk path. It may explain and cross-check the same assessment but may not alter scores. It must cite source IDs, qualify claims, identify gaps or contradictions, avoid asserting forced labor as fact, and end with three useful investigative steps. If AI is unavailable or errors, the rule-based memo remains usable; an AI failure falls back to the rule-based memo.

### 6.4 Scoring explanation

The app must describe the five pillars, convergence thresholds, downstream propagation, evidence labels, and the limitations of the model in user-readable language. It must make clear that transparency affects confidence and composite score but not convergence.

## 7. Prototype acceptance criteria

The mock cases should demonstrate distinct behaviors:

- The hoodie assessment reaches High product risk through the Xinjiang ginnery (E05), while the Indian cotton source (E06) remains Low.
- The solar case detects capacity and post-enforcement volume anomalies for Strait Crest Trading (S04) and assigns it High; Baotou Northern Wafer (S06), with exposure alone, remains Watch.
- The tuna case surfaces worker-level indicators for the recruitment broker (T05), while the certified alternative fleet (T06) remains Low.
- Memos for all three cases explicitly distinguish risk indicators from findings and never assert that a supplier uses forced labor.
- Scores, paths, sources, and supplier details remain inspectable without enabling the AI analyst.

These are regression expectations for the fictional fixtures, not claims about real companies or calibration evidence for live use.

## 8. Non-functional requirements and boundaries

- **Explainability:** every score must be traceable to signals, pillar aggregation, tier rules, and (when applicable) a supply-path edge.
- **Data integrity:** missing evidence must not be represented as evidence of absence. Preserve source IDs and reliability metadata.
- **Privacy and secrets:** keep API keys out of source files, exported memos, and logs. The optional AI feature must be disabled when no key is configured.
- **Resilience:** errors in optional AI memo generation must not disable the core assessment or rule-based memo.
- **Auditability:** thresholds and weights must be configurable in code and covered by focused tests when changed.
- **Scope boundary:** the MVP does not establish legal liability, certify suppliers, verify worker testimony, calculate a legally operative UFLPA determination, perform a complete chain-of-custody reconciliation, or provide live data by default.

## 9. Future validation before production use

Before applying the model to real suppliers, validate identity matching, source reliability, completeness and age of supply maps, sector/geography baselines, trade-capacity and price thresholds, ownership-network logic, worker-indicator tagging, and propagation semantics with domain experts. Test how analysts interpret inherited tiers, confidence, and uncertainty. Live integrations should preserve provenance, timestamps, licensing constraints, and a path to correct disputed or stale records. Production use should include an explicit human-review process and governance for model changes.
