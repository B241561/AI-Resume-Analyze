# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = Path(SPECPATH)
icon_path = project_dir / "assets" / "app_icon.ico"

# Build the application natively on the current OS. The ICO is only used where
# PyInstaller can apply a Windows executable icon safely.
icon_value = str(icon_path) if sys.platform == "win32" and icon_path.exists() else None

datas = [("assets", "assets")]
datas += collect_data_files("customtkinter")
datas += collect_data_files("certifi")

a = Analysis(
    ["app.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("groq") + collect_submodules("docx") + collect_submodules("fitz") + collect_submodules("keyring"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ResumeAnalyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_value,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ResumeAnalyzer_Portable",
)
