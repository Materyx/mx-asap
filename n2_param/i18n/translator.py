"""
Load string tables from CSV and provide runtime language switching.

Default language is Russian (RU). CSV columns are locale codes in lower case.
"""

from __future__ import annotations

import csv
import logging
from importlib import resources as importlib_resources
from typing import Final

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

_DEFAULT_LANG: Final[str] = "ru"


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
        """Return locale codes present in the loaded tables."""
        return tuple(sorted(self._tables.keys()))

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
        """Load bundled CSV from ``n2_param.resources``."""
        csv_bytes = importlib_resources.files("n2_param.resources").joinpath("strings.csv").read_bytes()
        csv_text = csv_bytes.decode("utf-8")
        self._ingest_csv_text(csv_text)

    def _ingest_csv_text(self, csv_text: str) -> None:
        """Parse CSV content with header row: key,en,ru,cn,..."""
        reader = csv.DictReader(csv_text.splitlines())
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        fieldnames = [fn.strip().lower() for fn in reader.fieldnames if fn is not None]
        key_field = "key"
        if key_field not in fieldnames:
            raise ValueError("CSV must include a 'key' column")

        lang_cols = [fn for fn in fieldnames if fn != key_field]
        for lang in lang_cols:
            self._tables.setdefault(lang, {})

        for row in reader:
            if row.get("key") is None:
                continue
            key = str(row["key"]).strip()
            if not key:
                continue
            for lang in lang_cols:
                cell = row.get(lang)
                if cell is None:
                    continue
                self._tables[lang][key] = str(cell)
