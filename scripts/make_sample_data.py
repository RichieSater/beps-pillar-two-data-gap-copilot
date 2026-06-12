"""Generate the synthetic 'Atlas Components Group' demo files.

The files intentionally contain real-world messiness:
- entity names that differ across systems (Ltd vs Limited, typos)
- a missing jurisdiction (Atlas UK Services Ltd in the entity master)
- missing entity-level deferred tax detail (Ireland)
- payroll available only at country level for Singapore
- missing tangible asset value (Netherlands)
- a blended tax adjustment column (TaxExpAdj)
- jurisdiction-level CbCR data with a missing income-tax-accrued figure (Singapore)

Run: python scripts/make_sample_data.py
"""

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_inputs"
OUT.mkdir(parents=True, exist_ok=True)

NA = None

entity_master = pd.DataFrame(
    [
        ["ATL001", "Atlas US Inc", "United States", 100.0, "Full"],
        ["ATL002", "Atlas IE Holdings Limited", "Ireland", 100.0, "Full"],
        ["ATL003", "Atlas DE GmbH", "Germany", 100.0, "Full"],
        ["ATL004", "Atlas NL B.V.", "Netherlands", 100.0, "Full"],
        ["ATL005", "Atlas SG IP Pte Ltd", "Singapore", 100.0, "Full"],
        ["ATL006", "Atlas UK Services Ltd", NA, 80.0, "Full"],  # jurisdiction missing
    ],
    columns=["LE_Code", "LegalEntityName", "Country_of_Residence", "Ownership_Pct", "Consol_Method"],
)
entity_master.to_csv(OUT / "entity_master.csv", index=False)

# Trial balance: entity names deliberately differ from the master.
trial_balance = pd.DataFrame(
    [
        ["Atlas US, Inc.", 520_000_000, 80_000_000, 110_000_000, 95_000_000],
        ["Atlas IE Holdings Ltd", 310_000_000, 95_000_000, 22_000_000, 8_000_000],
        ["Atlas DE GmbH", 180_000_000, 24_000_000, 35_000_000, 28_000_000],
        ["Atlas NL BV", 9_200_000, 700_000, 2_100_000, NA],          # tangible assets missing
        ["Atlas SG IP Pte. Ltd", 140_000_000, 60_000_000, NA, 3_000_000],  # payroll missing
        ["Atlas UK Service Ltd", 75_000_000, 6_000_000, 18_000_000, 12_000_000],  # typo: Service
    ],
    columns=["Entity", "Rev_Total", "PBT_Local", "Payroll_Cost", "Tangible_Assets_NBV"],
)
with pd.ExcelWriter(OUT / "trial_balance_by_entity.xlsx", engine="openpyxl") as writer:
    trial_balance.to_excel(writer, sheet_name="TB_FY2026", index=False)

tax_provision = pd.DataFrame(
    [
        ["Atlas US Inc", 18_000_000, 1_200_000, 2_500_000, 3_500_000],
        ["Atlas IE Holdings Limited", 9_500_000, 800_000, NA, NA],   # deferred detail missing
        ["Atlas DE GmbH", 7_400_000, 300_000, 600_000, 400_000],
        ["Atlas NL B.V.", 200_000, 0, 50_000, NA],
        ["Atlas SG IP Pte Ltd", 3_000_000, 500_000, 400_000, NA],
        ["Atlas UK Services Ltd", 1_500_000, 100_000, 300_000, NA],
    ],
    columns=["Entity_Name", "Curr_Tax_Exp", "TaxExpAdj", "DTA_Movement", "RD_Tax_Credits"],
)
tax_provision.to_csv(OUT / "tax_provision_extract.csv", index=False)

cbcr = pd.DataFrame(
    [
        ["United States", 520_000_000, 80_000_000, 17_500_000, 1200, 95_000_000],
        ["Ireland", 310_000_000, 95_000_000, 11_400_000, 150, 8_000_000],
        ["Germany", 180_000_000, 24_000_000, 7_200_000, 400, 28_000_000],
        ["Netherlands", 9_200_000, 700_000, 200_000, 25, 1_500_000],
        ["Singapore", 140_000_000, 60_000_000, NA, 45, 3_000_000],     # tax accrued missing
        ["United Kingdom", 75_000_000, 6_000_000, 1_400_000, 220, 12_000_000],
    ],
    columns=["Tax_Jurisdiction", "Revenues", "Profit_Loss_Before_Income_Tax",
             "Income_Tax_Accrued", "Employees", "Tangible_Assets"],
)
cbcr.to_csv(OUT / "cbcr_report.csv", index=False)

attributes = pd.DataFrame(
    [
        ["United States", "No", "No", "No"],
        ["Ireland", "Yes", "Yes", "Yes"],
        ["Germany", "Yes", "Yes", "Yes"],
        ["Netherlands", "Yes", "Yes", "Yes"],
        ["Singapore", "Yes", "No", "No"],
        ["United Kingdom", "Yes", "Yes", "No"],
    ],
    columns=["Country", "QDMTT_Enacted", "IIR_Enacted", "UTPR_Enacted"],
)
attributes.to_csv(OUT / "jurisdiction_tax_attributes.csv", index=False)

print(f"Sample files written to {OUT}")
