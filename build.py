# build.py
# สคริปต์สำหรับสร้างไฟล์ .exe ด้วย Nuitka โดยจะทำการเตรียมไฟล์และโฟลเดอร์ที่จำเป็นก่อน จากนั้นจะเรียกคำสั่ง Nuitka เพื่อทำการคอมไพล์ไฟล์ main.py เป็น .exe พร้อมกับตั้งค่า icon และรวมแพ็กเกจที่จำเป็น
# หมายเหตุ: ก่อนที่จะรันสคริปต์นี้ ควรติดตั้ง Nuitka และ dependencies ที่จำเป็นทั้งหมดแล้ว และควรตรวจสอบให้แน่ใจว่าไฟล์ main.py และ icon.ico อยู่ในโฟลเดอร์เดียวกับ build.py

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

        f"--output-dir={BUILD_DIR}",

        "--enable-plugin=pyqt6",
        "--windows-console-mode=disable",  # หากพบปัญหาเกี่ยวกับ console ให้ลองเปลี่ยนเป็น enable

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


