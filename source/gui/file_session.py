"""
Mutable per-file state shared between raw editor and chart widgets.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from source.core.models import ParsedReport
from source.core.parsing.asap_report_parser import AsapReportParser

logger = logging.getLogger(__name__)


class OpenFileSession(QObject):
    """Tracks text, parsed results, and edit permissions for one report file."""

    parsed_changed = Signal()
    dirty_changed = Signal(bool)
    edit_policy_changed = Signal(bool)

    def __init__(
        self,
        path: Path,
        text: str,
        encoding: str,
        parsed: ParsedReport,
        parent: QObject | None = None,
    ) -> None:
        """
        Construct a session for an on-disk ASAP export.

        Args:
            path: Absolute path to the source file.
            text: Full decoded file contents.
            encoding: Encoding used when reading the file.
            parsed: Initial parse result for the text.
            parent: Optional QObject parent.
        """
        super().__init__(parent)
        if not isinstance(path, Path):
            raise TypeError("path must be pathlib.Path")
        if not path.is_absolute():
            raise ValueError("path must be absolute")
        if not isinstance(text, str):
            raise TypeError("text must be str")
        if not isinstance(encoding, str) or not encoding.strip():
            raise ValueError("encoding must be a non-empty string")
        self._path = path
        self._text = text
        self._encoding = encoding
        self._parsed = parsed
        self._parser = AsapReportParser()
        self._dirty = False
        self._allow_edit_raw = False

    @property
    def path(self) -> Path:
        """Filesystem path for this session."""
        return self._path

    @property
    def text(self) -> str:
        """Current in-memory text buffer."""
        return self._text

    @property
    def encoding(self) -> str:
        """Encoding used for round-tripping saves."""
        return self._encoding

    @property
    def parsed(self) -> ParsedReport:
        """Latest structured parse for this buffer."""
        return self._parsed

    @property
    def is_dirty(self) -> bool:
        """True if buffer differs from last successful save."""
        return self._dirty

    @property
    def allow_edit_raw(self) -> bool:
        """Whether raw text editing is permitted by the user."""
        return self._allow_edit_raw

    def set_allow_edit_raw(self, enabled: bool) -> None:
        """
        Toggle raw editing permission.

        Args:
            enabled: When False, editors must stay read-only.
        """
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be bool")
        if enabled == self._allow_edit_raw:
            return
        self._allow_edit_raw = enabled
        self.edit_policy_changed.emit(self._allow_edit_raw)

    def set_text_buffer(self, text: str) -> None:
        """
        Update buffer text and mark dirty without immediate disk write.

        Args:
            text: Replacement text from the editor.
        """
        if not isinstance(text, str):
            raise TypeError("text must be str")
        self._text = text
        self._set_dirty(True)

    def apply_disk_snapshot(self, text: str, encoding: str, parsed: ParsedReport) -> None:
        """
        Replace buffer after a successful load or external reload.

        Args:
            text: Text loaded from disk.
            encoding: Encoding used for that text.
            parsed: Parsed representation.
        """
        self._text = text
        self._encoding = encoding
        self._parsed = parsed
        self._set_dirty(False)
        self.parsed_changed.emit()

    def reparse_buffer(self) -> None:
        """Recompute structured data from the current buffer."""
        self._parsed = self._parser.parse(self._text)
        self.parsed_changed.emit()

    def save_to_disk(self) -> None:
        """
        Persist the buffer using the tracked encoding.

        Raises:
            OSError: Propagated from filesystem writes.
        """
        self._path.write_text(self._text, encoding=self._encoding)
        logger.info("Saved ASAP report to %s", self._path)
        self._set_dirty(False)

    def mark_saved_snapshot(self) -> None:
        """Clear dirty flag after a successful save."""
        self._set_dirty(False)

    def display_title(self) -> str:
        """Human-friendly tab label prioritizing SAMPLE ID."""
        sid = self._parsed.sample_id
        if sid is not None and sid.strip():
            return sid.strip()
        return self._path.name

    def _set_dirty(self, dirty: bool) -> None:
        if self._dirty == dirty:
            return
        self._dirty = dirty
        self.dirty_changed.emit(self._dirty)
