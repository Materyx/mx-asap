"""
Abstract export interfaces so Excel writers can plug in later.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from n2_param.core.models import ParsedReport


class ExportSink(Protocol):
    """Target for structured exports such as spreadsheets."""

    def export_parsed_report(self, target_path: Path, report: ParsedReport) -> None:
        """Persist a parsed report to a file."""
        ...


class NoopExportSink:
    """Placeholder exporter for early development stages."""

    def export_parsed_report(self, target_path: Path, report: ParsedReport) -> None:
        """
        Raise to signal that export is not implemented yet.

        Args:
            target_path: Unused in this stub.
            report: Unused in this stub.

        Raises:
            RuntimeError: Always, until stage 2 implements real export.
        """
        raise RuntimeError("Excel export is planned for stage 2")
