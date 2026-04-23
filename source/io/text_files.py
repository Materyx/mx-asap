"""
Read text files with encoding fallbacks suitable for legacy instrument exports.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_text_file_best_effort(path: Path) -> tuple[str, str]:
    """
    Read a text file using UTF-8 first, then Windows-1252 as a fallback.

    Args:
        path: Filesystem path to an existing file.

    Returns:
        Tuple of (text, encoding_used).

    Raises:
        TypeError: If path is not a Path.
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
        UnicodeError: If decoding fails for all attempted encodings.
    """
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    if not path.exists():
        raise FileNotFoundError(str(path))
    if not path.is_file():
        raise ValueError("path must point to a file")

    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            logger.debug("Decoded %s using %s", path, encoding)
            return text, encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Unable to decode file: {path}")
