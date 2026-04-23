"""
Registration model for per-file inner tabs (charts, stats, raw text).

Adding a view is a single registry entry plus a widget implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from source.gui.file_session import OpenFileSession
from source.i18n.translator import Translator


@dataclass(frozen=True, slots=True)
class ViewDescriptor:
    """Declarative metadata used to construct inner tabs."""

    view_id: str
    title_key: str
    factory: Callable[[OpenFileSession, Translator], QWidget]


def default_view_descriptors() -> tuple[ViewDescriptor, ...]:
    """
    Built-in views for stage 1.

    Returns:
        Tuple ordered as presented to the user.
    """
    from source.gui.widgets.bjh_chart import BjhChartWidget
    from source.gui.widgets.analysis_log_chart import AnalysisLogChartWidget
    from source.gui.widgets.raw_text import RawTextWidget
    from source.gui.widgets.statistics import StatisticsWidget

    return (
        ViewDescriptor(
            view_id="chart_pp0_vs_vol",
            title_key="tab.chart_pp0_vs_vol",
            factory=lambda session, translator: AnalysisLogChartWidget(session, translator),
        ),
        ViewDescriptor(
            view_id="chart_bjh",
            title_key="tab.chart_bjh",
            factory=lambda session, translator: BjhChartWidget(session, translator),
        ),
        ViewDescriptor(
            view_id="statistics",
            title_key="tab.statistics",
            factory=lambda session, translator: StatisticsWidget(translator),
        ),
        ViewDescriptor(
            view_id="raw_text",
            title_key="tab.raw",
            factory=lambda session, translator: RawTextWidget(session, translator),
        ),
    )
