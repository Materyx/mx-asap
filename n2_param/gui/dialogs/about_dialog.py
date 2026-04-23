"""
About box with localized chrome and static developer details.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from n2_param.gui.about_info import ABOUT_DETAILS
from n2_param.i18n.translator import Translator


class AboutDialog(QDialog):
    """Small modal dialog describing the application."""

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        """
        Build dialog labels from translator keys and local constants.

        Args:
            translator: Supplies localized window title and summary line.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle(translator.tr_key("about.title"))

        layout = QVBoxLayout(self)
        summary = QLabel(translator.tr_key("about.body"), self)
        summary.setWordWrap(True)
        details = QLabel(ABOUT_DETAILS, self)
        details.setWordWrap(True)

        layout.addWidget(summary)
        layout.addWidget(details)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
