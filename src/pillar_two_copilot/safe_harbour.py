"""Transitional CbCR safe harbour readiness triage.

This is a *readiness* check, not tax advice: for each jurisdiction we
determine (a) whether the data needed for each test exists, and (b) where
it does, an indicative pass/fail using the published transitional
thresholds. Anything indicative is labelled as such and routed to tax
technical review.
"""

import pandas as pd

# Transitional CbCR safe harbour parameters (OECD, Dec 2022 guidance).
DE_MINIMIS_REVENUE = 10_000_000  # EUR
DE_MINIMIS_PROFIT = 1_000_000  # EUR
SIMPLIFIED_ETR_RATE = {2023: 0.15, 2024: 0.15, 2025: 0.16, 2026: 0.17}
# Transitional SBIE percentages step down annually; demo uses FY2026 values.
SBIE_PAYROLL_PCT = 0.094
SBIE_ASSET_PCT = 0.074


def _num(value):
    return None if value is None or pd.isna(value) else float(value)


def evaluate_jurisdiction(jur_row, entity_rows, fiscal_year=2026):
    """Evaluate the three transitional safe harbour tests for one jurisdiction.

    jur_row: dict-like with cbcr_revenue / cbcr_profit_before_tax /
        cbcr_income_tax_accrued (jurisdiction-level CbCR data).
    entity_rows: DataFrame slice of entities in this jurisdiction (SBIE inputs).
    """
    revenue = _num(jur_row.get("cbcr_revenue"))
    pbt = _num(jur_row.get("cbcr_profit_before_tax"))
    tax_accrued = _num(jur_row.get("cbcr_income_tax_accrued"))

    tests = []

    # 1. De minimis: revenue < EUR 10m AND PBT < EUR 1m
    missing = [m for m, v in [("CbCR revenue", revenue), ("CbCR profit before tax", pbt)] if v is None]
    if missing:
        tests.append({"test": "De minimis", "can_evaluate": False, "missing": missing, "status": "Cannot evaluate"})
    else:
        passed = revenue < DE_MINIMIS_REVENUE and pbt < DE_MINIMIS_PROFIT
        tests.append({
            "test": "De minimis", "can_evaluate": True, "missing": [],
            "status": "Indicative pass" if passed else "Indicative fail",
            "detail": f"Revenue €{revenue:,.0f} vs €10m; PBT €{pbt:,.0f} vs €1m",
        })

    # 2. Simplified ETR: covered taxes (income tax accrued) / PBT >= transition rate
    rate = SIMPLIFIED_ETR_RATE.get(fiscal_year, 0.17)
    missing = [m for m, v in [("CbCR income tax accrued", tax_accrued), ("CbCR profit before tax", pbt)] if v is None]
    if missing:
        tests.append({"test": "Simplified ETR", "can_evaluate": False, "missing": missing, "status": "Cannot evaluate"})
    elif pbt is not None and pbt <= 0:
        tests.append({
            "test": "Simplified ETR", "can_evaluate": True, "missing": [],
            "status": "Indicative pass", "detail": "Jurisdictional loss — no top-up exposure under this test",
        })
    else:
        etr = tax_accrued / pbt
        tests.append({
            "test": "Simplified ETR", "can_evaluate": True, "missing": [],
            "status": "Indicative pass" if etr >= rate else "Indicative fail",
            "detail": f"Simplified ETR {etr:.1%} vs {rate:.0%} threshold (FY{fiscal_year})",
        })

    # 3. Routine profits: PBT <= SBIE amount (needs entity-level payroll + tangible assets)
    missing = []
    payroll = tangible = None
    if entity_rows.empty:
        missing.append("No entities tied to this jurisdiction (check entity jurisdiction assignments)")
    if "payroll_costs" not in entity_rows.columns or entity_rows.empty or entity_rows["payroll_costs"].isna().any():
        missing.append("Entity-level payroll costs")
    else:
        payroll = float(entity_rows["payroll_costs"].sum())
    if "tangible_asset_carrying_value" not in entity_rows.columns or entity_rows.empty or entity_rows["tangible_asset_carrying_value"].isna().any():
        missing.append("Entity-level tangible asset carrying value")
    else:
        tangible = float(entity_rows["tangible_asset_carrying_value"].sum())
    if pbt is None:
        missing.append("CbCR profit before tax")

    if missing:
        tests.append({"test": "Routine profits", "can_evaluate": False, "missing": missing, "status": "Cannot evaluate"})
    else:
        sbie = SBIE_PAYROLL_PCT * payroll + SBIE_ASSET_PCT * tangible
        passed = pbt <= sbie
        tests.append({
            "test": "Routine profits", "can_evaluate": True, "missing": [],
            "status": "Indicative pass" if passed else "Indicative fail",
            "detail": f"PBT €{pbt:,.0f} vs SBIE amount €{sbie:,.0f}",
        })

    evaluable = sum(1 for t in tests if t["can_evaluate"])
    overall = "Yes" if evaluable == len(tests) else ("Partial" if evaluable else "No")
    return {"can_evaluate": overall, "tests": tests}


def safe_harbour_triage(entity_df, jurisdiction_df, fiscal_year=2026):
    """Run the triage for every jurisdiction. Returns a list of result dicts."""
    results = []
    for _, jur_row in jurisdiction_df.iterrows():
        jurisdiction = jur_row.get("jurisdiction")
        if pd.isna(jurisdiction):
            continue
        if "jurisdiction" in entity_df.columns:
            entity_rows = entity_df[entity_df["jurisdiction"] == jurisdiction]
        else:
            entity_rows = entity_df.iloc[0:0]
        outcome = evaluate_jurisdiction(jur_row, entity_rows, fiscal_year)
        missing_items = sorted({m for t in outcome["tests"] for m in t["missing"]})
        passes = [t["test"] for t in outcome["tests"] if t["status"] == "Indicative pass"]
        results.append({
            "jurisdiction": jurisdiction,
            "can_evaluate": outcome["can_evaluate"],
            "missing_items": missing_items,
            "indicative_passes": passes,
            "tests": outcome["tests"],
        })
    return results
