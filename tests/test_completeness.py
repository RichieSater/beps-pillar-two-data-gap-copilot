import pandas as pd

from pillar_two_copilot.completeness import (
    assemble_datasets,
    find_gaps,
    gap_summary_by_jurisdiction,
    readiness_score,
)


def _mapping(source_file, column, field, approved=True):
    return {
        "source_file": source_file, "source_sheet": "data", "source_column": column,
        "suggested_field": field, "field_label": field, "confidence": 0.95,
        "note": "", "approved": approved,
    }


def _frames():
    master = pd.DataFrame({
        "Name": ["Alpha GmbH", "Beta BV"],
        "Country": ["Germany", None],
    })
    tb = pd.DataFrame({
        "Entity": ["Alpha GmbH", "Beta B.V."],
        "PBT": [100.0, None],
    })
    cbcr = pd.DataFrame({"Jur": ["Germany"], "Revenues": [1000.0]})
    return {
        ("master.csv", "data"): master,
        ("tb.csv", "data"): tb,
        ("cbcr.csv", "data"): cbcr,
    }


MAPPINGS = [
    _mapping("master.csv", "Name", "entity_name"),
    _mapping("master.csv", "Country", "jurisdiction"),
    _mapping("tb.csv", "Entity", "entity_name"),
    _mapping("tb.csv", "PBT", "profit_loss_before_tax"),
    _mapping("cbcr.csv", "Jur", "jurisdiction"),
    _mapping("cbcr.csv", "Revenues", "cbcr_revenue"),
]


def test_assemble_merges_entity_frames_on_reconciled_names():
    entity_df, jurisdiction_df, matches = assemble_datasets(
        _frames(), MAPPINGS, ["Alpha GmbH", "Beta BV"]
    )
    assert len(entity_df) == 2
    alpha = entity_df[entity_df["entity_name"] == "Alpha GmbH"].iloc[0]
    assert alpha["profit_loss_before_tax"] == 100.0
    assert list(jurisdiction_df["jurisdiction"]) == ["Germany"]
    # "Beta B.V." reconciles to "Beta BV"
    assert any(m["candidate"] == "Beta B.V." and m["matched_to"] == "Beta BV" for m in matches)


def test_unapproved_mapping_is_ignored():
    mappings = [m.copy() for m in MAPPINGS]
    for m in mappings:
        if m["source_column"] == "PBT":
            m["approved"] = False
    entity_df, _, _ = assemble_datasets(_frames(), mappings, ["Alpha GmbH", "Beta BV"])
    assert "profit_loss_before_tax" not in entity_df.columns


def test_find_gaps_distinguishes_missing_field_and_missing_value():
    entity_df, jurisdiction_df, _ = assemble_datasets(_frames(), MAPPINGS, ["Alpha GmbH", "Beta BV"])
    gaps = find_gaps(entity_df, jurisdiction_df)
    by_key = {(g["entity"], g["field"]): g for g in gaps}
    # Beta has a null PBT -> missing value
    assert "Value missing" in by_key[("Beta BV", "profit_loss_before_tax")]["reason"]
    # revenue never provided anywhere -> missing field for both entities
    assert "not present" in by_key[("Alpha GmbH", "revenue")]["reason"]
    # Beta's missing jurisdiction lands under "(unassigned)"
    assert by_key[("Beta BV", "profit_loss_before_tax")]["jurisdiction"] == "(unassigned)"


def test_readiness_score_and_summary():
    entity_df, jurisdiction_df, _ = assemble_datasets(_frames(), MAPPINGS, ["Alpha GmbH", "Beta BV"])
    gaps = find_gaps(entity_df, jurisdiction_df)
    score = readiness_score(gaps, entity_df, jurisdiction_df)
    assert 0.0 <= score < 1.0
    summary = gap_summary_by_jurisdiction(gaps)
    assert all(row["total"] == row["high"] + row["medium"] + row["low"] for row in summary)


def test_perfect_data_scores_one():
    entity_df = pd.DataFrame([{k: "x" for k in [
        "entity_name", "entity_id", "jurisdiction", "ownership_percentage",
        "consolidation_method", "revenue", "profit_loss_before_tax",
        "current_tax_expense", "deferred_tax_expense", "covered_taxes_adjustments",
        "excluded_dividends", "payroll_costs", "tangible_asset_carrying_value", "tax_credits",
    ]}])
    jurisdiction_df = pd.DataFrame([{
        "jurisdiction": "Germany", "cbcr_revenue": 1.0,
        "cbcr_profit_before_tax": 1.0, "cbcr_income_tax_accrued": 1.0, "qdmtt_status": "Yes",
    }])
    gaps = find_gaps(entity_df, jurisdiction_df)
    assert gaps == []
    assert readiness_score(gaps, entity_df, jurisdiction_df) == 1.0
