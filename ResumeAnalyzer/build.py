from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
OUTPUT_DIR = DIST_DIR / "ResumeAnalyzer_Portable"


def remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def main() -> int:
    print("Building AI Resume Analyzer with PyInstaller...")

    for path in [BUILD_DIR / "ResumeAnalyzer", BUILD_DIR / "ResumeAnalyzer_Portable", OUTPUT_DIR]:
        remove(path)

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "temp").mkdir(exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "ResumeAnalyzer.spec",
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    exe_name = "ResumeAnalyzer.exe" if sys.platform == "win32" else "ResumeAnalyzer"
    exe_path = OUTPUT_DIR / exe_name
    internal_path = OUTPUT_DIR / "_internal"

    if not exe_path.exists() or not internal_path.exists():
        raise RuntimeError(f"PyInstaller finished, but expected output was not found: {exe_path}")

    copy_tree(ROOT / "assets", OUTPUT_DIR / "assets")
    copy_tree(ROOT / "reports", OUTPUT_DIR / "reports")
    copy_tree(ROOT / "temp", OUTPUT_DIR / "temp")
    shutil.copy2(ROOT / ".env.example", OUTPUT_DIR / ".env.example")
    shutil.copy2(ROOT / "README.txt", OUTPUT_DIR / "README.txt")

    print(f"Build complete: {OUTPUT_DIR}")
    print(f"Executable: {exe_path}")
    print("This script builds a native executable for the current operating system.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
