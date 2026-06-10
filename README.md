# BEPS 2.0 Pillar Two Data Gap Copilot

An AI-assisted web app that tells a multinational tax team whether its source data is ready for Pillar Two compliance — and if not, **exactly what is missing, where it likely lives, who owns it, and what to ask for**.

> **Status: built and working.** Streamlit app + deterministic Python core + optional Claude narrative layer, with a synthetic demo dataset and a 25-test suite. See [Quickstart](#quickstart).

---

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/make_sample_data.py   # regenerate synthetic inputs (already checked in)
.venv/bin/streamlit run app.py                 # open http://localhost:8501
.venv/bin/python -m pytest                     # 25 tests
```

Optional AI narrative: `export ANTHROPIC_API_KEY=...` and flip the "Draft memo narrative with Claude" toggle in the sidebar. Everything else runs fully offline and deterministic.

### Deploying to Streamlit Community Cloud

1. Push this repo to GitHub (public repo for the free tier).
2. At [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py` on `main`.
3. (Optional) In the app's **Settings → Secrets**, add `ANTHROPIC_API_KEY = "sk-ant-..."` to enable the Claude memo narrative. Without it the app runs in deterministic mode — every feature works except the AI-drafted prose.

---

> 🎤 **Presenting this?** The full presenter script — exact clicks, talking points, interactive beats, Q&A cheat sheet, troubleshooting — is in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

## The 5-minute demo script

0. **Demo story (📖 tab).** Meet **Aurora Global Group** — a fully synthetic €1.2bn consumer-electronics multinational built for this demo: a low-ETR Irish holding company, a people-light Singapore IP hub, a half-onboarded UK acquisition, and four source systems that don't agree. The tab tells the story and lists every problem planted in the data.
1. **Source intake (Tab 1).** The app loads five messy "Aurora Global Group" files — entity master, Excel trial balance, tax provision extract, CbCR report, jurisdiction attributes — profiles every column, hashes every file, and flags that *"Aurora UK Service Ltd"* (typo) had to be fuzzy-matched to the entity master.
2. **Mapping review (Tab 2).** A heuristic engine maps source columns (`PBT_Local`, `TaxExpAdj`, `Rev_Total`…) to a Pillar Two field catalog with confidence scores. High-confidence matches are pre-approved; `Tangible_Assets_NBV` (0.85) and the unmapped `Employees` column wait for the reviewer. The reviewer can remap or reject anything — approvals drive everything downstream.
3. **Data gap dashboard (Tab 3).** 15 gaps, severity-weighted readiness score of 87%. Headlines: Ireland is missing entity-level deferred tax detail (blocks GloBE ETR), Singapore has no entity-level payroll (blocks SBIE), the UK entity has no jurisdiction assigned (blocks everything). Each gap carries a likely data owner and a ready-to-send remediation request.
4. **Safe harbour triage (Tab 4).** Per jurisdiction: can we even evaluate the three transitional CbCR safe harbour tests, and where we can, what's the indicative result? Ireland *fails* the simplified ETR test (12% vs 17%), Netherlands likely qualifies under de minimis, Singapore can't be concluded because income tax accrued is missing from the CbC report.
5. **Readiness memo & export (Tab 5).** A workpaper-style memo (executive summary, blockers, owner-by-owner data requests, open questions, full mapping appendix), a gap-register CSV, and a JSON audit package. The final package is **gated** until all mappings are dispositioned and entities reconciled.

6. **Use your own data (📥 tab).** The app is not sample-bound: switch off the sample toggle, upload any CSV/XLSX extracts, and review the suggested mappings. The tab documents exactly what files/columns to request (entity master, trial balance, provision extract, CbC Table 1, jurisdiction attributes) and offers blank CSV templates whose headers map automatically.

The question every tab serves: *"Are we ready to calculate and file — and if not, exactly what is missing?"*

---

## Design principle: AI accelerates, rules decide

| Layer | What it does | Where |
| --- | --- | --- |
| **Deterministic (always on)** | Column-mapping confidence scores, entity fuzzy-matching, completeness rules, severity/readiness scoring, safe harbour data checks and indicative thresholds, audit package | `src/pillar_two_copilot/` |
| **AI (optional, Claude Opus 4.8)** | Drafts the memo *narrative only*, from deterministic results, via structured outputs (JSON schema enforced). Never alters a number. Falls back to a deterministic draft if no key. | `claude_client.py` |
| **Human (required)** | Approves/overrides every mapping, resolves fuzzy entity matches; the final audit package is blocked until review gates pass | App tab 2 / tab 5 |

Audit trail by design: every mapped value traces to source file (SHA-256-hashed) → sheet → column → confidence → approval status, all preserved in the exported JSON package and memo appendices.

---

## Architecture

```
beps-pillar-two-data-gap-copilot/
  app.py                          # Streamlit UI (5 tabs)
  scripts/make_sample_data.py     # regenerates the synthetic Aurora dataset
  data/sample_inputs/             # messy synthetic client files (CSV + XLSX)
  src/pillar_two_copilot/
    field_catalog.py              # 17 canonical fields: purposes blocked, severity, owner, remediation, synonyms
    ingestion.py                  # CSV/Excel loading + column profiling (lineage anchor)
    column_mapper.py              # heuristic column->field suggestions w/ confidence + reasons
    entity_matcher.py             # legal-suffix-aware fuzzy entity reconciliation
    completeness.py               # assemble entity/jurisdiction datasets, find gaps, readiness score
    safe_harbour.py               # transitional CbCR safe harbour triage (de minimis / simplified ETR / routine profits)
    memo.py                       # workpaper memo rendering (deterministic narrative fallback)
    claude_client.py              # optional Claude Opus 4.8 narrative drafting (structured output)
    export.py                     # gap CSV + JSON audit package
  tests/                          # 25 tests incl. end-to-end run on the sample data
```

Data flow: `load files → profile columns → suggest mappings → human review → assemble entity/jurisdiction datasets (entity reconciliation) → gap rules + readiness score + safe harbour triage → memo + exports`.

### Why these choices

- **Streamlit over Next.js** — one-day-buildable, interview-friendly, and the review workflow (approve mappings, watch the score change) demos well as a single reactive script.
- **Field catalog as data, not code** — adding a field means one dict entry (label, purposes, severity, owner, remediation, synonyms); mapper, gap rules, memo, and score all pick it up automatically.
- **Confidence thresholds, not magic** — ≥0.85 pre-approved, 0.45–0.85 suggested-but-held, <0.45 left unmapped. The note column says *why* each match scored what it did.
- **Safe harbour = readiness, not advice** — the app's first question is "can this test even be evaluated with the data on hand?"; indicative pass/fail is labelled as such and routed to tax technical review.

---

## The synthetic dataset (planted problems)

`scripts/make_sample_data.py` builds "Aurora Global Group" (6 entities, 6 jurisdictions, >€750m revenue) with deliberate real-world messiness:

| Planted problem | Where | What the app does |
| --- | --- | --- |
| Entity names differ across systems (`Ltd` vs `Limited` vs `B.V.`, plus a typo) | trial balance vs entity master | suffix-aware normalization; the typo surfaces as a *fuzzy* match for review |
| Missing jurisdiction | Aurora UK Services Ltd in entity master | high-severity gap; routine-profits test marked unevaluable for the UK |
| Missing entity-level deferred tax | Ireland, provision extract | high-severity gap blocking GloBE ETR; remediation = request a deferred tax rollforward |
| Payroll only at country level | Singapore (blank in TB, present in CbCR) | SBIE gap + routine profits test blocked |
| Missing tangible assets | Netherlands, trial balance | SBIE gap |
| Blended tax adjustment line | `TaxExpAdj` in provision extract | mapped to covered-taxes adjustments; flagged for disaggregation |
| Missing income tax accrued | Singapore row of CbCR | simplified ETR test unevaluable |
| Field nobody provided | excluded dividends | "not present in any uploaded source" gap for all entities |

---

## Interview context (Big 4 Tax Technology)

Big 4 firms position their Pillar Two platforms around data ingestion, compliance automation, analytics, and responsible AI. This demo is framed as the **pre-calculation readiness layer** that complements (never competes with) such platforms: before any engine can calculate, someone has to prove the data exists, reconcile entities across systems, and chase the gaps.

Talk track:

> "I chose Pillar Two because it's a perfect tax technology problem: global rules, fragmented data, evolving guidance, high compliance risk, and a need for auditability. My demo focuses on the data readiness layer. AI is used where it's strong — classification, explanation, drafting — while every calculation, validation, and test stays deterministic, traceable, and gated behind human review."

Differentiators to hit live: (1) AI as reviewer-accelerator, not unchecked calculator; (2) audit trail by design — hash → sheet → column → confidence → approval; (3) tax operating-model awareness — every gap names a likely owner (provision, consolidation, HR, fixed assets, local controllers); (4) export gates that mirror real review controls.

Reference material:

- OECD GloBE Model Rules / Pillar Two hub: https://www.oecd.org/en/topics/sub-issues/global-minimum-tax/global-anti-base-erosion-model-rules-pillar-two.html
- OECD GIR XML schema guide: https://www.oecd.org/en/publications/globe-information-return-pillar-two-xml-schema_c594935a-en.html

---

## Possible extensions (not built, by intent)

- GIR field-level coverage mapped to the OECD XML schema
- QDMTT/IIR/UTPR effective-date logic per jurisdiction (currently a status flag)
- Persistence (SQLite) for multi-session review workflows and remediation tracking
- Claude-drafted, owner-addressed remediation emails from the gap register
- A second LLM pass suggesting mappings for the columns heuristics leave unmapped (`Employees` → headcount)

These are deliberately out of scope: the demo's value is the *workflow shape* — ingest, map, review, gate, export — not rule coverage.

---

## Disclaimer

Interview/demo prototype only. Synthetic data. Not tax advice. Implements a simplified field catalog and indicative transitional safe harbour thresholds, not the full OECD GloBE rules. Does not reproduce or rely on any firm's proprietary technology.
