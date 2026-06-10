import pandas as pd

from pillar_two_copilot.safe_harbour import evaluate_jurisdiction, safe_harbour_triage


def _entities(payroll=10_000_000.0, tangible=20_000_000.0):
    return pd.DataFrame([{
        "entity_name": "E1", "jurisdiction": "Testland",
        "payroll_costs": payroll, "tangible_asset_carrying_value": tangible,
    }])


def test_de_minimis_pass():
    out = evaluate_jurisdiction(
        {"cbcr_revenue": 5_000_000, "cbcr_profit_before_tax": 500_000, "cbcr_income_tax_accrued": 100_000},
        _entities(), fiscal_year=2026,
    )
    de_minimis = next(t for t in out["tests"] if t["test"] == "De minimis")
    assert de_minimis["status"] == "Indicative pass"


def test_simplified_etr_threshold_by_year():
    row = {"cbcr_revenue": 100e6, "cbcr_profit_before_tax": 10e6, "cbcr_income_tax_accrued": 1.65e6}
    # 16.5% ETR: passes 2024 (15%/16%... passes 2024 at 15% and 2025 at 16%), fails 2026 at 17%
    etr_2024 = next(t for t in evaluate_jurisdiction(row, _entities(), 2024)["tests"] if t["test"] == "Simplified ETR")
    etr_2026 = next(t for t in evaluate_jurisdiction(row, _entities(), 2026)["tests"] if t["test"] == "Simplified ETR")
    assert etr_2024["status"] == "Indicative pass"
    assert etr_2026["status"] == "Indicative fail"


def test_loss_jurisdiction_passes_simplified_etr():
    row = {"cbcr_revenue": 100e6, "cbcr_profit_before_tax": -5e6, "cbcr_income_tax_accrued": 0}
    etr = next(t for t in evaluate_jurisdiction(row, _entities(), 2026)["tests"] if t["test"] == "Simplified ETR")
    assert etr["status"] == "Indicative pass"


def test_missing_tax_accrued_blocks_simplified_etr():
    row = {"cbcr_revenue": 100e6, "cbcr_profit_before_tax": 10e6, "cbcr_income_tax_accrued": None}
    out = evaluate_jurisdiction(row, _entities(), 2026)
    etr = next(t for t in out["tests"] if t["test"] == "Simplified ETR")
    assert etr["can_evaluate"] is False
    assert out["can_evaluate"] == "Partial"


def test_missing_payroll_blocks_routine_profits():
    row = {"cbcr_revenue": 100e6, "cbcr_profit_before_tax": 10e6, "cbcr_income_tax_accrued": 2e6}
    out = evaluate_jurisdiction(row, _entities(payroll=None), 2026)
    routine = next(t for t in out["tests"] if t["test"] == "Routine profits")
    assert routine["can_evaluate"] is False
    assert any("payroll" in m.lower() for m in routine["missing"])


def test_no_entities_tied_to_jurisdiction_blocks_routine_profits():
    row = {"cbcr_revenue": 100e6, "cbcr_profit_before_tax": 10e6, "cbcr_income_tax_accrued": 2e6}
    out = evaluate_jurisdiction(row, _entities().iloc[0:0], 2026)
    routine = next(t for t in out["tests"] if t["test"] == "Routine profits")
    assert routine["can_evaluate"] is False
    assert any("No entities tied" in m for m in routine["missing"])


def test_triage_runs_per_jurisdiction():
    entity_df = pd.DataFrame([
        {"entity_name": "A", "jurisdiction": "X", "payroll_costs": 1e6, "tangible_asset_carrying_value": 1e6},
    ])
    jurisdiction_df = pd.DataFrame([
        {"jurisdiction": "X", "cbcr_revenue": 5e6, "cbcr_profit_before_tax": 0.5e6, "cbcr_income_tax_accrued": 0.2e6},
    ])
    results = safe_harbour_triage(entity_df, jurisdiction_df, 2026)
    assert len(results) == 1
    assert results[0]["jurisdiction"] == "X"
    assert results[0]["can_evaluate"] == "Yes"
