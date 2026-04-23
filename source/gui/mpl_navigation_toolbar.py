"""
Custom Matplotlib Qt navigation toolbar: localized Figure options and wide default dialog.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox, QWidget

import matplotlib.backends.qt_editor.figureoptions as mfigureoptions
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

from source.gui.qt_figureoptions import figure_edit

if TYPE_CHECKING:
    from source.i18n.translator import Translator

logger = logging.getLogger(__name__)

# Proportion: height:width = 1:1.5  (width = 1.5 * height).
_FIGURE_OPTIONS_H_PX: int = 400
_FIGURE_OPTIONS_H_MIN_PX: int = 300
_FIGURE_OPTIONS_W_OVER_H: float = 1.5
_FIGURE_OPTIONS_SCREEN_MARGIN: int = 40


def _size_figure_options_dialog(dlg: QDialog) -> None:
    """
    Resize the Matplotlib ``fedit`` / "Figure options" form dialog to a wide format.

    Uses **height:width = 1:1.5** (i.e. ``width = 1.5 * height``), then shrinks to fit the screen if needed.

    Args:
        dlg: The ``FormDialog`` created by ``matplotlib.backends.qt_editor._formlayout.fedit``.

    Raises:
        TypeError: If ``dlg`` is not a ``QDialog`` instance.
    """
    if not isinstance(dlg, QDialog):
        raise TypeError("dlg must be a QDialog")
    h = int(
        max(
            _FIGURE_OPTIONS_H_MIN_PX,
            _FIGURE_OPTIONS_H_PX,
            int(dlg.sizeHint().height()),
        )
    )
    wh = _FIGURE_OPTIONS_W_OVER_H
    w = int(round(wh * h))
    screen = dlg.screen()
    if screen is not None:
        g = screen.availableGeometry()
        m = _FIGURE_OPTIONS_SCREEN_MARGIN
        max_w = int(max(200, g.width() - m))
        max_h = int(max(200, g.height() - m))
        w = min(int(w), max_w)
        h = int(round(w / wh))
        if h > max_h:
            h = int(max_h)
            w = min(int(round(wh * h)), max_w)
    dlg.resize(int(w), int(h))
    logger.debug("Figure options dialog resized to %dx%d", w, h)


class MateryxAsapNavigationToolbar2QT(NavigationToolbar2QT):
    """
    Same as :class:`NavigationToolbar2QT` with a localized "Figure options" form and
    a wider default size (height:width = 1:1.5).
    """

    def __init__(
        self,
        canvas: FigureCanvasQTAgg,
        parent: QWidget | None = None,
        *,
        translator: Translator | None = None,
    ) -> None:
        """
        Build the stock toolbar; ``translator`` drives the Figure options dialog text.

        Args:
            canvas: The figure canvas to control.
            parent: Optional parent widget (often the containing chart view).
            translator: If given, "Figure options" and multi-axes prompts use the active locale.
        """
        super().__init__(canvas, parent)
        self._translator: Translator | None = translator
        if translator is None and parent is not None:
            t = getattr(parent, "_translator", None)
            if t is not None and hasattr(t, "tr_key"):
                self._translator = t  # type: ignore[assignment]

    @staticmethod
    def _tr_errors_only_en(key: str) -> str:
        """Short English for toolbar prompts when a full translator is not wired."""
        if key == "figure_options.error_title":
            return "Error"
        if key == "figure_options.error_no_axes":
            return "There are no Axes to edit."
        if key == "figure_options.customize":
            return "Customize"
        if key == "figure_options.select_axes":
            return "Select Axes:"
        return key

    def edit_parameters(self) -> None:  # noqa: C901
        """
        Open the figure-options form; optional axes picker; then size the wide dialog.
        """
        t = self._translator
        if t is None and self.parent() is not None:
            t = getattr(self.parent(), "_translator", None)
        axes = self.canvas.figure.get_axes()
        if not axes:
            QMessageBox.warning(
                self.canvas.parent(),
                t.tr_key("figure_options.error_title")
                if t is not None and hasattr(t, "tr_key")
                else MateryxAsapNavigationToolbar2QT._tr_errors_only_en("figure_options.error_title"),
                t.tr_key("figure_options.error_no_axes")
                if t is not None and hasattr(t, "tr_key")
                else MateryxAsapNavigationToolbar2QT._tr_errors_only_en("figure_options.error_no_axes"),
            )
            return
        if len(axes) == 1:
            ax, = axes
        else:
            qtitles = [
                ax.get_label()
                or ax.get_title()
                or ax.get_title("left")
                or ax.get_title("right")
                or " - ".join(filter(None, [ax.get_xlabel(), ax.get_ylabel()]))
                or f"<anonymous {type(ax).__name__}>"
                for ax in axes
            ]
            duplicate = [q for q in qtitles if qtitles.count(q) > 1]
            for i, axx in enumerate(axes):
                if qtitles[i] in duplicate:
                    qtitles[i] = f"{qtitles[i]} (id: {id(axx):#x})"
            item, ok = QInputDialog.getItem(
                self.canvas.parent(),
                t.tr_key("figure_options.customize")
                if t is not None and hasattr(t, "tr_key")
                else MateryxAsapNavigationToolbar2QT._tr_errors_only_en("figure_options.customize"),
                t.tr_key("figure_options.select_axes")
                if t is not None and hasattr(t, "tr_key")
                else MateryxAsapNavigationToolbar2QT._tr_errors_only_en("figure_options.select_axes"),
                qtitles,
                0,
                False,
            )
            if not ok:
                return
            ax = axes[qtitles.index(item)]

        if t is not None and hasattr(t, "tr_key"):

            def tr(k: str) -> str:
                return t.tr_key(k)  # type: ignore[union-attr, no-any-return]

            figure_edit(ax, self, tr)
        else:
            mfigureoptions.figure_edit(ax, self)
        dlg = getattr(self, "_fedit_dialog", None)
        if not isinstance(dlg, QDialog):
            return
        QTimer.singleShot(0, lambda d=dlg: _size_figure_options_dialog(d))
