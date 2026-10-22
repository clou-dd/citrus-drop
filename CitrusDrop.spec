# Windows에서 build.cmd로 실행합니다. 한 폴더 형태로 Qt/PDFium DLL을 함께 배포합니다.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata

base = Path(SPECPATH)
datas = [(str(base / "assets"), "assets"), (str(base / "THIRD_PARTY_NOTICES.md"), ".")]
datas += [(str(base / name), ".") for name in ("LICENSE", "LICENSE.txt") if (base / name).is_file()]
datas += collect_data_files("reportlab")
datas += collect_data_files("pypdfium2") + collect_data_files("pypdfium2_raw")
for distribution in ("PySide6", "PySide6-Essentials", "shiboken6", "Pillow", "reportlab", "pypdfium2"):
    datas += copy_metadata(distribution)

a = Analysis(
    [str(base / "main.py")],
    pathex=[str(base)],
    binaries=collect_dynamic_libs("pypdfium2_raw"),
    datas=datas,
    hiddenimports=collect_submodules("reportlab.pdfbase"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2"],
    noarchive=False,
)
pyz = PYZ(a.pure)
icon_path = base / "assets" / "icon.ico"
if not icon_path.is_file():
    raise FileNotFoundError("Run tools/generate_icons.py before building CitrusDrop.spec")
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="CitrusDrop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CitrusDrop")
