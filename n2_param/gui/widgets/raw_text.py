"""
Raw ASAP text editor with explicit edit policy and save actions.
"""

from __future__ import annotations

import logging

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from n2_param.gui.file_session import OpenFileSession
from n2_param.i18n.translator import Translator

logger = logging.getLogger(__name__)


class RawTextWidget(QWidget):
    """Editable plain-text view gated by user consent."""

    def __init__(self, session: OpenFileSession, translator: Translator, parent: QWidget | None = None) -> None:
        """
        Wire editor state to the backing session.

        Args:
            session: File buffer to display and persist.
            translator: Localization helper.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._session = session
        self._translator = translator

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self._allow_checkbox = QCheckBox("", self)
        self._save_button = QPushButton("", self)
        self._status_label = QLabel("", self)
        controls.addWidget(self._allow_checkbox)
        controls.addWidget(self._save_button)
        controls.addStretch(1)
        controls.addWidget(self._status_label)
        layout.addLayout(controls)

        self._editor = QPlainTextEdit(self)
        layout.addWidget(self._editor)

        self._editor.blockSignals(True)
        self._editor.setPlainText(session.text)
        self._editor.blockSignals(False)
        self._editor.setReadOnly(not session.allow_edit_raw)

        self._allow_checkbox.setChecked(session.allow_edit_raw)
        self._save_button.setEnabled(session.allow_edit_raw)

        self._allow_checkbox.toggled.connect(self._on_allow_toggled)
        self._save_button.clicked.connect(self._save)
        self._editor.textChanged.connect(self._on_text_changed)
        session.edit_policy_changed.connect(self._on_policy_changed)
        session.dirty_changed.connect(self._on_dirty_changed)
        translator.locale_changed.connect(self._refresh_static_text)

        shortcut = QShortcut(QKeySequence.Save, self)
        shortcut.activated.connect(self._save)

        self._refresh_static_text()
        self._on_dirty_changed(session.is_dirty)

    def _refresh_static_text(self) -> None:
        """Apply localized button and checkbox labels."""
        self._allow_checkbox.setText(self._translator.tr_key("raw.allow_edit"))
        self._save_button.setText(self._translator.tr_key("raw.save"))

    def _on_allow_toggled(self, checked: bool) -> None:
        """Mirror checkbox state into the session policy."""
        self._session.set_allow_edit_raw(checked)
        self._editor.setReadOnly(not checked)
        self._save_button.setEnabled(checked)

    def _on_policy_changed(self, allowed: bool) -> None:
        """Keep widgets aligned when policy changes externally."""
        self._allow_checkbox.blockSignals(True)
        self._allow_checkbox.setChecked(allowed)
        self._allow_checkbox.blockSignals(False)
        self._editor.setReadOnly(not allowed)
        self._save_button.setEnabled(allowed)

    def _on_text_changed(self) -> None:
        """Propagate editor changes into the session buffer."""
        self._session.set_text_buffer(self._editor.toPlainText())

    def _on_dirty_changed(self, dirty: bool) -> None:
        """Show a lightweight dirty indicator near the controls."""
        if dirty:
            self._status_label.setText(self._translator.tr_key("raw.unsaved"))
        else:
            self._status_label.setText("")

    def _save(self) -> None:
        """Persist buffer to disk if editing is enabled."""
        if not self._session.allow_edit_raw:
            return
        text = self._editor.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, self._translator.tr_key("menu.file"), self._translator.tr_key("dialog.save_failed"))
            return
        try:
            self._session.set_text_buffer(text)
            self._session.reparse_buffer()
            self._session.save_to_disk()
        except OSError:
            logger.exception("Save failed")
            QMessageBox.critical(
                self,
                self._translator.tr_key("menu.file"),
                self._translator.tr_key("dialog.save_failed"),
            )
