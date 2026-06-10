"""Simplified Pillar Two field catalog.

Each canonical field carries everything the deterministic rules need:
which compliance purposes require it, how severe a gap is, who in a tax
operating model usually owns the data, and the remediation request to
draft when it is missing. `synonyms` feed the heuristic column mapper.
"""

# Compliance purposes a field can block.
PURPOSES = {
    "globe_etr": "GloBE ETR / top-up tax calculation",
    "cbcr_safe_harbour": "Transitional CbCR safe harbour",
    "sbie": "Substance-based income exclusion",
    "gir": "GloBE Information Return filing",
}

SEVERITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}

# level: "entity" fields are expected per constituent entity,
# "jurisdiction" fields per jurisdiction (e.g. CbCR aggregates).
FIELD_CATALOG = {
    "entity_id": {
        "label": "Legal entity identifier",
        "level": "entity",
        "required_for": ["globe_etr", "cbcr_safe_harbour", "sbie", "gir"],
        "severity": "high",
        "likely_owner": "Legal Entity Management",
        "remediation": "Confirm a unique legal entity identifier (LEI or internal code) for every constituent entity.",
        "synonyms": ["entity id", "entity code", "le code", "legal entity id", "company code", "lei"],
    },
    "entity_name": {
        "label": "Legal entity name",
        "level": "entity",
        "required_for": ["globe_etr", "cbcr_safe_harbour", "sbie", "gir"],
        "severity": "high",
        "likely_owner": "Legal Entity Management",
        "remediation": "Provide the registered legal name; reconcile naming differences across source systems.",
        "synonyms": ["entity name", "legal entity", "legal entity name", "company name", "entity"],
    },
    "jurisdiction": {
        "label": "Tax jurisdiction of residence",
        "level": "entity",
        "required_for": ["globe_etr", "cbcr_safe_harbour", "sbie", "gir"],
        "severity": "high",
        "likely_owner": "International Tax",
        "remediation": "Confirm jurisdiction of tax residence for each entity (incl. dual-residence analysis where relevant).",
        "synonyms": ["jurisdiction", "country", "tax jurisdiction", "country of residence", "tax country", "residence"],
    },
    "ownership_percentage": {
        "label": "Ownership percentage",
        "level": "entity",
        "required_for": ["globe_etr", "gir"],
        "severity": "medium",
        "likely_owner": "Legal Entity Management",
        "remediation": "Provide UPE ownership percentage to determine allocable share of top-up tax.",
        "synonyms": ["ownership", "ownership pct", "ownership percent", "holding pct", "share held", "pct owned"],
    },
    "consolidation_method": {
        "label": "Consolidation status / method",
        "level": "entity",
        "required_for": ["globe_etr", "gir"],
        "severity": "medium",
        "likely_owner": "Group Consolidation",
        "remediation": "Confirm consolidation method (full / equity / not consolidated) per entity to scope constituent entities.",
        "synonyms": ["consolidation", "consolidation method", "consol method", "consolidation status"],
    },
    "revenue": {
        "label": "Revenue",
        "level": "entity",
        "required_for": ["globe_etr", "cbcr_safe_harbour"],
        "severity": "high",
        "likely_owner": "Group Consolidation / ERP",
        "remediation": "Pull entity-level revenue from the consolidation system or trial balance.",
        "synonyms": ["revenue", "total revenue", "rev total", "net sales", "turnover", "sales"],
    },
    "profit_loss_before_tax": {
        "label": "Profit / loss before tax",
        "level": "entity",
        "required_for": ["globe_etr", "cbcr_safe_harbour"],
        "severity": "high",
        "likely_owner": "Group Consolidation / ERP",
        "remediation": "Provide PBT per entity on the group reporting basis (note local GAAP vs group GAAP differences).",
        "synonyms": ["pbt", "pbt local", "profit before tax", "pretax income", "ebt", "income before tax", "profit loss before tax"],
    },
    "current_tax_expense": {
        "label": "Current tax expense",
        "level": "entity",
        "required_for": ["globe_etr"],
        "severity": "high",
        "likely_owner": "Tax Provision",
        "remediation": "Extract entity-level current tax expense from the provision system.",
        "synonyms": ["current tax", "current tax expense", "curr tax exp", "current income tax"],
    },
    "deferred_tax_expense": {
        "label": "Deferred tax expense",
        "level": "entity",
        "required_for": ["globe_etr"],
        "severity": "high",
        "likely_owner": "Tax Provision",
        "remediation": "Request an entity-level deferred tax rollforward (movement by category, recast at 15% where required).",
        "synonyms": ["deferred tax", "deferred tax expense", "def tax exp", "dta movement", "dtl movement", "deferred tax movement"],
    },
    "covered_taxes_adjustments": {
        "label": "Covered taxes adjustments",
        "level": "entity",
        "required_for": ["globe_etr"],
        "severity": "medium",
        "likely_owner": "Tax Provision",
        "remediation": "Disaggregate blended tax adjustment lines into GloBE covered-tax adjustment categories.",
        "synonyms": ["tax adjustments", "tax exp adj", "covered taxes adjustment", "tax expense adjustments", "uncertain tax positions"],
    },
    "excluded_dividends": {
        "label": "Excluded dividends / equity gains",
        "level": "entity",
        "required_for": ["globe_etr"],
        "severity": "medium",
        "likely_owner": "Group Consolidation",
        "remediation": "Identify intercompany dividends and excluded equity gains/losses booked in PBT.",
        "synonyms": ["dividend income", "excluded dividends", "equity method income", "dividends received"],
    },
    "payroll_costs": {
        "label": "Eligible payroll costs",
        "level": "entity",
        "required_for": ["sbie"],
        "severity": "medium",
        "likely_owner": "HR / Finance",
        "remediation": "Request payroll cost split by entity and by employee work location (not just country aggregate).",
        "synonyms": ["payroll", "payroll costs", "wages", "staff costs", "employee costs", "avg fte cost", "personnel expense"],
    },
    "tangible_asset_carrying_value": {
        "label": "Tangible asset carrying value",
        "level": "entity",
        "required_for": ["sbie"],
        "severity": "medium",
        "likely_owner": "Fixed Assets",
        "remediation": "Pull the fixed asset register by entity (carrying value of eligible tangible assets, incl. ROU assets).",
        "synonyms": ["tangible assets", "fixed assets", "ppe", "property plant equipment", "tangible asset carrying value", "asset carrying value"],
    },
    "tax_credits": {
        "label": "Tax credits (incl. refundability)",
        "level": "entity",
        "required_for": ["globe_etr"],
        "severity": "medium",
        "likely_owner": "Local Tax",
        "remediation": "Confirm credit type and whether each credit is a qualified refundable tax credit (QRTC).",
        "synonyms": ["tax credits", "rd credit", "r&d credit", "credits", "qualified refundable tax credit", "qrtc"],
    },
    "cbcr_revenue": {
        "label": "CbCR revenue (jurisdiction)",
        "level": "jurisdiction",
        "required_for": ["cbcr_safe_harbour"],
        "severity": "high",
        "likely_owner": "Tax Reporting (CbCR)",
        "remediation": "Source jurisdictional revenue from the qualified CbC report.",
        "synonyms": ["cbcr revenue", "cb cr revenue", "revenue unrelated party", "total revenue cbcr", "revenues"],
    },
    "cbcr_profit_before_tax": {
        "label": "CbCR profit before tax (jurisdiction)",
        "level": "jurisdiction",
        "required_for": ["cbcr_safe_harbour"],
        "severity": "high",
        "likely_owner": "Tax Reporting (CbCR)",
        "remediation": "Source jurisdictional profit (loss) before income tax from the qualified CbC report.",
        "synonyms": ["profit loss before income tax", "cbcr pbt", "profit before income tax"],
    },
    "cbcr_income_tax_accrued": {
        "label": "CbCR income tax accrued (jurisdiction)",
        "level": "jurisdiction",
        "required_for": ["cbcr_safe_harbour"],
        "severity": "high",
        "likely_owner": "Tax Reporting (CbCR)",
        "remediation": "Source income tax accrued (current year) from the qualified CbC report.",
        "synonyms": ["income tax accrued", "tax accrued current year", "income tax accrued current year"],
    },
    "qdmtt_status": {
        "label": "QDMTT / IIR / UTPR status (jurisdiction)",
        "level": "jurisdiction",
        "required_for": ["gir"],
        "severity": "medium",
        "likely_owner": "International Tax",
        "remediation": "Track which jurisdictions have enacted QDMTT/IIR/UTPR and from which fiscal year.",
        "synonyms": ["qdmtt", "qdmtt status", "iir status", "utpr status", "pillar two status", "minimum tax status"],
    },
}


def fields_for_level(level):
    """Return {field_key: spec} for one level ('entity' or 'jurisdiction')."""
    return {k: v for k, v in FIELD_CATALOG.items() if v["level"] == level}


def blocked_purposes(field_key):
    """Human-readable purposes blocked when `field_key` is missing."""
    spec = FIELD_CATALOG[field_key]
    return [PURPOSES[p] for p in spec["required_for"]]
