"""
Regression tests for ASAP parsing using synthetic public-safe sample exports.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from source.core.parsing.asap_report_parser import (
    AsapReportParser,
    _ANALYSIS_LOG_LINE,
    _DATA_ROW_RE,
)
from source.gui.chart_series import bjh_dVdD_cc_g_nm

_SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"
_MERGED = "synthetic-asap-merged.001"


def _legacy_first_segment_analysis_log_row_count(text: str) -> int:
    """Count ANALYSIS LOG rows using only the text before the second section header."""
    matches = list(_ANALYSIS_LOG_LINE.finditer(text))
    if not matches:
        return 0
    block_end = matches[1].start() if len(matches) > 1 else len(text)
    block = text[matches[0].end() : block_end]
    header_match = re.search(
        r"RELATIVE\s+PRESSURE.*?VOL ADSORBED",
        block,
        flags=re.DOTALL,
    )
    if header_match is None:
        return 0
    count = 0
    for raw_line in block[header_match.end() :].splitlines():
        if _DATA_ROW_RE.match(raw_line.rstrip("\n")):
            count += 1
    return count


@pytest.mark.parametrize(
    "filename",
    [
        _MERGED,
        "synthetic-asap-alt.002",
    ],
)
def test_parse_samples_parse_without_fatal_errors(filename: str) -> None:
    """Each sample should parse and expose core tables."""
    path = _SAMPLES_DIR / filename
    text = path.read_text(encoding="utf-8", errors="replace")
    report = AsapReportParser().parse(text)
    assert report.sample_id is not None
    assert len(report.analysis_log) > 0
    assert len(report.bjh_desorption_rows) > 0
    assert report.summary.bjh_cumulative_desorption_surface_area_sq_m_g is not None
    assert report.summary.bjh_cumulative_desorption_pore_volume_cc_g is not None
    assert report.summary.bjh_desorption_average_pore_diameter_a is not None


def test_synthetic_merged_log_spans_pages() -> None:
    """Multi-page ANALYSIS LOG continuations must append after the page break."""
    path = _SAMPLES_DIR / _MERGED
    text = path.read_text(encoding="utf-8", errors="replace")
    report = AsapReportParser().parse(text)
    legacy_first_only = _legacy_first_segment_analysis_log_row_count(text)
    assert legacy_first_only > 0
    assert len(report.analysis_log) > legacy_first_only
    assert len(report.analysis_log) == 14


def test_bjh_dVdD_formula_row() -> None:
    """dV/dD = (A * 10) / (B - C) with A incremental volume, C_min and B_max from range (Å)."""
    path = _SAMPLES_DIR / _MERGED
    text = path.read_text(encoding="utf-8", errors="replace")
    report = AsapReportParser().parse(text)
    assert len(report.bjh_desorption_rows) >= 2
    row1 = report.bjh_desorption_rows[1]
    a = 0.009009
    b_minus_c = 441.8 - 394.6
    expect = a * 10.0 / b_minus_c
    assert bjh_dVdD_cc_g_nm(row1) == pytest.approx(expect, rel=1e-5)


def test_synthetic_merged_summary_snapshot() -> None:
    """Spot-check summary metrics from the merged synthetic file."""
    path = _SAMPLES_DIR / _MERGED
    text = path.read_text(encoding="utf-8", errors="replace")
    report = AsapReportParser().parse(text)
    assert report.sample_id == "Demo-01, Lab Specimen"
    assert report.summary.bjh_cumulative_desorption_surface_area_sq_m_g == pytest.approx(12.5)
    assert report.summary.bjh_cumulative_desorption_pore_volume_cc_g == pytest.approx(0.1)
    assert report.summary.bjh_desorption_average_pore_diameter_a == pytest.approx(50.0)
