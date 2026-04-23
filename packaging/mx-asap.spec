# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: Materyx ASAP Analyzer (PySide6, matplotlib, openpyxl, bundled `source.resources`).

import os
import sys

# SPECPATH is set by PyInstaller; fall back to __file__. Resolve repo root via pyproject.toml.
try:
    _sp = os.path.abspath(SPECPATH)  # type: ignore[name-defined]  # noqa: F821
except NameError:
    _sp = os.path.abspath(__file__)
_c = _sp
while _c and _c != os.path.dirname(_c):
    if os.path.isfile(os.path.join(_c, "pyproject.toml")):
        _ROOT = _c
        break
    _c = os.path.normpath(os.path.join(_c, os.pardir))
else:
    raise SystemExit("mx-asap.spec: could not find pyproject.toml above the spec file")

from PyInstaller.building.build_main import (  # noqa: E402
    Analysis,
    PYZ,
    EXE,
    COLLECT,
    BUNDLE,
)
from PyInstaller.utils.hooks import (  # noqa: E402
    collect_all,
    collect_data_files,
    collect_submodules,
)

block_cipher = None

_pyside_d, _pyside_b, _pyside_h = collect_all("PySide6", include_py_files=True)
_mpl = collect_data_files("matplotlib", include_py_files=True)

a_datas: list = [
    (os.path.join(_ROOT, "source", "resources"), "source/resources"),
] + _pyside_d + _mpl
a_binaries: list = list(_pyside_b)

hiddenimports: list = list(_pyside_h)
for _m in (
    "openpyxl",
    "openpyxl.cell",
    "openpyxl.workbook",
    "openpyxl.writer",
    "openpyxl.styles",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qtagg",
):
    if _m not in hiddenimports:
        hiddenimports.append(_m)
for _sub in collect_submodules("source"):
    if _sub not in hiddenimports:
        hiddenimports.append(_sub)

a = Analysis(
    [os.path.join(_ROOT, "source", "__main__.py")],
    pathex=[_ROOT],
    binaries=a_binaries,
    datas=a_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# macOS: onedir + BUNDLE; Windows and Linux: one file without console
if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="mx-asap",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="mx-asap",
    )
    BUNDLE(
        coll,
        name="mx-asap.app",
        icon=None,
        bundle_identifier="com.materyx.mx-asap",
    )
else:
    EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="mx-asap",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        console=False,
        onefile=True,
    )
