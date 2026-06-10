"""Load and profile client source files (CSV / Excel)."""

import io
from pathlib import Path

import pandas as pd


def load_tabular(source, filename=None):
    """Load a CSV or Excel source into {sheet_name: DataFrame}.

    `source` may be a path, bytes, or a file-like object (e.g. a Streamlit
    upload). CSVs are returned under the pseudo-sheet name "data".
    """
    name = filename or getattr(source, "name", None)
    if name is None and isinstance(source, (str, Path)):
        name = str(source)
    if name is None:
        raise ValueError("Cannot determine file type: provide `filename`.")

    suffix = Path(name).suffix.lower()
    if isinstance(source, bytes):
        source = io.BytesIO(source)

    if suffix == ".csv":
        return {"data": pd.read_csv(source)}
    if suffix in (".xlsx", ".xls"):
        sheets = pd.read_excel(source, sheet_name=None)
        return {str(k): v for k, v in sheets.items()}
    raise ValueError(f"Unsupported file type: {suffix} (expected .csv, .xlsx, .xls)")


def profile_columns(df, source_file="", sheet=""):
    """Profile each column: dtype, fill rate, sample values.

    The profile is what the mapper (and the reviewer) sees — it keeps the
    audit trail anchored to the original source file/sheet/column.
    """
    profiles = []
    n = len(df)
    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        samples = series.dropna().astype(str).unique()[:3].tolist()
        profiles.append(
            {
                "source_file": source_file,
                "source_sheet": sheet,
                "source_column": str(col),
                "dtype": str(series.dtype),
                "rows": n,
                "non_null": non_null,
                "fill_rate": round(non_null / n, 3) if n else 0.0,
                "sample_values": samples,
            }
        )
    return profiles
