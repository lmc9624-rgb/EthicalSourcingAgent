# SourceSight: Product Concept

## The idea

SourceSight is a decision-support tool for understanding where human-rights risk may enter a product’s supply chain, how that risk can travel through upstream inputs, and what evidence supports each concern. It starts with a product, maps its suppliers back toward raw materials, and brings together several kinds of evidence in one reviewable picture.

Its purpose is not to declare that a company has used forced labor. It is to help a human investigator ask better questions, prioritize follow-up, and explain why a supplier or sourcing route deserves attention.

## Why it should exist

A finished product can depend on suppliers several tiers removed from the brand or importer. A review focused only on the direct supplier may therefore miss relevant upstream inputs. At the same time, risk information can be scattered across ownership records, enforcement lists, trade data, worker reports, supplier disclosures, and commodity or regional risk references. These sources describe different parts of a situation and vary in reliability; considered separately, they can be difficult to connect to a particular product.

SourceSight is intended to make those connections legible. It follows the inputs rather than only the corporate ownership chain: a reviewer can see which material comes from which supplier, where a risk signal appears, and whether that risk is inherited by downstream buyers. It places evidence beside the score, labels claims as FACT, INFERENCE, or LEAD, and makes gaps in transparency visible. The result is a traceable starting point for investigation rather than an opaque ranking.

## Who it is for

The primary users are people responsible for supply-chain due diligence who need to move between product-level sourcing and supplier-level evidence:

- **Responsible-sourcing and human-rights teams** deciding which suppliers, materials, or sourcing routes need deeper review.
- **Compliance and legal teams** preparing a documented, carefully qualified account of indicators and evidence for internal decisions.
- **Procurement and category managers** identifying where to request origin documentation, production records, or corrective action from suppliers.
- **Investigators and analysts** comparing independent signals, tracing corporate or trade relationships, and recording what remains unverified.

The tool is most useful when a team has at least a partial bill of materials or supplier map and needs to prioritize limited review capacity. It is not a replacement for worker engagement, independent verification, legal advice, or a complete due-diligence program.

## How it works

For each supplier, SourceSight organizes evidence into five pillars: sector and geography exposure, links to listed entities, trade-flow anomalies, worker-level indicators, and supplier transparency. It distinguishes the number of independent pillars from the volume of signals within a single pillar, so repeated observations of one kind do not automatically appear to be independent corroboration. It also keeps confidence in the available data separate from the risk tier.

The product map then carries risk downstream through supplier inputs. This lets a reviewer see both a supplier’s own evidence and risk inherited from upstream sources, including the path through which it travels. Each signal retains its description, source, claim type, and suggested next investigative step. A memo can summarize the current assessment for review and sharing.

## What makes the approach useful

- **Product-first:** begin with an item and its inputs, not just a company name or watchlist search.
- **Path-aware:** show where risk enters and how it reaches downstream suppliers or the finished good.
- **Evidence-led:** expose the underlying signals and sources so a reviewer can challenge or corroborate them.
- **Convergence-aware:** treat independent evidence categories as more meaningful than a large count of similar signals.
- **Human-centered:** identify indicators and follow-up actions without turning a model score into a finding of forced labor.

## A practical first step

The current prototype uses fictional companies, people, and documents to exercise three different patterns: upstream cotton exposure, solar-industry trade and network anomalies, and worker-level indicators in fishing. That makes it suitable for testing the model’s logic and interface without API costs or making real-world allegations. The next step is to validate whether the maps, explanations, and follow-up recommendations help intended users make faster, better-documented review decisions. Before any live use, data sources, thresholds, uncertainty handling, and legal language would need expert review and calibration.

**In one sentence:** SourceSight helps sourcing and compliance teams see how risk evidence connects to a product’s upstream inputs, so they can investigate the right places with a clear account of what is known, inferred, and still unverified.
