"""
Read and write .mxap project archives: ZIP with ``metadata.json`` and ``sources/`` file copies.
"""

from __future__ import annotations

import json
import logging
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence, TypedDict, cast

_MXAP_FORMAT: Final[str] = "mxap"
_MXAP_VERSION: Final[int] = 1
_APP_ID: Final[str] = "materyx-asap"
_METADATA: Final[str] = "metadata.json"
_SOURCES: Final[str] = "sources/"
_UNSAFE: Final[re.Pattern[str]] = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

logger = logging.getLogger(__name__)


class MxapError(ValueError):
    """The archive is missing, corrupt, or does not follow the .mxap schema."""


class _FileMeta(TypedDict):
    id: str
    source_basename: str
    entry_path: str
    encoding: str


class MxapMetadataV1(TypedDict, total=False):
    """V1 top-level object inside ``metadata.json``."""

    format: str
    version: int
    app: str
    files: list[_FileMeta]
    language: str


def _safe_entry_filename(source_basename: str, index: int) -> str:
    """
    Build a unique, filesystem-safe name under ``sources/`` (index prefix avoids collisions).
    """
    if not isinstance(source_basename, str) or not isinstance(index, int):
        raise TypeError("source_basename must be str, index int")
    base = Path(source_basename).name
    cleaned = _UNSAFE.sub("_", base)
    cleaned = cleaned.strip(" .")
    if not cleaned:
        cleaned = "file"
    if len(cleaned) > 180:
        cleaned = cleaned[:180]
    return f"{index:03d}_{cleaned}"


def _assert_within_root(root: Path, path: Path) -> Path:
    """
    Resolve ``path`` and require it to stay under ``root`` (zip-slip guard).
    """
    try:
        r = root.resolve()
        p = path.resolve()
    except (OSError, ValueError) as exc:
        raise MxapError("invalid path in archive") from exc
    try:
        p.relative_to(r)
    except ValueError as exc:
        raise MxapError("invalid path in archive (outside project root)") from exc
    return p


def save_mxap(
    archive_path: Path,
    file_entries: Sequence[tuple[str, str, str]],
    language: str | None,
) -> None:
    """
    Write a ``.mxap`` ZIP: ``metadata.json`` plus one file per entry under ``sources/``.

    Parameters:
        archive_path: Destination (typically ends in ``.mxap``).
        file_entries: Ordered (``source_basename`` for display, file ``text``, ``encoding`` name for round-trip).
        language: Optional UI locale to restore (e.g. ``ru``).

    Raises:
        TypeError: If a parameter is invalid.
        MxapError: If a text cannot be encoded with the given ``encoding`` name.
    """
    if not isinstance(archive_path, Path):
        raise TypeError("archive_path must be pathlib.Path")
    if not isinstance(file_entries, Sequence) or not file_entries:
        raise TypeError("file_entries must be a non-empty sequence")
    meta_files: list[_FileMeta] = []
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for index, (base, text, enc) in enumerate(file_entries):
            if not isinstance(base, str) or not isinstance(text, str):
                raise TypeError("each entry must be (str basename, str text, str encoding)")
            if not isinstance(enc, str) or not enc.strip():
                raise TypeError("encoding must be a non-empty string")
            comp = _safe_entry_filename(base, index)
            rel = f"{_SOURCES}{comp}"
            try:
                data = text.encode(enc)
            except (LookupError, UnicodeEncodeError) as exc:
                raise MxapError(f"cannot encode with encoding {enc!r}") from exc
            zf.writestr(rel, data)
            meta_files.append(
                {
                    "id": str(index),
                    "source_basename": base,
                    "entry_path": rel,
                    "encoding": enc,
                }
            )
        top: MxapMetadataV1 = {
            "format": _MXAP_FORMAT,
            "version": _MXAP_VERSION,
            "app": _APP_ID,
            "files": meta_files,
        }
        if language is not None:
            if not isinstance(language, str) or not language.strip():
                raise TypeError("language must be a non-empty str when set")
            top["language"] = language
        payload = json.dumps(dict(top), ensure_ascii=False, indent=2) + "\n"
        zf.writestr(_METADATA, payload.encode("utf-8"))
    logger.info("Wrote mxap project: %s (%d file(s))", archive_path, len(file_entries))


def _read_metadata(zf: zipfile.ZipFile) -> MxapMetadataV1:
    if _METADATA not in zf.namelist():
        raise MxapError("missing metadata.json in archive")
    try:
        raw: bytes = zf.read(_METADATA)
    except (KeyError, OSError) as exc:
        raise MxapError("could not read metadata.json") from exc
    try:
        obj: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MxapError("metadata.json is not valid JSON") from exc
    if not isinstance(obj, dict):
        raise MxapError("metadata root must be an object")
    return cast(MxapMetadataV1, obj)


def _validate_metadata(meta: MxapMetadataV1) -> list[_FileMeta]:
    if meta.get("format") != _MXAP_FORMAT:
        raise MxapError("unknown mxap format value")
    ver = meta.get("version")
    if not isinstance(ver, int) or ver != _MXAP_VERSION:
        raise MxapError("unsupported mxap version")
    if meta.get("app") is not None and not isinstance(meta.get("app"), str):
        raise MxapError("invalid app field")
    files = meta.get("files")
    if not isinstance(files, list):
        raise MxapError("files must be a list")
    out: list[_FileMeta] = []
    for item in files:
        if not isinstance(item, dict):
            raise MxapError("each file entry must be an object")
        m = cast(_FileMeta, item)
        for key in ("id", "source_basename", "entry_path", "encoding"):
            if not isinstance(m.get(key), str) or not (m.get(key) or "").strip():
                raise MxapError("invalid file entry field")
        out.append(m)
    return out


@dataclass(frozen=True, slots=True)
class MxapLoadedFile:
    """
    One extracted data file: absolute path, encoding, and the original display basename.
    """

    path: Path
    encoding: str
    source_basename: str


def load_mxap(archive_path: Path, dest_dir: Path) -> tuple[str | None, list[MxapLoadedFile]]:
    """
    Extract a ``.mxap`` archive to ``dest_dir`` and return UI language and ordered file list.

    Parameters:
        archive_path: Path to a ``.mxap`` (ZIP) file.
        dest_dir: Existing or creatable root directory; member paths are written only under it.

    Returns:
        (``language`` or ``None``, list of :class:`MxapLoadedFile` in project order).

    Raises:
        TypeError: If parameters are wrong.
        MxapError: If the archive is invalid, unsafe, or unreadable.
    """
    if not isinstance(archive_path, Path):
        raise TypeError("archive_path must be pathlib.Path")
    if not isinstance(dest_dir, Path):
        raise TypeError("dest_dir must be pathlib.Path")
    if not archive_path.is_file():
        raise MxapError("project file does not exist or is not a file")
    dest_dir.mkdir(parents=True, exist_ok=True)
    root = dest_dir.resolve()
    try:
        zf = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile as exc:
        raise MxapError("file is not a valid archive") from exc
    with zf:
        meta = _read_metadata(zf)
        file_list = _validate_metadata(meta)
        language: str | None = meta.get("language")
        if language is not None and (not isinstance(language, str) or not language.strip()):
            raise MxapError("invalid language in metadata")
        if language is not None:
            language = language.strip()
        loaded: list[MxapLoadedFile] = []
        for fe in file_list:
            rel = fe["entry_path"]
            if ".." in Path(rel).parts or rel.startswith(("/", "\\")):
                raise MxapError("unsafe entry_path in metadata")
            enc = fe["encoding"]
            base = fe["source_basename"]
            target = _assert_within_root(root, root / rel)
            if rel not in zf.namelist():
                raise MxapError(
                    f"missing data file in archive: {rel}",
                )
            try:
                data = zf.read(rel)
            except (KeyError, OSError) as exc:
                raise MxapError("could not read data from archive") from exc
            try:
                _ = data.decode(enc)
            except (LookupError, UnicodeError) as exc:
                raise MxapError(f"cannot decode {rel} with encoding {enc!r}") from exc
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            loaded.append(
                MxapLoadedFile(
                    path=target,
                    encoding=enc,
                    source_basename=base,
                )
            )
    logger.info("Loaded mxap: %d file(s) under %s", len(loaded), dest_dir)
    return language, loaded
