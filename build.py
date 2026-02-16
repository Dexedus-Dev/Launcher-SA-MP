import os
import sys
import shutil
import subprocess
from pathlib import Path

# ===== CONFIG =====
MAIN_FILE = "main.py"
ICON_PATH = "icon.ico"
OUTPUT_NAME = "Launcher"
LAUNCHER_SETTING_LINK = "http://127.0.0.1/launcher_setting.json"
BUILD_DIR = Path("build")
TEMP_MAIN = BUILD_DIR / MAIN_FILE
# ==================


def replace_text_in_file(file_path, old_text, new_text):
    path = Path(file_path)
    data = path.read_text(encoding="utf-8")
    data = data.replace(old_text, new_text)
    path.write_text(data, encoding="utf-8")


def prepare_build_dir():
    # ล้าง build เก่า (สำคัญ)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    BUILD_DIR.mkdir(parents=True)


def build():
    if not Path(MAIN_FILE).exists():
        print("❌ ไม่พบไฟล์:", MAIN_FILE)
        return

    prepare_build_dir()

    # copy main ไป build/
    shutil.copy(MAIN_FILE, TEMP_MAIN)

    # inject config link
    replace_text_in_file(TEMP_MAIN, "$SETTINGS_LINK", LAUNCHER_SETTING_LINK)

    cmd = [
        sys.executable, "-m", "nuitka",

        str(TEMP_MAIN),

        "--standalone",
        "--onefile",

        # ⭐ บอก Nuitka ให้ปล่อย output ลง build/
        f"--output-dir={BUILD_DIR}",

        # GUI
        "--enable-plugin=pyqt6",
        "--windows-disable-console", # ไม่แสดง console ตอนรัน (ถ้าอยากเห็นให้เอาอันนี้ออก)

        f"--output-filename={OUTPUT_NAME}.exe",
        f"--windows-icon-from-ico={ICON_PATH}",

        "--include-package=func",
        "--include-data-dir=assets=assets",

        "--lto=yes",

        "--nofollow-import-to=PyQt6.QtWebEngine",
        "--nofollow-import-to=PyQt6.QtMultimedia",
    ]

    print("\n🚀 Building with Nuitka...\n")
    print(" ".join(cmd))
    print("\n============================\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ BUILD SUCCESS!")
        print("📦 Output:", BUILD_DIR / f"{OUTPUT_NAME}.exe")
    else:
        print("\n❌ BUILD FAILED")


if __name__ == "__main__":
    build()
