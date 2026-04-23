"""
Load string tables from a line-oriented file and provide runtime language switching.

The bundled ``strings.csv`` uses the multi-character delimiter ``" :: "`` (space, two colons, space)
between columns so commas inside translated text need no escaping. The first line is a header
with lower-case locale codes. Default language is Russian (``ru``).
"""

from __future__ import annotations

import logging
from importlib import resources as importlib_resources
from typing import Final

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

_DEFAULT_LANG: Final[str] = "ru"
# Delimiter between columns in ``source/resources/strings.csv`` (not a single comma).
_STRINGS_FIELD_SEP: Final[str] = " :: "


class Translator(QObject):
    """Qt-friendly translator with a simple CSV backing store."""

    locale_changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        """
        Initialize translator and load bundled defaults.

        Args:
            parent: Optional QObject parent for lifetime management.
        """
        super().__init__(parent)
        self._tables: dict[str, dict[str, str]] = {}
        self._current_lang = _DEFAULT_LANG
        self._load_package_strings()

    @property
    def current_language(self) -> str:
        """Active locale code such as ``ru`` or ``en``."""
        return self._current_lang

    def tr_key(self, key: str) -> str:
        """
        Translate a logical key for the active language.

        Args:
            key: Stable identifier such as ``menu.file.open``.

        Returns:
            Localized string, or the key itself if missing.
        """
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        lang_table = self._tables.get(self._current_lang, {})
        if key in lang_table and lang_table[key].strip():
            return lang_table[key]
        en_table = self._tables.get("en", {})
        if key in en_table and en_table[key].strip():
            return en_table[key]
        logger.warning("Missing translation for key %s", key)
        return key

    def available_languages(self) -> tuple[str, ...]:
        """
        Return locale codes in a fixed order for menus: ``en``, ``ru``, ``cn`` (only those
        with a table in the CSV; default at startup remains ``ru`` if present).
        """
        return self.ordered_ui_languages()

    def ordered_ui_languages(self) -> tuple[str, ...]:
        """
        Return ``en``, ``ru``, ``cn`` in that order, including only codes present in the loaded data.
        """
        preferred: tuple[str, str, str] = ("en", "ru", "cn")
        return tuple(code for code in preferred if code in self._tables)

    def set_language(self, lang_code: str) -> None:
        """
        Switch UI language.

        Args:
            lang_code: Locale code such as ``ru`` or ``en``.

        Raises:
            ValueError: If language is unknown or empty.
        """
        if not isinstance(lang_code, str) or not lang_code.strip():
            raise ValueError("lang_code must be a non-empty string")
        normalized = lang_code.strip().lower()
        if normalized not in self._tables:
            raise ValueError(f"unsupported language: {lang_code}")
        if normalized == self._current_lang:
            return
        self._current_lang = normalized
        self.locale_changed.emit(self._current_lang)

    def _load_package_strings(self) -> None:
        """Load bundled CSV from ``source.resources``."""
        csv_bytes = importlib_resources.files("source.resources").joinpath("strings.csv").read_bytes()
        csv_text = csv_bytes.decode("utf-8")
        self._ingest_csv_text(csv_text)

    def _ingest_csv_text(self, csv_text: str) -> None:
        """
        Parse the strings file: first line is ``key :: en :: ru :: cn`` (arbitrary language columns).
        """
        lines = [ln for ln in csv_text.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("empty strings file")
        sep = _STRINGS_FIELD_SEP
        fieldnames = [c.strip().lower() for c in lines[0].split(sep)]
        key_field = "key"
        if key_field not in fieldnames:
            raise ValueError("strings file must include a 'key' column")
        n_cols = len(fieldnames)
        lang_cols = [fn for fn in fieldnames if fn != key_field]
        for lang in lang_cols:
            self._tables.setdefault(lang, {})

        for line_no, line in enumerate(lines[1:], start=2):
            parts = [c.strip() for c in line.split(sep)]
            if len(parts) != n_cols:
                msg = (
                    f"strings.csv line {line_no}: expected {n_cols} columns"
                    f" (delimiter {sep!r}), got {len(parts)}"
                )
                raise ValueError(msg)
            key = parts[fieldnames.index(key_field)]
            if not key:
                continue
            for fn in lang_cols:
                col_idx = fieldnames.index(fn)
                self._tables[fn][key] = str(parts[col_idx])
