"""
Load bundled SVG assets for the main window toolbar, application / window title icons, and similar chrome.
"""

from __future__ import annotations

import logging
from pathlib import Path

import source
from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)

_PACKAGE_ROOT = Path(source.__file__).resolve().parent
_ICONS = _PACKAGE_ROOT / "resources" / "icons"
_MATERYX_SVG: str = "Materyx"


def toolbar_svg_icon(stem: str) -> QIcon:
    """
    Build a ``QIcon`` from ``resources/icons/<stem>.svg`` in the package tree.

    Parameters:
        stem: File name without extension (e.g. ``"Open"``, ``"Save"``).

    Returns:
        A ``QIcon``, or an empty icon if the file is missing.
    """
    if not isinstance(stem, str) or not stem.strip():
        raise ValueError("stem must be a non-empty string")
    p = _ICONS / f"{stem.strip()}.svg"
    if not p.is_file():
        return QIcon()
    return QIcon(str(p))


def materyx_brand_svg_path() -> Path:
    """
    Return the path to the Materyx logotype (``Materyx.svg``) in ``resources/icons``.

    Returns:
        Path to the asset; use :meth:`Path.is_file` before loading.
    """
    return _ICONS / f"{_MATERYX_SVG}.svg"


def application_icon() -> QIcon:
    """
    Return the application :class:`QIcon` (``Materyx.svg``) for the default window icon: title bar, taskbar,
    dock, and any widget that uses the app-wide icon.

    Returns:
        A non-empty :class:`QIcon` when the SVG is present, otherwise an empty :class:`QIcon`.
    """
    ico = toolbar_svg_icon(_MATERYX_SVG)
    if ico.isNull():
        logger.warning("Application icon is missing: %s", _ICONS / f"{_MATERYX_SVG}.svg")
    return ico
