"""Narrate deterministic pipeline results as a staged "copilot analysis".

Everything here is presentation, not computation: by the time these
functions run, the engine has already profiled, scored, and matched.
They turn those results into the staged transcript the app streams while
a file is ingested — so the "thinking" the audience watches is the
deterministic engine explaining itself, line by line, with real numbers.
"""

from .column_mapper import AUTO_APPROVE_THRESHOLD

# Canonical source kinds the copilot expects for a Pillar Two readiness review.
SOURCE_KINDS = {
    "entity_master": "Entity master / legal entity register",
    "trial_balance": "Trial balance / consolidation extract",
    "tax_provision": "Tax provision extract",
    "cbcr_report": "CbC report (Table 1)",
    "jurisdiction_attributes": "Jurisdiction tax attributes",
    "other": "Unclassified source",
}

# The intake checklist shows these five, in this order.
EXPECTED_KINDS = [
    "entity_master",
    "trial_balance",
    "tax_provision",
    "cbcr_report",
    "jurisdiction_attributes",
]

_PROVISION_FIELDS = {
    "current_tax_expense", "deferred_tax_expense", "covered_taxes_adjustments",
    "tax_credits", "excluded_dividends",
}
_FINANCIAL_FIELDS = {
    "revenue", "profit_loss_before_tax", "payroll_costs", "tangible_asset_carrying_value",
}
_CBCR_FIELDS = {"cbcr_revenue", "cbcr_profit_before_tax", "cbcr_income_tax_accrued"}


def classify_source(file_mappings):
    """Classify one source file from the catalog fields its columns mapped to.

    Returns (kind_key, reason). Classification is over *suggested* fields so
    it works before the reviewer has approved anything.
    """
    fields = {m["suggested_field"] for m in file_mappings if m["suggested_field"]}
    if {"entity_id", "entity_name"} <= fields:
        return "entity_master", "it carries both entity identifiers and legal names"
    if fields & _CBCR_FIELDS:
        return "cbcr_report", "it carries jurisdiction-level CbCR aggregates"
    if "qdmtt_status" in fields:
        return "jurisdiction_attributes", "it carries jurisdiction-level tax regime attributes"
    if "entity_name" in fields and fields & _PROVISION_FIELDS:
        return "tax_provision", "it carries entity-level tax expense detail"
    if "entity_name" in fields and fields & _FINANCIAL_FIELDS:
        return "trial_balance", "it carries entity-level financial balances"
    return "other", "its columns did not match a known source pattern"


def narrate_file(fname, sheets, profiles, file_mappings, kind, kind_reason,
                 match_results=None, n_reference=0, source_hash=""):
    """Build the staged analysis transcript for one ingested file.

    sheets: list of (sheet_name, n_rows, n_cols)
    profiles / file_mappings: this file's column profiles and mapping records
    match_results: entity_matcher output for this file's names vs the master
        (None when there is no master yet, or the file is the master itself)
    Returns a list of {"label": str, "lines": [markdown str]} stages.
    """
    stages = []

    # -- stage 1: read --------------------------------------------------
    sheet_bits = ", ".join(f"**{name}** ({rows} rows × {cols} columns)" for name, rows, cols in sheets)
    lines = [f"Opened `{fname}` — {len(sheets)} sheet{'s' if len(sheets) != 1 else ''}: {sheet_bits}."]
    if source_hash:
        lines.append(f"Recorded SHA-256 `{source_hash}` so every downstream number traces back to this exact file.")
    stages.append({"label": "📄 Reading the file", "lines": lines})

    # -- stage 2: profile ------------------------------------------------
    lines = [f"Profiled {len(profiles)} columns: type, fill rate, sample values."]
    gappy = [p for p in profiles if p["fill_rate"] < 1.0]
    for p in gappy:
        missing = p["rows"] - p["non_null"]
        lines.append(
            f"⚠️ `{p['source_column']}` is only {p['fill_rate']:.0%} populated "
            f"({missing} of {p['rows']} rows blank) — noting that for the gap analysis."
        )
    if not gappy:
        lines.append("Every column is fully populated — no blanks to chase in this file.")
    stages.append({"label": "🔬 Profiling columns", "lines": lines})

    # -- stage 3: map ----------------------------------------------------
    lines = []
    auto, queued, unmapped = 0, 0, 0
    for m in file_mappings:
        col, field = m["source_column"], m["suggested_field"]
        if not field:
            unmapped += 1
            lines.append(f"🔴 `{col}` — no confident match in the Pillar Two catalog. Leaving it unmapped for the reviewer.")
        elif m["confidence"] >= AUTO_APPROVE_THRESHOLD:
            auto += 1
            lines.append(f"`{col}` → **{m['field_label']}** ({m['confidence']:.2f} — {_lc(m['note'])}). Pre-approved.")
        else:
            queued += 1
            lines.append(
                f"🟠 `{col}` → **{m['field_label']}**? ({m['confidence']:.2f} — {_lc(m['note'])}). "
                f"Below the {AUTO_APPROVE_THRESHOLD:.2f} auto-approve bar — queued for human review."
            )
    summary = f"{auto} of {len(file_mappings)} columns pre-approved at high confidence"
    if queued:
        summary += f"; {queued} waiting for the reviewer in the Mapping review tab"
    if unmapped:
        summary += f"; {unmapped} unmapped"
    lines.append(summary + ". Nothing is calculated from a mapping a human hasn't approved.")
    stages.append({"label": "🧭 Mapping columns to the Pillar Two catalog", "lines": lines})

    # -- stage 4: classify -----------------------------------------------
    lines = [f"This looks like the **{SOURCE_KINDS[kind]}** — {kind_reason}."]
    if kind == "entity_master":
        n_entities = next((rows for _, rows, _ in sheets), 0)
        lines.append(
            f"Treating it as the reference list: **{n_entities} legal entities**. "
            "Entity names in every other file will be reconciled against these."
        )
    stages.append({"label": "🗂️ Classifying the source", "lines": lines})

    # -- stage 5: reconcile entity names ----------------------------------
    if match_results is not None:
        lines = []
        exact = [r for r in match_results if r["status"] == "exact"]
        fuzzy = [r for r in match_results if r["status"] == "fuzzy"]
        unmatched = [r for r in match_results if r["status"] == "unmatched"]
        lines.append(
            f"Checked {len(match_results)} entity names against the {n_reference}-entity master: "
            f"{len(exact)} match exactly (after normalising legal-form suffixes like Ltd/Limited)."
        )
        for r in fuzzy:
            lines.append(
                f"🟠 `{r['candidate']}` is not in the master. Closest candidate: **{r['matched_to']}** "
                f"(similarity {r['score']:.2f}). Flagging it as a fuzzy match — "
                "the rows only merge once a reviewer confirms."
            )
        for r in unmatched:
            lines.append(
                f"🔴 `{r['candidate']}` matched nothing in the master (best similarity {r['score']:.2f}). "
                "Held out of the analysis until it is resolved."
            )
        if not fuzzy and not unmatched:
            lines.append("No exceptions — every name reconciled cleanly.")
        stages.append({"label": "🔗 Reconciling entity names across systems", "lines": lines})

    return stages


def _lc(note):
    """Lower-case the first character of a mapper note for mid-sentence use."""
    return note[:1].lower() + note[1:] if note else note
