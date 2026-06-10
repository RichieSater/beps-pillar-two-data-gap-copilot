import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from pillar_two_copilot.claude_client import claude_available, draft_memo_narrative
from pillar_two_copilot.column_mapper import suggest_mappings
from pillar_two_copilot.completeness import (
    assemble_datasets,
    find_gaps,
    gap_summary_by_jurisdiction,
    readiness_score,
)
from pillar_two_copilot.export import (
    build_audit_package,
    file_hash,
    gaps_to_csv_bytes,
    package_to_json_bytes,
)
from pillar_two_copilot.field_catalog import FIELD_CATALOG
from pillar_two_copilot.ingestion import load_tabular, profile_columns
from pillar_two_copilot.memo import build_fallback_narrative, memo_to_markdown
from pillar_two_copilot.safe_harbour import safe_harbour_triage

SAMPLE_DIR = ROOT / "data" / "sample_inputs"

st.set_page_config(page_title="Pillar Two Data Gap Copilot", page_icon="🌍", layout="wide")

# On Streamlit Cloud the API key lives in st.secrets; bridge it to the env var
# the Claude client reads. Local runs keep using a plain environment variable.
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["ANTHROPIC_API_KEY"])
except Exception:
    pass

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.2rem;}
      .hero {
        background: linear-gradient(135deg, #00338D 0%, #005EB8 55%, #6CACE4 100%);
        color: white; padding: 1.3rem 1.6rem; border-radius: 18px; margin-bottom: 1rem;
      }
      .hero h1 {margin: 0; font-size: 2.0rem;}
      .hero p {font-size: 1.0rem; max-width: 980px; margin-bottom: 0;}
      .draft-pill {
        display:inline-block; padding:.25rem .55rem; border-radius:999px;
        background:#fff3cd; color:#664d03; font-weight:700; font-size:.78rem;
      }
    </style>
    <div class="hero">
      <div class="draft-pill">CONTROLLED AI DEMO • NOT TAX ADVICE • TAX PROFESSIONAL REVIEW REQUIRED</div>
      <h1>Pillar Two Data Gap Copilot</h1>
      <p><b>Question it answers:</b> are we ready to calculate, run safe harbour tests, and file —
      and if not, exactly what data is missing, where does it live, and who do we ask?
      AI accelerates mapping and drafting; every score, gap, and test result is deterministic and traceable.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def severity_badge(sev):
    return {"high": "🔴 high", "medium": "🟠 medium", "low": "🟡 low"}.get(sev, sev)


with st.sidebar:
    st.header("Engagement setup")
    group_alias = st.text_input("Group alias", value="Aurora Global Group")
    fiscal_year = st.selectbox("Fiscal year", [2024, 2025, 2026], index=2)
    use_sample = st.toggle("Use synthetic Aurora sample files", value=True)
    uploads = st.file_uploader(
        "Upload source files (CSV / XLSX)", type=["csv", "xlsx", "xls"], accept_multiple_files=True
    )
    run_ai = st.toggle(
        "Draft memo narrative with Claude (if key available)",
        value=False,
        help="Requires ANTHROPIC_API_KEY. Claude drafts prose only; all numbers stay deterministic.",
    )
    st.caption(
        "Synthetic data only. Prototype demo: simplified field catalog, "
        "indicative transitional safe harbour thresholds, no full GloBE rules."
    )

# ---------------------------------------------------------------- ingest
sources = []  # (filename, raw_bytes)
if use_sample:
    for path in sorted(SAMPLE_DIR.iterdir()):
        if path.suffix.lower() in (".csv", ".xlsx", ".xls"):
            sources.append((path.name, path.read_bytes()))
if uploads:
    for up in uploads:
        sources.append((up.name, up.getvalue()))

if not sources:
    st.info(
        "Upload source files or enable the synthetic sample to begin. "
        "See the **Use your own data** tab for what to provide."
    )
    st.stop()

if use_sample and uploads:
    st.warning(
        "You are mixing the synthetic Aurora sample with your uploaded files. "
        "Turn off the sample toggle in the sidebar to analyse only your own data."
    )

frames, profiles, source_hashes, load_errors = {}, [], {}, []
for fname, raw in sources:
    source_hashes[fname] = file_hash(raw)
    try:
        for sheet, df in load_tabular(raw, filename=fname).items():
            frames[(fname, sheet)] = df
            profiles.extend(profile_columns(df, fname, sheet))
    except Exception as exc:
        load_errors.append(f"{fname}: {exc}")
if load_errors:
    st.warning(" • ".join(load_errors))
if not frames:
    st.error("No readable tabular data found.")
    st.stop()

# ---------------------------------------------------------------- mapping state
suggestions = suggest_mappings(profiles)
st.session_state.setdefault("mapping_overrides", {})


def mapping_key(m):
    return f"{m['source_file']}|{m['source_sheet']}|{m['source_column']}"


mappings = []
for m in suggestions:
    override = st.session_state["mapping_overrides"].get(mapping_key(m))
    record = dict(m)
    if override is not None:
        field = override.get("field", record["suggested_field"])
        record["suggested_field"] = field or None
        record["field_label"] = FIELD_CATALOG[field]["label"] if field else "(unmapped)"
        record["approved"] = override.get("approved", record["approved"])
        if override.get("manual"):
            record["note"] = "Manually mapped by reviewer"
            record["confidence"] = 1.0
    mappings.append(record)

# ---------------------------------------------------------------- assemble + analyse
reference_entities = None
for (fname, sheet), df in frames.items():
    cols = {
        m["source_column"]: m["suggested_field"]
        for m in mappings
        if m["source_file"] == fname and m["source_sheet"] == sheet and m["approved"]
    }
    name_cols = [c for c, f in cols.items() if f == "entity_name"]
    if name_cols and any(f == "entity_id" for f in cols.values()):
        reference_entities = df[name_cols[0]].dropna().tolist()  # entity master wins
        break

entity_df, jurisdiction_df, entity_matches = assemble_datasets(frames, mappings, reference_entities)
gaps = find_gaps(entity_df, jurisdiction_df)
score = readiness_score(gaps, entity_df, jurisdiction_df)
gap_summary = gap_summary_by_jurisdiction(gaps)
sh_results = safe_harbour_triage(entity_df, jurisdiction_df, fiscal_year)

high_gaps = [g for g in gaps if g["severity"] == "high"]
pending_review = [m for m in mappings if m["suggested_field"] and not m["approved"]]
fuzzy_matches = [m for m in entity_matches if m["status"] != "exact"]
unmatched = [m for m in entity_matches if m["status"] == "unmatched"]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Readiness score", f"{score:.0%}")
c2.metric("Data gaps", len(gaps), delta=f"-{len(high_gaps)} high severity", delta_color="inverse")
c3.metric("Entities", len(entity_df))
c4.metric("Jurisdictions", len(jurisdiction_df))
c5.metric("Mappings awaiting review", len(pending_review))

tabs = st.tabs(
    ["📖 Demo story", "1 · Source intake", "2 · Mapping review", "3 · Data gap dashboard",
     "4 · Safe harbour triage", "5 · Readiness memo & export", "📥 Use your own data"]
)

# ---------------------------------------------------------------- tab 0: story
with tabs[0]:
    st.subheader("Meet the demo client: Aurora Global Group")
    left, right = st.columns([1.25, 0.75])
    with left:
        st.markdown(
            """
**Aurora Global Group** is a fictional consumer-electronics multinational headquartered in the
United States, with consolidated revenue of roughly **€1.2bn** — comfortably above the
**€750m** threshold that pulls a group into Pillar Two.

Like most groups its size, Aurora grew by acquisition, and its data shows it:

- The **US parent** (Aurora US Inc) runs the group on SAP and owns the consolidation.
- An **Irish holding company** owns the European businesses and books most of the group's
  financing income — at an effective tax rate well below 15%.
- A **Singapore IP company** licenses technology to the operating entities. It is highly
  profitable, has almost no people or assets on the ground, and its payroll is tracked only
  in a country-level HR system.
- **German and Dutch operating companies** manufacture and distribute; the Dutch entity is
  small and may fall out of scope under the de minimis rules.
- A **UK services company** was acquired eighteen months ago and still is not fully set up
  in the legal-entity master — nobody has recorded its tax jurisdiction.

**The trigger:** Aurora's Head of Tax has been asked by the audit committee whether the group
can rely on the transitional CbCR safe harbours — and if not, what the top-up tax exposure is.
Before anyone can answer, the tax team needs to assemble entity-level data from **four systems
that don't agree with each other**: the legal-entity register, the SAP trial balance, the tax
provision tool, and the CbC report prepared by a different team.

**What this copilot does for them:** ingests those messy extracts, maps every column to a
Pillar Two data model (with a reviewer approving each mapping), reports exactly which data is
missing, who owns it, and what to request — and triages which safe harbour tests can even be
evaluated today.
            """
        )
    with right:
        st.markdown("**The problems planted in Aurora's data** (all real-world patterns):")
        st.dataframe(
            pd.DataFrame(
                [
                    ["Entity names disagree across systems", "'…Ltd' vs '…Limited', plus a typo in the TB"],
                    ["Missing jurisdiction", "UK entity never set up in the entity master"],
                    ["No entity-level deferred tax", "Ireland — blocks the GloBE ETR calculation"],
                    ["Payroll at country level only", "Singapore — blocks the SBIE / routine profits test"],
                    ["Missing tangible asset value", "Netherlands trial balance"],
                    ["Blended tax adjustment line", "'TaxExpAdj' needs disaggregation"],
                    ["CbCR missing income tax accrued", "Singapore — blocks the simplified ETR test"],
                    ["A field nobody provided", "Excluded dividends — absent from every file"],
                ],
                columns=["Planted problem", "Where it shows up"],
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Aurora Global Group is entirely synthetic: every entity, number, and name was "
            "generated for this demo and any resemblance to a real company is coincidental."
        )

# ---------------------------------------------------------------- tab 1
with tabs[1]:
    st.subheader("Detected files, sheets and column profiles")
    st.caption("Every downstream number traces back to a file / sheet / column captured here (with SHA-256 hash).")
    hash_df = pd.DataFrame(
        [{"File": f, "SHA-256 (prefix)": h} for f, h in source_hashes.items()]
    )
    st.dataframe(hash_df, hide_index=True, width="stretch")
    profile_df = pd.DataFrame(profiles)
    profile_df["sample_values"] = profile_df["sample_values"].map(lambda v: ", ".join(v))
    st.dataframe(profile_df, hide_index=True, width="stretch", height=380)

    if fuzzy_matches or unmatched:
        st.subheader("Entity name reconciliation")
        st.caption("Names rarely match across ERP / provision / legal-entity systems — fuzzy matches need a reviewer's eye.")
        st.dataframe(pd.DataFrame(entity_matches), hide_index=True, width="stretch")

# ---------------------------------------------------------------- tab 2
with tabs[2]:
    st.subheader("AI-suggested mappings — reviewer approves, mappings drive everything downstream")
    st.caption(
        "Heuristic engine scores each source column against the Pillar Two field catalog. "
        "High-confidence matches are pre-approved; anything else waits for you."
    )
    field_options = [""] + list(FIELD_CATALOG.keys())
    for m in mappings:
        key = mapping_key(m)
        cols = st.columns([2.2, 2.2, 1.0, 2.4, 0.9])
        cols[0].markdown(f"**{m['source_column']}**  \n`{m['source_file']}` / {m['source_sheet']}")
        current = m["suggested_field"] or ""
        chosen = cols[1].selectbox(
            "Pillar Two field", field_options,
            index=field_options.index(current) if current in field_options else 0,
            key=f"field_{key}", label_visibility="collapsed",
            format_func=lambda f: FIELD_CATALOG[f]["label"] if f else "(unmapped)",
        )
        cols[2].markdown(f"conf **{m['confidence']:.2f}**")
        cols[3].caption(m["note"])
        approved = cols[4].checkbox("approve", value=m["approved"], key=f"appr_{key}")
        if chosen != current or approved != m["approved"]:
            st.session_state["mapping_overrides"][key] = {
                "field": chosen or None,
                "approved": approved and bool(chosen),
                "manual": chosen != (m["suggested_field"] or "") and bool(chosen),
            }
            st.rerun()

# ---------------------------------------------------------------- tab 3
with tabs[3]:
    st.subheader("Missing data by entity and jurisdiction")
    if not gaps:
        st.success("No gaps against the simplified field catalog.")
    else:
        left, right = st.columns([1.1, 0.9])
        with left:
            gaps_df = pd.DataFrame(gaps)
            gaps_df["severity"] = gaps_df["severity"].map(severity_badge)
            st.dataframe(
                gaps_df[["jurisdiction", "entity", "field_label", "severity", "blocks",
                         "likely_owner", "suggested_action", "reason"]],
                hide_index=True, width="stretch", height=430,
            )
        with right:
            summary_df = pd.DataFrame(gap_summary)
            fig = px.bar(
                summary_df.melt(id_vars="jurisdiction", value_vars=["high", "medium", "low"],
                                var_name="severity", value_name="gaps"),
                x="jurisdiction", y="gaps", color="severity",
                color_discrete_map={"high": "#d62728", "medium": "#ff7f0e", "low": "#ffd700"},
                title="Gaps by jurisdiction and severity",
            )
            st.plotly_chart(fig, use_container_width=True)
        st.download_button(
            "Download data gap register (CSV)", gaps_to_csv_bytes(gaps),
            file_name="data_gap_register.csv", mime="text/csv",
        )

# ---------------------------------------------------------------- tab 4
with tabs[4]:
    st.subheader(f"Transitional CbCR safe harbour readiness — FY{fiscal_year}")
    st.caption(
        "Readiness triage, not advice: can each test be evaluated with the data on hand, "
        "and where it can, what is the indicative result? Every result requires tax technical review."
    )
    overview = pd.DataFrame(
        [{
            "Jurisdiction": r["jurisdiction"],
            "Can evaluate?": r["can_evaluate"],
            "Indicative passes": ", ".join(r["indicative_passes"]) or "—",
            "Missing items": "; ".join(r["missing_items"]) or "—",
        } for r in sh_results]
    )
    st.dataframe(overview, hide_index=True, width="stretch")
    for r in sh_results:
        with st.expander(f"{r['jurisdiction']} — detail"):
            st.dataframe(
                pd.DataFrame([
                    {"Test": t["test"], "Status": t["status"],
                     "Detail": t.get("detail", ""), "Missing": "; ".join(t["missing"])}
                    for t in r["tests"]
                ]),
                hide_index=True, width="stretch",
            )

# ---------------------------------------------------------------- tab 5
with tabs[5]:
    st.subheader("Workpaper-style readiness memo")
    narrative_source = "Deterministic draft"
    if run_ai:
        if not claude_available():
            st.warning("ANTHROPIC_API_KEY not set (or anthropic not installed) — using deterministic draft.")
            narrative = build_fallback_narrative(score, gaps, sh_results)
        else:
            try:
                with st.spinner("Claude is drafting the narrative…"):
                    narrative = draft_memo_narrative({
                        "group_alias": group_alias,
                        "fiscal_year": fiscal_year,
                        "readiness_score": score,
                        "gap_summary": gap_summary,
                        "gaps": gaps,
                        "entity_match_exceptions": fuzzy_matches + unmatched,
                        "safe_harbour": [
                            {k: v for k, v in r.items() if k != "tests"} for r in sh_results
                        ],
                    })
                narrative_source = "Claude draft (claude-opus-4-8) — deterministic numbers"
            except Exception as exc:
                st.warning(f"Claude unavailable ({exc}) — using deterministic draft.")
                narrative = build_fallback_narrative(score, gaps, sh_results)
    else:
        narrative = build_fallback_narrative(score, gaps, sh_results)

    memo_md = memo_to_markdown(
        narrative, score, gaps, gap_summary, sh_results, mappings,
        group_alias, fiscal_year, narrative_source,
    )
    st.markdown(memo_md)

    st.divider()
    blocking = bool(pending_review) or bool(unmatched)
    if blocking:
        st.warning(
            "Final audit package is blocked until all suggested mappings are approved/rejected "
            "and unmatched entities are resolved. Draft memo and gap register remain available."
        )
    else:
        st.success("Review gates satisfied: mappings dispositioned and entities reconciled.")
    package = build_audit_package(
        source_hashes, mappings, entity_matches, gaps, gap_summary, score,
        sh_results, narrative, narrative_source, group_alias, fiscal_year,
    )
    d1, d2 = st.columns(2)
    d1.download_button(
        "Download readiness memo (Markdown)", memo_md.encode("utf-8"),
        file_name="pillar_two_readiness_memo.md", mime="text/markdown",
    )
    d2.download_button(
        "Download final audit package (JSON)", package_to_json_bytes(package),
        file_name="pillar_two_audit_package.json", mime="application/json",
        disabled=blocking,
    )

# ---------------------------------------------------------------- tab 6: bring your own data
with tabs[6]:
    st.subheader("Running the copilot on your own data")
    st.markdown(
        """
The app accepts **CSV and Excel (`.xlsx`/`.xls`)** files — multi-sheet workbooks are fine,
every sheet is profiled separately. Column names do **not** need to match anything exactly:
the mapper suggests a Pillar Two field for each column and you confirm or fix the mapping in
**Tab 2** before anything is calculated.

**How to use it with real extracts:**

1. Turn **off** the *"Use synthetic Aurora sample files"* toggle in the sidebar.
2. Upload your files (as many as you like).
3. Review the suggested mappings in Tab 2 — approve, remap, or reject each column.
4. Read the gaps, safe harbour triage, and memo in Tabs 3–5.

**What data to provide** (more is better, but the app degrades gracefully — anything missing
simply shows up as a gap with a remediation request):
        """
    )
    spec_df = pd.DataFrame(
        [
            ["Entity master / legal entity register", "Recommended first", "One row per legal entity",
             "Entity ID, entity name, tax jurisdiction, ownership %, consolidation method"],
            ["Trial balance or consolidation extract", "Recommended", "One row per entity",
             "Entity name, revenue, profit/loss before tax, payroll costs, tangible asset carrying value"],
            ["Tax provision extract", "Recommended", "One row per entity",
             "Entity name, current tax expense, deferred tax expense, covered-tax adjustments, tax credits, excluded dividends"],
            ["CbC report (Table 1)", "Needed for safe harbour triage", "One row per jurisdiction",
             "Jurisdiction, revenues, profit/loss before income tax, income tax accrued (current year)"],
            ["Jurisdiction attributes", "Optional", "One row per jurisdiction",
             "Jurisdiction, QDMTT / IIR / UTPR enactment status"],
        ],
        columns=["File", "Priority", "Grain", "Columns the catalog looks for"],
    )
    st.dataframe(spec_df, hide_index=True, width="stretch")

    st.markdown(
        """
**Practical notes**

- The file that contains **both an entity ID and entity names** is treated as the entity
  master; entity names in every other file are reconciled to it (suffix-aware fuzzy matching,
  so *"Ltd"* vs *"Limited"* is handled — genuine typos are flagged for review in Tab 1).
- Use **one currency basis** across files (the demo assumes EUR); the app does not translate.
- Jurisdiction names must be **spelled consistently** between entity-level and
  jurisdiction-level files ("United Kingdom" in both, not "UK" in one).
- Amounts should be plain numbers (no thousands separators stored as text).
- Files never leave the app session; each upload is SHA-256-hashed for the audit trail.

**Blank templates** — fastest path if you'd rather request data in a clean shape:
        """
    )
    templates = {
        "entity_master_template.csv": (
            "Entity_ID,Entity_Name,Jurisdiction,Ownership_Pct,Consolidation_Method\n"
            "E001,Example HoldCo Ltd,Ireland,100,Full\n"
        ),
        "trial_balance_template.csv": (
            "Entity_Name,Revenue,Profit_Before_Tax,Payroll_Costs,Tangible_Assets\n"
            "Example HoldCo Ltd,100000000,12000000,5000000,8000000\n"
        ),
        "tax_provision_template.csv": (
            "Entity_Name,Current_Tax_Expense,Deferred_Tax_Expense,Covered_Taxes_Adjustments,"
            "Excluded_Dividends,Tax_Credits\n"
            "Example HoldCo Ltd,1500000,200000,0,0,0\n"
        ),
        "cbcr_template.csv": (
            "Tax_Jurisdiction,CbCR_Revenue,Profit_Loss_Before_Income_Tax,Income_Tax_Accrued\n"
            "Ireland,100000000,12000000,1500000\n"
        ),
        "jurisdiction_attributes_template.csv": (
            "Jurisdiction,QDMTT_Status\nIreland,Yes\n"
        ),
    }
    cols = st.columns(len(templates))
    for col, (fname, content) in zip(cols, templates.items()):
        col.download_button(
            fname.replace("_template.csv", "").replace("_", " "),
            content.encode("utf-8"),
            file_name=fname,
            mime="text/csv",
            key=f"tpl_{fname}",
        )
    st.caption(
        "Template headers map automatically at high confidence, but any reasonable naming "
        "works — the mapping review in Tab 2 is the control point."
    )
