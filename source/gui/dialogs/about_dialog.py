"""
Modal About dialog: square Materyx logotype in the left column and only QLabel widgets
(plain and rich with external links) in the right column. QTextBrowser is not used.
"""

from __future__ import annotations

import logging
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from source import __version__
from source.gui import app_icons
from source.gui.about_info import (
    ABOUT_EMAIL,
    ABOUT_EMAIL_MAILTO,
    URL_ISSUES,
    URL_MIT,
    URL_MXASAP,
    URL_SITE,
)
from source.i18n.translator import Translator

logger = logging.getLogger(__name__)

# Logotype in a fixed square; SVG is scaled to fit.
_LOGO_SIDE_PX: int = 120


def _link_paragraph(
    lead: str, url: str, link_text: str, trail: str
) -> str:
    """
    Build a single rich-text line: ``lead`` + one anchor to ``url`` (label ``link_text``) + ``trail``.

    Inserts a space before the link if ``lead`` does not already end with whitespace, and
    a space after ``</a>`` when ``trail`` (after HTML escaping) starts with a parenthesis so
    languages like Russian do not produce ``лейблMIT(``-style gluing.

    Parameters:
        lead: Unescaped text before the link (from translations).
        url: Absolute URL for the ``href``.
        link_text: Visible link label (unescaped, then escaped in markup).
        trail: Unescaped text after the link (e.g. period or a clause in brackets).

    Returns:
        A safe HTML fragment without outer ``<html>``/``<body>`` tags.

    Raises:
        TypeError: If any argument is not a ``str``.
    """
    if not all(isinstance(x, str) for x in (lead, url, link_text, trail)):
        raise TypeError("lead, url, link_text, and trail must be str")
    s_lead = _h(lead).rstrip() + " "
    anchor = f'<a href="{url}">{_h(link_text)}</a>'
    t = _h(trail)
    if t and t[0] in "(（":
        return f"{s_lead}{anchor} {t}"
    return f"{s_lead}{anchor}{t}"


def _h(text: str) -> str:
    """
    Escape ``text`` for safe use inside a Qt rich text fragment (escaped nodes only, not full URLs
    in ``href`` attributes).

    Parameters:
        text: User-visible string from translations.

    Returns:
        A string safe to place inside an HTML text node in :class:`QLabel` rich text.

    Raises:
        TypeError: If ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return escape(text, quote=True)


def _plain_label(parent: QWidget, text: str) -> QLabel:
    """
    Create a line-wrapping :class:`QLabel` in plain text mode for a paragraph of ``text``.

    Parameters:
        parent: Qt parent.
        text: Unescaped paragraph; stored as plain text (no tags).

    Returns:
        A configured :class:`QLabel`.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    w = QLabel(parent)
    w.setObjectName("aboutLabelPlain")
    w.setTextFormat(Qt.TextFormat.PlainText)
    w.setText(text)
    w.setWordWrap(True)
    w.setAlignment(
        Qt.AlignmentFlag.AlignLeft
        | Qt.AlignmentFlag.AlignTop
    )
    w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return w


def _link_label(parent: QWidget, rich_inner: str) -> QLabel:
    """
    Create a :class:`QLabel` with Qt rich text (one paragraph, may include ``<a>``) and
    :meth:`QWidget.setOpenExternalLinks` enabled so the system opens ``http(s)`` and ``mailto`` targets.

    Parameters:
        parent: Qt parent.
        rich_inner: HTML fragment; must not include outer document wrapper.

    Returns:
        A configured :class:`QLabel`.
    """
    if not isinstance(rich_inner, str):
        raise TypeError("rich_inner must be a string")
    w = QLabel(parent)
    w.setObjectName("aboutLabelLink")
    w.setTextFormat(Qt.TextFormat.RichText)
    w.setText(
        f"<p style='margin:0'>{rich_inner}</p>"
    )
    w.setWordWrap(True)
    w.setOpenExternalLinks(True)
    w.setTextInteractionFlags(
        Qt.TextInteractionFlag.LinksAccessibleByMouse
    )
    w.setAlignment(
        Qt.AlignmentFlag.AlignLeft
        | Qt.AlignmentFlag.AlignTop
    )
    return w


def _v_line(parent: QWidget, translator: Translator) -> list[QLabel]:
    """
    Build the vertical stack of labels for the About right column, in read order from top to bottom.

    Parameters:
        parent: Parent of each label (usually the dialog or the text column widget).
        translator: Active :class:`Translator` for ``about.*`` keys.

    Returns:
        A list of :class:`QLabel` instances in display order.
    """
    if not isinstance(translator, Translator):
        raise TypeError("translator must be a Translator")
    if not isinstance(parent, QWidget):
        raise TypeError("parent must be a QWidget")

    trk = translator.tr_key
    product = trk("about.product_name")

    p5 = _link_paragraph(
        trk("about.p5_lead"),
        URL_MXASAP,
        trk("about.p5_link"),
        trk("about.p5_trail"),
    )
    tr_mit = trk("about.mit_trail")
    if translator.current_language == "cn" and tr_mit.startswith("下"):
        tr_mit = f" {tr_mit}"
    mit = _link_paragraph(
        trk("about.mit_lead"),
        URL_MIT,
        trk("about.mit_link"),
        tr_mit,
    )
    version_line = trk("about.line_version").format(product=product, version=__version__)
    copyright_line = trk("about.line_copyright")
    version_block = (
        f"<b>{_h(version_line)}</b><br/>{_h(copyright_line)}"
    )
    contacts = (
        f"{_h(trk('about.contact_caption'))}: "
        f'<a href="{ABOUT_EMAIL_MAILTO}">{_h(ABOUT_EMAIL)}</a> &middot; '
        f'<a href="{URL_SITE}">www.materyx.ru</a> &middot; '
        f'<a href="{URL_ISSUES}">{_h(trk("about.a_issues"))}</a>'
    )

    labels: list[QLabel] = [
        _plain_label(parent, trk("about.p1")),
        _plain_label(parent, trk("about.p2")),
        _plain_label(parent, trk("about.p3")),
        _plain_label(parent, trk("about.p4")),
        _link_label(parent, p5),
        _link_label(parent, mit),
        _link_label(parent, version_block),
        _link_label(parent, contacts),
    ]
    return labels


class AboutDialog(QDialog):
    """Modal dialog: square logo, plain and rich :class:`QLabel` only (no :class:`QTextBrowser`)."""

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        """
        Create the dialog with a square logotype, an optional link column, and a close button.

        Parameters:
            translator: Supplies the active locale and ``about.*`` strings.
            parent: Optional parent widget, usually the main window.

        Raises:
            TypeError: If ``translator`` is not a :class:`Translator` instance.
        """
        super().__init__(parent)
        if not isinstance(translator, Translator):
            raise TypeError("translator must be a Translator")
        self.setWindowIcon(app_icons.application_icon())
        self.setWindowTitle(translator.tr_key("about.title"))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(8)
        root.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setContentsMargins(0, 0, 0, 0)

        logo = QSvgWidget(self)
        svg_p = app_icons.materyx_brand_svg_path()
        if svg_p.is_file():
            logo.load(str(svg_p))
        else:
            logger.warning("About logo not found: %s", svg_p)
        logo.setFixedSize(_LOGO_SIDE_PX, _LOGO_SIDE_PX)
        top_row.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        text_w = QWidget(self)
        text_col = QVBoxLayout()
        text_col.setSpacing(8)
        text_col.setContentsMargins(0, 0, 0, 0)
        for lab in _v_line(text_w, translator):
            text_col.addWidget(lab)
        text_w.setLayout(text_col)
        text_w.setMinimumWidth(400)
        top_row.addWidget(text_w, 1, Qt.AlignmentFlag.AlignTop)

        root.addLayout(top_row)
        btn_row = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        btn_row.accepted.connect(self.accept)
        root.addWidget(btn_row, 0, Qt.AlignmentFlag.AlignRight)
