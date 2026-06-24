from __future__ import annotations
import csv
import io
import numpy as np


def parse_hardware_csv(content: bytes, vendor: str | None) -> tuple[np.ndarray, int]:
    """Return (force_N_array, sample_rate_hz). Auto-detects column if vendor unknown."""
    v = (vendor or "").lower()
    if v == "hawkin":
        return _hawkin(content)
    if v in ("amti", "kistler", "bertec", "vald"):
        return _column_csv(content, col_keywords=["fz", "force"], default_sr=1000)
    return _generic(content)


def _hawkin(content: bytes) -> tuple[np.ndarray, int]:
    text = content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    sample_rate = 1000
    data_start = 0
    for i, line in enumerate(lines):
        ll = line.lower()
        if "sample rate" in ll or "samplerate" in ll:
            try:
                sample_rate = int("".join(filter(str.isdigit, line.split(",")[-1])))
            except ValueError:
                pass
        if ll.startswith("time") or "time (s)" in ll:
            data_start = i
            break
    reader = csv.DictReader(io.StringIO("\n".join(lines[data_start:])))
    fz_col = next(
        (h for h in (reader.fieldnames or []) if "fz" in h.lower() or "force" in h.lower()),
        None,
    )
    if not fz_col:
        return _generic(content)
    values = [float(r[fz_col]) for r in reader if _safe_float(r.get(fz_col, "")) is not None]
    return np.array(values, dtype=float), sample_rate


def _column_csv(content: bytes, col_keywords: list[str], default_sr: int) -> tuple[np.ndarray, int]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    col = next((h for h in headers for kw in col_keywords if kw in h.lower()), None)
    if not col:
        return _generic(content)
    values = [v for r in reader if (v := _safe_float(r.get(col, ""))) is not None]
    return np.array(values, dtype=float), default_sr


def _generic(content: bytes) -> tuple[np.ndarray, int]:
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    data_start = next((i for i, r in enumerate(rows) if r and _safe_float(r[0]) is not None), 0)
    data_rows = rows[data_start:]
    if not data_rows:
        raise ValueError("No numeric data found in CSV")
    n_cols = len(data_rows[0])
    best_col = max(
        range(n_cols),
        key=lambda c: sum(1 for r in data_rows if c < len(r) and _safe_float(r[c]) is not None),
    )
    values = [
        v for r in data_rows
        if (v := _safe_float(r[best_col] if best_col < len(r) else "")) is not None
    ]
    return np.array(values, dtype=float), 1000


def _safe_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
