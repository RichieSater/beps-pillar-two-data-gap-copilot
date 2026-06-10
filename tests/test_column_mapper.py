from pillar_two_copilot.column_mapper import normalize, score_column, suggest_mappings


def test_normalize_handles_camelcase_and_punctuation():
    assert normalize("TaxExpAdj") == "tax exp adj"
    assert normalize("PBT_Local") == "pbt local"
    assert normalize("Profit/Loss Before Tax") == "profit loss before tax"


def test_exact_synonym_match_scores_high():
    field, confidence, _ = score_column("Rev_Total")
    assert field == "revenue"
    assert confidence >= 0.9


def test_cbcr_columns_map_to_jurisdiction_fields():
    assert score_column("Revenues")[0] == "cbcr_revenue"
    assert score_column("Income_Tax_Accrued")[0] == "cbcr_income_tax_accrued"
    assert score_column("Profit_Loss_Before_Income_Tax")[0] == "cbcr_profit_before_tax"


def test_unknown_column_left_unmapped():
    profiles = [{
        "source_file": "x.csv", "source_sheet": "data",
        "source_column": "Zebra_Quotient", "dtype": "float64",
        "rows": 1, "non_null": 1, "fill_rate": 1.0, "sample_values": [],
    }]
    (suggestion,) = suggest_mappings(profiles)
    assert suggestion["suggested_field"] is None
    assert suggestion["approved"] is False


def test_mid_confidence_suggestion_not_auto_approved():
    field, confidence, _ = score_column("Tangible_Assets_NBV")
    assert field == "tangible_asset_carrying_value"
    assert confidence < 0.9  # suggested but needs reviewer approval check
