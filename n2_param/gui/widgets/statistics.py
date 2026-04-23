"""
Placeholder statistics pane until stage 2 defines metrics.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from n2_param.i18n.translator import Translator


class StatisticsWidget(QWidget):
    """Shows a localized placeholder message."""

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        """
        Initialize placeholder content.

        Args:
            translator: Provides localized placeholder text.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._translator = translator
        layout = QVBoxLayout(self)
        self._label = QLabel("", self)
        layout.addWidget(self._label)
        translator.locale_changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        """Reload label text for the active language."""
        self._label.setText(self._translator.tr_key("stats.placeholder"))
