"""
Round-trip tests for .mxap project archives.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from source.project.mxap_io import MxapError, load_mxap, save_mxap

_TEXT_A = "Micromeritics\nSAMPLE ID: S-A\n"
_TEXT_B = "Micromeritics\nSAMPLE ID: S-B\n"


def test_save_load_round_trip_text_order(tmp_path: Path) -> None:
    """Save two text blobs and reload: same count, order, and text."""
    out = tmp_path / "p.mxap"
    ext = tmp_path / "ex"
    ext.mkdir()
    save_mxap(
        out,
        [
            ("a.txt", _TEXT_A, "utf-8"),
            ("b.txt", _TEXT_B, "utf-8"),
        ],
        language="en",
    )
    assert out.is_file()
    lang, files = load_mxap(out, ext)
    assert lang == "en"
    assert len(files) == 2
    p0, p1 = files[0].path, files[1].path
    assert p0.read_text(encoding=files[0].encoding) == _TEXT_A
    assert p1.read_text(encoding=files[1].encoding) == _TEXT_B
    assert files[0].source_basename == "a.txt"
    assert files[1].source_basename == "b.txt"
    assert "sources" in p0.as_posix()


def test_reject_non_mxap_magic(tmp_path: Path) -> None:
    p = tmp_path / "x.mxap"
    p.write_text("not a zip", encoding="utf-8")
    ext = tmp_path / "d"
    with pytest.raises(MxapError):
        load_mxap(p, ext)
