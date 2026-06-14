# Demo Script — Pillar Two Data Gap Copilot

**Audience:** generic / any Big 4 viewer. The tailored, named recording script lives outside the repo in `~/dev/_demo-prep/`.

Presenter walkthrough for the live app. Target length: **8–10 minutes** plus Q&A.
Live app: **https://pillar-two-data-gap-copilot.streamlit.app** • Repo: **https://github.com/RichieSater/beps-pillar-two-data-gap-copilot**

**The shape of this demo changed:** the app now starts **empty**. You drag the five Atlas
files in yourself, live, and the copilot visibly analyses each one as it lands — streaming
its findings line by line. The audience watches the work happen instead of being told it
already did. Every number it streams is real engine output; the animation is pacing, not
fiction (and there's a Q&A answer for exactly that question below).

---

## Before the demo (5-minute checklist)

- [ ] In the app sidebar, click **"⬇️ Atlas demo file pack (ZIP)"**, unzip it, and leave the
  folder open in Finder, arranged so you can drag files onto the browser without hunting.
  File order matters for the story: `entity_master.csv` → `trial_balance_by_entity.xlsx` →
  `tax_provision_extract.csv` → `cbcr_report.csv` → `jurisdiction_tax_attributes.csv`.
- [ ] Click **"🔄 Reset session"** in the sidebar right before you start — no leftover state
  from rehearsal. The intake checklist on the right should show five empty boxes.
- [ ] Confirm the sidebar shows **"Draft memo narrative with Claude" OFF** (deterministic
  mode — zero dependency on an API key mid-demo) and **"Animate copilot analysis" ON**.
- [ ] Rehearsal tip: flip **Animate OFF** to step through instantly; flip it back ON before
  the real thing.
- [ ] After all five files are in, the metric tiles must read:
  **Readiness 87% · Data gaps 15 · Entities 6 · Jurisdictions 6 · Mappings awaiting review 0**.
  If they do, everything downstream matches this script.
- [ ] **No-files fallback** (presenting from a machine without the ZIP): the sidebar
  **"📂 Stage next"** button feeds the same five files through the same live analysis, one
  click per file. Identical show, no drag-and-drop.
- [ ] **Offline fallback** (if the venue wifi dies):
  ```bash
  cd ~/dev/beps-pillar-two-data-gap-copilot
  .venv/bin/streamlit run app.py
  ```
  Identical app on localhost:8501.

---

## The 30-second opener (app empty, 📖 Demo story tab showing)

> "Every Pillar Two engine — every Big 4 platform, every in-house build — assumes the data is
> already there. In practice, the hardest question a tax team faces is earlier: **do we even
> have the data to calculate, run safe harbour tests, and file — and if not, what exactly is
> missing, where does it live, and who do we ask?**
>
> This is a copilot for that question. AI accelerates the boring parts — mapping messy
> columns, drafting the memo — but every score, every gap, every test result is deterministic,
> traceable, and gated behind human review. The app is empty right now. Let me feed it a
> realistic mess, one file at a time."

**While still on the 📖 Demo story tab** (~45 sec):
> "The client here is Atlas Components Group — the same name that ran through the screening and
> portfolio-monitoring demos. It's a synthetic $4.8bn U.S.-parented industrial-electronics group I built
> to behave like a real Pillar Two engagement: a low-tax Irish holding company, a Singapore IP hub with profit but no
> people, a UK acquisition that never got fully onboarded, and four source systems that don't agree
> with each other. The data is invented; every problem in it is one you'd recognize from a real client."

---

## Act 1 — Feed it the files (~3 min, the heart of the demo)

### File 1: `entity_master.csv`

**Do:** Drag it onto the **Source intake** drop zone. The copilot analysis panel appears and
streams. **Don't talk over all of it — let the first lines land in silence**, then narrate:

> "Watch what it's doing: profiling every column, hashing the file for the audit trail —
> and it already caught something: *Country_of_Residence* is only 83% populated. One entity
> has no tax jurisdiction recorded. Hold that thought.
>
> It mapped all five columns to the Pillar Two catalog with the reasoning shown — exact
> synonym matches at 0.95 — and classified the file: this is the **entity master**, so these
> six entities become the reference list everything else reconciles against."

**Point at the checklist on the right:** first box ticked, four to go.

### File 2: `trial_balance_by_entity.xlsx`

**Do:** Drag it in. This one has the money moment — the streaming reconciliation stage:

> "A real Excel trial balance this time. Same routine — profile, hash, map… and now it's
> cross-checking entity names against the master it just built. Five of six match. But look:
> *'Atlas UK **Service** Ltd'* — singular — isn't in the master. Closest candidate at 97%
> similarity. That's a typo in the trial balance, and instead of silently merging, it
> **flags it for a human to confirm**. That's the design philosophy of the entire tool:
> the AI notices, the reviewer decides."

### Files 3–5: `tax_provision_extract.csv`, `cbcr_report.csv`, `jurisdiction_tax_attributes.csv`

**Do:** Drag all three in together. Three analysis panels run in sequence. Narrate selectively:

> "Provision extract — reconciles cleanly. CbC report — see that red line: an *Employees*
> column it refuses to guess at; it stays unmapped until a reviewer maps it. And it caught
> that income tax accrued is blank for one jurisdiction — that one will come back to haunt
> Singapore in the safe harbour tests.
>
> Five files, four source systems, and now look at the top: **six entities, six jurisdictions,
> fifteen gaps, 87% data-ready.** Now I'll show you where that number comes from."

*(Checklist: all five boxes ticked. Tiles: 87% / 15 / 6 / 6 / 0.)*

---

## Act 2 — Tab-by-tab walkthrough

### Tab "1 · Source intake" (~45 sec)

**Do:** Click the tab. The analysis transcripts you just watched are preserved as expanders;
below them, the column profiles, hashes, and the entity reconciliation table.

**Say:**
> "Everything it streamed is kept as a transcript — this is workpaper evidence, not theater.
> Every column profiled, every file hashed, and the UK typo sitting in the reconciliation
> table waiting for review."

### Tab "2 · Mapping review" (~2 min) — the control point

**Do:** Click the tab. Scroll slowly; pause on `TaxExpAdj`, `Tangible_Assets_NBV`, and `Employees`.

**Say:**
> "This is where AI meets control. Every suggestion you watched stream past lands here with
> its confidence and its reasoning — and nothing flows into any calculation until it's
> approved on this screen. 'PBT_Local', exact match, 0.95, pre-approved. 'Employees' — no
> confident match, left unmapped rather than guessed."

**Interactive beat (the money moment):** Untick the **approve** checkbox on `DTA_Movement`
(the deferred tax column).

> "Watch the top of the screen — I just rejected one mapping…"

*(The app reruns: readiness drops, gap count jumps, because deferred tax now reads as missing
for every entity.)*

> "…and the readiness score and gap register recalculated instantly. The reviewer's decision
> **is** the pipeline."

**Do:** Re-tick the checkbox. Confirm the tiles return to **87% / 15**.

### Tab "3 · Data gap dashboard" (~2 min) — the headline

**Do:** Click the tab. Point at the table rows, then the severity chart.

**Say:**
> "Here's the answer to 'what's missing'. Not a list of nulls — every gap says **what it
> blocks, who likely owns it, and the exact request to send**:
>
> - Ireland is missing entity-level **deferred tax** — high severity because it blocks the
>   GloBE ETR calculation itself. Suggested action: request a deferred tax rollforward from
>   the provision team.
> - Singapore has **no entity-level payroll** — payroll only exists at country level in HR.
>   That blocks the substance carve-out.
> - The UK entity has **no tax jurisdiction recorded** — remember the 83% fill rate the
>   copilot flagged on the very first file? This is that, priced: a master-data problem that
>   blocks everything, owned by legal entity management, not tax.
>
> This converts a data audit into a **work allocation plan**. And it exports as CSV for the
> trackers everyone actually uses."

**Do:** Hover the download button; don't click.

### Tab "4 · Safe harbour triage" (~2 min)

**Do:** Click the tab. Walk the overview table top to bottom, then expand **Ireland**.

**Say:**
> "Now the audit committee's actual question. For each jurisdiction the copilot asks two
> things, in order: **can the three transitional safe harbour tests even be evaluated with
> the data on hand** — and only where they can, what's the indicative result?
>
> - Germany, the US: evaluable, and they'd likely pass on simplified ETR.
> - The Netherlands likely qualifies under **de minimis** — small enough to fall out.
> - **Ireland: all three tests evaluable, and it fails all three** — simplified ETR is 12%
>   against a 17% threshold. That's the exposure headline.
> - **Singapore is the more interesting answer: 'we don't know, and here's why'** — the blank
>   income tax accrued the copilot flagged during intake, plus the missing entity-level
>   payroll. The honest answer is a data request, not a conclusion.
>
> Note the language: 'indicative', 'cannot evaluate'. This is readiness triage feeding tax
> technical review — it never pretends to be the adviser."

### Tab "5 · Readiness memo & export" (~1.5 min)

**Do:** Click the tab. The memo does **not** pre-exist — click **"✍️ Draft readiness memo"**
and let the executive summary stream onto the screen.

**Say (while it streams):**
> "Last step: the memo drafts itself from the deterministic results — executive summary,
> blockers, data requests **grouped by owner** ready to send, open questions for technical
> review — and Appendix B, the full source-to-field mapping with confidences and approval
> status. That's the audit trail.
>
> Two exports: the memo, and a JSON audit package with the file hashes, every mapping
> decision, every gap, every test result. And the final package is **gated** — if any mapping
> were still awaiting review, that button would be disabled. Same control mindset as a real
> engagement file."

**AI note (say even with the toggle off):**
> "There's one AI toggle here: Claude can draft the memo narrative. It receives only the
> deterministic results, writes prose around them under a JSON schema, and is explicitly
> forbidden from changing a number. If it's unavailable, a deterministic draft renders
> instead — the demo never depends on it."

### Tab "📥 Use your own data" (~30 sec, or longer if asked)

**Do:** Click the tab, gesture at the file spec table and template buttons.

**Say:**
> "And nothing you watched was sample-bound. The intake zone takes any CSV or Excel extract —
> column names don't need to match anything, because the mapping review you just saw is the
> control point. This tab is the data request: five files, the grain and columns for each,
> and blank templates whose headers map automatically."

**If invited to prove it:** drop a pre-filled template into the intake zone and let the
analysis stream on *their* shape of data (~2 extra minutes).

---

## The closing line

> "So: ingest the mess — live, file by file — map it with AI under review, get a defensible
> answer to 'are we ready', and when the answer is no, get the exact request list, by owner,
> to make it yes. AI where it's strong: classification, explanation, drafting. Deterministic
> code where it must be: calculations, validations, audit trail. That's the operating model
> I think tax AI tooling needs."

---

## Q&A cheat sheet

**"Was that streaming analysis actually the AI thinking?"**
It's the deterministic engine narrating its real results — every number, confidence, and
match score in the stream is genuine pipeline output; only the pacing is presentational.
That's deliberate and it's the point: an auditable system should be able to *show its work*
in plain language. Flip "Animate copilot analysis" off in the sidebar and you get identical
results instantly — the transcript in Tab 1 is the same either way. (The optional Claude
layer drafts memo prose only.)

**"Why not let the LLM do the analysis?"**
Tax conclusions need to be reproducible, explainable, and reviewable. LLMs are used for what
they're good at — fuzzy classification and drafting — and everything that must survive audit
scrutiny (scores, gaps, thresholds) is plain, tested Python. 33 automated tests, including an
end-to-end run on the demo dataset.

**"What happens with a file you've never seen?"**
Every column gets profiled; the mapper suggests with confidence or honestly leaves it
unmapped; the reviewer can map anything manually. Unknown data degrades to "needs review",
never to a silent guess.

**"How does it scale beyond 6 entities?"**
Rules are vectorized over pandas — hundreds of entities is the same code path. The next layer
would be persistence (multi-session review, remediation tracking) and the OECD GIR XML schema
as a full field catalog.

**"Is the safe harbour logic complete?"**
Deliberately simplified: published transitional thresholds (de minimis $10m/$1m — OECD states
these in EUR; the demo runs single-currency USD with no FX — simplified ETR 15/16/17% by year,
SBIE transition percentages), labelled *indicative* throughout. The
demo's value is the workflow shape — readiness triage before calculation — not rule coverage.

**"What about data security?"**
Demo runs on synthetic data. Uploads stay in the app session; files are hashed for
traceability, not stored. In production this pattern would sit inside a firm's environment —
the architecture has no external dependency unless the AI toggle is switched on.

**"Could this complement an existing Pillar Two platform?"**
That's the intent — it's the pre-calculation readiness layer. Platforms calculate; this
proves the inputs exist, reconciles entities across systems, and runs the data chase with
named owners.

**"How long did this take to build?"**
About a day with an AI pair: deterministic core first with tests, then UI, then the AI
layer — same controlled-AI workflow the tool itself demonstrates.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Metrics don't match this script after all 5 files | Sidebar **Reset session**, re-drag the files (or **Stage next** ×5) |
| Dragged a file and nothing streamed | It was already analysed this session (same name). Reset session to replay |
| Animation feels too slow for the room | Sidebar: turn **Animate copilot analysis** off — same results, instant |
| Don't have the Atlas files on this machine | Sidebar **📂 Stage next** button, five times — same live analysis |
| App asleep ("Zzzz" / wake-up screen) | Streamlit free tier sleeps after inactivity — click "Yes, get this app back up", takes ~1 min, do it **before** the audience arrives |
| Wifi fails | Run locally: `.venv/bin/streamlit run app.py` |
| AI toggle errors | Expected without an API key — it warns and falls back to the deterministic draft; that's a feature, narrate it |
| Numbers changed after a git push | The app auto-redeploys from `main`; re-verify the checklist numbers after any push |
