"""src/publication/statistics_formatter.py — Consistent statistical formatting for Phase 12.

Provides scientific and publication-standard number formatting, confidence intervals,
p-values, and LaTeX math representations without modifying or recomputing raw numerical values.
"""

from typing import Any
import numpy as np


def format_f1(value: float | None, precision: int = 4) -> str:
    """Format F1 score to fixed decimal places or placeholder."""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value:.{precision}f}"


def format_percentage(value: float | None, precision: int = 2) -> str:
    """Format error percentages like MAPE."""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value:.{precision}f}\\%"


def format_ci(lower: float, upper: float, precision: int = 4) -> str:
    """Format a 95% confidence interval [lower, upper]."""
    return f"[{lower:.{precision}f}, {upper:.{precision}f}]"


def format_p_value(p: float) -> str:
    """Format p-value per IEEE style."""
    if p < 0.0001:
        return "< 0.0001"
    elif p < 0.001:
        return f"{p:.4f}"
    elif p >= 0.9999:
        return "1.0000"
    return f"{p:.4f}"


def format_scientific(val: float, precision: int = 2) -> str:
    """Format small values in scientific LaTeX notation."""
    if abs(val) < 1e-12:
        return "0.0"
    exp = int(np.floor(np.log10(abs(val))))
    coeff = val / (10 ** exp)
    return f"{coeff:.{precision}f} \\times 10^{{{exp}}}"


def sanitize_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text."""
    replacements = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    res = text
    for char, rep in replacements.items():
        res = res.replace(char, rep)
    return res
