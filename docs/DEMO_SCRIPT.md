# Demo Script — Pillar Two Data Gap Copilot

Presenter walkthrough for the live app. Target length: **8–10 minutes** plus Q&A.
Live app: **https://pillar-two-data-gap-copilot.streamlit.app** • Repo: **https://github.com/RichieSater/beps-pillar-two-data-gap-copilot**

---

## Before the demo (5-minute checklist)

- [ ] Open the live app in a fresh browser tab. A **page refresh fully resets the session** — do this right before you start so no leftover state from rehearsal shows.
- [ ] Confirm the sidebar shows **"Use synthetic Aurora sample files" ON** and **"Draft memo narrative with Claude" OFF** (deterministic mode — zero dependency on an API key mid-demo).
- [ ] Confirm the five metric tiles read: **Readiness 87% · Data gaps 15 · Entities 6 · Jurisdictions 6 · Mappings awaiting review 0**. If they do, everything downstream will match this script.
- [ ] **Offline fallback** (if the venue wifi dies):
  ```bash
  cd ~/dev/beps-pillar-two-data-gap-copilot
  .venv/bin/streamlit run app.py
  ```
  Identical app on localhost:8501.
- [ ] Optional: have one of the blank CSV templates (from the 📥 tab) downloaded and lightly filled, in case someone asks "can it take *our* data?" and you want to upload live.

---

## The 30-second opener (before touching anything)

> "Every Pillar Two engine — every Big 4 platform, every in-house build — assumes the data is already there. In practice, the hardest question a tax team faces is earlier: **do we even have the data to calculate, run safe harbour tests, and file — and if not, what exactly is missing, where does it live, and who do we ask?**
>
> This is a copilot for that question. AI accelerates the boring parts — mapping messy columns, drafting the memo — but every score, every gap, every test result is deterministic, traceable, and gated behind human review. Let me show you a realistic mess."

---

## Tab-by-tab walkthrough

### 1 · 📖 Demo story (~1 min)

**Do:** You land here by default. Gesture at the left narrative, then the right-hand table.

**Say:**
> "Meet Aurora Global Group — fully synthetic, €1.2bn consumer electronics group, so comfortably in Pillar Two scope. It looks like every post-acquisition multinational: a low-tax Irish holding company, a Singapore IP hub with profit but no people, a UK acquisition that never got fully onboarded, and four source systems that don't agree with each other.
>
> The audit committee has asked the Head of Tax one question: *can we rely on the safe harbours?* Before anyone can answer, the team has to assemble entity-level data from all four systems. Every problem in this table is planted in the files you're about to see — and every one of them is a pattern you'd recognize from real engagements."

**Point at the metric tiles (top):**
> "The copilot has already ingested the files: 6 entities, 6 jurisdictions, 15 gaps, 87% data-ready. Here's how it got there."

### 2 · Tab "1 · Source intake" (~1 min)

**Do:** Click the tab. Scroll briefly through the column profiles, then stop at the **Entity name reconciliation** table at the bottom.

**Say:**
> "Five files — CSVs and a real Excel trial balance. Every column is profiled: type, fill rate, sample values. And every file is SHA-256 hashed, because everything downstream needs to trace back to evidence.
>
> First catch: entity names don't match across systems. 'Limited' versus 'Ltd', 'B.V.' with dots — normalized away automatically. But look at this one —" *(point at the fuzzy row)* "— the trial balance says 'Aurora UK **Service** Ltd', singular. That's a typo, the matcher is 97% confident, and instead of silently merging it, it's **flagged for a human**. That's the design philosophy of the whole tool."

### 3 · Tab "2 · Mapping review" (~2 min) — the control point

**Do:** Click the tab. Scroll slowly; pause on `TaxExpAdj`, `Tangible_Assets_NBV`, and `Employees`.

**Say:**
> "This is where AI meets control. The mapper scores every source column against a Pillar Two field catalog and tells you **why**: 'PBT_Local' is an exact synonym match at 0.95 — pre-approved. 'Tangible_Assets_NBV' only scores 0.85 — the note says it's a partial match, and a reviewer should look. 'Employees' gets no confident match at all, so it's left unmapped rather than guessed.
>
> Nothing flows into any calculation until it's approved on this screen."

**Interactive beat (the money moment):** Untick the **approve** checkbox on `DTA_Movement` (the deferred tax column).

> "Watch the top of the screen — I just rejected one mapping…"

*(The app reruns: readiness drops, gap count jumps, because deferred tax now reads as missing for every entity.)*

> "…and the readiness score and gap register recalculated instantly. The reviewer's decision **is** the pipeline."

**Do:** Re-tick the checkbox. Confirm the tiles return to **87% / 15**.

### 4 · Tab "3 · Data gap dashboard" (~2 min) — the headline

**Do:** Click the tab. Point at the table rows, then the severity chart.

**Say:**
> "Here's the answer to 'what's missing'. Not a list of nulls — every gap says **what it blocks, who likely owns it, and the exact request to send**:
>
> - Ireland is missing entity-level **deferred tax** — that's high severity because it blocks the GloBE ETR calculation itself. Suggested action: request a deferred tax rollforward from the provision team.
> - Singapore has **no entity-level payroll** — payroll only exists at country level in HR. That blocks the substance carve-out.
> - The UK entity has **no tax jurisdiction recorded** — a master-data problem that blocks everything, owned by legal entity management, not tax.
>
> This converts a data audit into a **work allocation plan**. And it exports as CSV for the trackers everyone actually uses."

**Do:** Hover the download button; don't click.

### 5 · Tab "4 · Safe harbour triage" (~2 min)

**Do:** Click the tab. Walk the overview table top to bottom, then expand **Ireland**.

**Say:**
> "Now the audit committee's actual question. For each jurisdiction the copilot asks two things, in order: **can the three transitional safe harbour tests even be evaluated with the data on hand** — and only where they can, what's the indicative result?
>
> - Germany, the US: evaluable, and they'd likely pass on simplified ETR.
> - The Netherlands likely qualifies under **de minimis** — small enough to fall out.
> - **Ireland: all three tests evaluable, and it fails all three** — simplified ETR is 12% against a 17% threshold. That's the exposure headline.
> - **Singapore is the more interesting answer: 'we don't know, and here's why'** — income tax accrued is missing from the CbC report and payroll is missing at entity level. The honest answer is a data request, not a conclusion.
>
> Note the language: 'indicative', 'cannot evaluate'. This is readiness triage feeding tax technical review — it never pretends to be the adviser."

### 6 · Tab "5 · Readiness memo & export" (~1.5 min)

**Do:** Click the tab. Scroll the memo steadily — executive summary → owner-by-owner data requests → Appendix B.

**Say:**
> "Everything assembles into a workpaper-style memo: executive summary, blockers, data requests **grouped by owner** ready to send, open questions for technical review — and Appendix B, the full source-to-field mapping with confidences and approval status. That's the audit trail.
>
> Two exports: the memo, and a JSON audit package with the file hashes, every mapping decision, every gap, every test result. And notice the final package is **gated** — if any mapping were still awaiting review, this button would be disabled. Same control mindset as a real engagement file."

**AI note (say even with the toggle off):**
> "There's one AI toggle here: Claude can draft the memo narrative. It receives only the deterministic results, writes prose around them under a JSON schema, and is explicitly forbidden from changing a number. If it's unavailable, a deterministic draft renders instead — the demo never depends on it."

### 7 · Tab "📥 Use your own data" (~30 sec, or longer if asked)

**Do:** Click the tab, gesture at the file spec table and template buttons.

**Say:**
> "And it's not sample-bound. Switch off the sample, upload any CSV or Excel extracts — column names don't need to match anything, because the mapping review you just saw is the control point. This tab is the data request: five files, the grain and columns for each, and blank templates whose headers map automatically."

**If invited to prove it:** toggle off the sample in the sidebar, upload your pre-filled template, and walk Tab 2 → Tab 3 live (~2 extra minutes).

---

## The closing line

> "So: ingest the mess, map it with AI under review, get a defensible answer to 'are we ready' — and when the answer is no, get the exact request list, by owner, to make it yes. AI where it's strong: classification, explanation, drafting. Deterministic code where it must be: calculations, validations, audit trail. That's the operating model I think tax AI tooling needs."

---

## Q&A cheat sheet

**"Why not let the LLM do the analysis?"**
Tax conclusions need to be reproducible, explainable, and reviewable. LLMs are used for what they're good at — fuzzy classification and drafting — and everything that must survive audit scrutiny (scores, gaps, thresholds) is plain, tested Python. 25 automated tests, including an end-to-end run on the demo dataset.

**"What happens with a file you've never seen?"**
Every column gets profiled; the mapper suggests with confidence or honestly leaves it unmapped; the reviewer can map anything manually. Unknown data degrades to "needs review", never to a silent guess.

**"How does it scale beyond 6 entities?"**
Rules are vectorized over pandas — hundreds of entities is the same code path. The next layer would be persistence (multi-session review, remediation tracking) and the OECD GIR XML schema as a full field catalog.

**"Is the safe harbour logic complete?"**
Deliberately simplified: published transitional thresholds (de minimis €10m/€1m, simplified ETR 15/16/17% by year, SBIE transition percentages), labelled *indicative* throughout. The demo's value is the workflow shape — readiness triage before calculation — not rule coverage.

**"What about data security?"**
Demo runs on synthetic data. Uploads stay in the app session; files are hashed for traceability, not stored. In production this pattern would sit inside a firm's environment — the architecture has no external dependency unless the AI toggle is switched on.

**"Could this complement an existing Pillar Two platform?"**
That's the intent — it's the pre-calculation readiness layer. Platforms calculate; this proves the inputs exist, reconciles entities across systems, and runs the data chase with named owners.

**"How long did this take to build?"**
About a day with an AI pair: deterministic core first with tests, then UI, then the AI layer — same controlled-AI workflow the tool itself demonstrates.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Metrics don't match this script | Refresh the page (resets session state); confirm sample toggle ON |
| App asleep ("Zzzz" / wake-up screen) | Streamlit free tier sleeps after inactivity — click "Yes, get this app back up", takes ~1 min, do it **before** the audience arrives |
| Wifi fails | Run locally: `.venv/bin/streamlit run app.py` |
| AI toggle errors | Expected without an API key — it warns and falls back to the deterministic draft; that's a feature, narrate it |
| Numbers changed after a git push | The app auto-redeploys from `main`; re-verify the checklist numbers after any push |
