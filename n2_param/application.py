"""
Qt application bootstrap: Fusion style for consistent cross-platform appearance.

Creates QApplication and hosts the main window lifecycle.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from PySide6.QtCore import QList

logger = logging.getLogger(__name__)


def create_application(argv: "QList[str] | list[str] | None" = None) -> QApplication:
    """
    Build the global QApplication with a consistent Qt style.

    Args:
        argv: Command-line arguments forwarded to Qt.

    Returns:
        Initialized QApplication instance.
    """
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    app.setStyle("Fusion")
    app.setOrganizationName("n2-param")
    app.setApplicationName("n2-param")
    logger.debug("QApplication created with Fusion style")
    return app


def run_main_window(app: QApplication) -> int:
    """
    Instantiate and show the main window, then exec the event loop.

    Args:
        app: Active QApplication.

    Returns:
        Process exit code from the event loop.
    """
    from n2_param.gui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()
