"""
Structured representations of ASAP report content.

Designed for reuse by GUI plots and future Excel exporters.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AnalysisLogRow:
    """Single row from the first ANALYSIS LOG table."""

    relative_pressure: float
    pressure_mmhg: float
    vol_adsorbed_cc_g_stp: float


@dataclass(frozen=True, slots=True)
class BJHDesorptionRow:
    """Single row from the BJH desorption pore distribution table."""

    pore_diameter_low_a: float
    pore_diameter_high_a: float
    average_diameter_a: float
    incremental_pore_volume_cc_g: float
    cumulative_pore_volume_cc_g: float
    incremental_pore_area_sq_m_g: float
    cumulative_pore_area_sq_m_g: float


@dataclass(frozen=True, slots=True)
class SummaryMetrics:
    """Selected numeric summary fields from the SUMMARY REPORT section."""

    bjh_cumulative_desorption_surface_area_sq_m_g: float | None
    bjh_cumulative_desorption_pore_volume_cc_g: float | None
    bjh_desorption_average_pore_diameter_a: float | None


@dataclass(frozen=True, slots=True)
class ParsedReport:
    """Complete parse result for one ASAP text file."""

    sample_id: str | None
    analysis_log: tuple[AnalysisLogRow, ...]
    bjh_desorption_rows: tuple[BJHDesorptionRow, ...]
    summary: SummaryMetrics
    warnings: tuple[str, ...] = field(default_factory=tuple)
