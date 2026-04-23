"""
Container widget that hosts per-file inner tabs (views).
"""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from source.gui.file_session import OpenFileSession
from source.gui.view_registry import ViewDescriptor, default_view_descriptors
from source.i18n.translator import Translator


class FileTabPage(QWidget):
    """Wraps the nested tab widget for one ASAP file."""

    def __init__(
        self,
        session: OpenFileSession,
        translator: Translator,
        descriptors: tuple[ViewDescriptor, ...] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Populate nested tabs using the provided descriptor registry.

        Args:
            session: Active file session shared by child widgets.
            translator: Localization helper for tab titles.
            descriptors: Optional custom registry; defaults to stage-1 views.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._session = session
        self._translator = translator
        layout = QVBoxLayout(self)
        self._inner_tabs = QTabWidget(self)
        layout.addWidget(self._inner_tabs)

        self._descriptors = descriptors if descriptors is not None else default_view_descriptors()
        for descriptor in self._descriptors:
            view = descriptor.factory(session, translator)
            title = translator.tr_key(descriptor.title_key)
            self._inner_tabs.addTab(view, title)

        translator.locale_changed.connect(self._refresh_titles)

    @property
    def session(self) -> OpenFileSession:
        """Session backing this page."""
        return self._session

    def _refresh_titles(self) -> None:
        """Update tab captions after language switches."""
        count = min(self._inner_tabs.count(), len(self._descriptors))
        for idx in range(count):
            title_key = self._descriptors[idx].title_key
            self._inner_tabs.setTabText(idx, self._translator.tr_key(title_key))
