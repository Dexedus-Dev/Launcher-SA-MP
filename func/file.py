from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
from pathlib import Path
import zipfile
import rarfile
from typing import Optional


class ExtractThread(QThread):
    """
    Thread สำหรับแตกไฟล์ .zip หรือ .rar โดยไม่ทำให้ UI ค้าง
    ส่งสัญญาณเมื่อเสร็จสิ้น (สำเร็จ/ล้มเหลว) พร้อมข้อความ
    """
    # สัญญาณ: (สำเร็จหรือไม่, ข้อความผลลัพธ์หรือ error)
    finished = pyqtSignal(bool, str)
    # ถ้าต้องการรายงานความคืบหน้าเพิ่มเติมในอนาคต สามารถเพิ่ม signal ได้

    def __init__(self, file_path: str | Path, extract_to: Optional[str | Path] = None):
        super().__init__()
        self.file_path = Path(file_path).resolve()      # ใช้ Path แปลงให้เป็น absolute path
        self.extract_to = Path(extract_to) if extract_to else self.file_path.with_suffix('')

    def run(self):
        """
        ทำงานใน thread แยก → แตกไฟล์ตามนามสกุล
        """
        extract_to = self.extract_to
        extract_to.mkdir(parents=True, exist_ok=True)

        ext = self.file_path.suffix.lower()

        try:
            if not self.file_path.is_file():
                raise FileNotFoundError(f"ไม่พบไฟล์: {self.file_path}")

            if ext == ".zip":
                with zipfile.ZipFile(self.file_path, 'r') as z:
                    # ตรวจสอบก่อนว่าไฟล์ zip ไม่เสีย
                    bad_file = z.testzip()
                    if bad_file:
                        raise zipfile.BadZipFile(f"ไฟล์ ZIP เสียหายที่: {bad_file}")
                    z.extractall(extract_to)

            elif ext in (".rar", ".cbr"):
                # rarfile ต้องการ unrar library ติดตั้งในระบบด้วย
                with rarfile.RarFile(self.file_path, 'r') as r:
                    r.extractall(extract_to)

            else:
                raise ValueError(f"ไม่รองรับนามสกุลไฟล์: {ext}\n(รองรับ .zip และ .rar เท่านั้น)")

            # ตรวจสอบว่าแตกสำเร็จจริงหรือไม่ (โฟลเดอร์มีไฟล์เพิ่มขึ้น)
            if len(list(extract_to.iterdir())) == 0:
                raise RuntimeError("แตกไฟล์แล้วแต่โฟลเดอร์ว่างเปล่า")

            self.finished.emit(True, str(extract_to))

        except rarfile.Error as e:
            self.finished.emit(False, f"ข้อผิดพลาด RAR: {e}\n(ตรวจสอบว่าได้ติดตั้ง unrar แล้วหรือไม่)")

        except zipfile.BadZipFile as e:
            self.finished.emit(False, f"ไฟล์ ZIP เสียหาย: {e}")

        except PermissionError as e:
            self.finished.emit(False, f"ไม่มีสิทธิ์เข้าถึงไฟล์/โฟลเดอร์: {e}")

        except Exception as e:
            self.finished.emit(False, f"เกิดข้อผิดพลาด: {type(e).__name__} - {str(e)}")


def find_gta_sa(start_path: str | Path) -> Optional[Path]:
    """
    ค้นหาไฟล์ gta_sa.exe แบบ recursive จาก start_path
    คืน Path หรือ None ถ้าไม่พบ
    """
    start_path = Path(start_path).resolve()
    if not start_path.exists():
        return None

    target = "gta_sa.exe"

    try:
        for path in start_path.rglob(target):
            if path.is_file():
                return path.resolve()
    except PermissionError:
        print(f"ข้ามบางโฟลเดอร์เนื่องจากไม่มีสิทธิ์: {start_path}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะค้นหา: {e}")

    return None

def launch_samp(gta_path, ip, port):
    """
    เปิด samp.exe พร้อมเชื่อมต่อเซิร์ฟเวอร์ที่ระบุ
    """
    gta_dir = Path(gta_path).parent
    samp_exe = gta_dir / "samp.exe"

    if not samp_exe.exists():
        print("❌ samp.exe not found:", samp_exe)
        return False

    server = f"{ip}:{port}"

    print("Launching:", samp_exe, server)

    subprocess.Popen(
        [str(samp_exe), server],
        cwd=str(gta_dir)
    )

    return True

def clean_assets(folder: str | Path = "assets", keep_name: str = "background") -> None:
    """
    ลบไฟล์ในโฟลเดอร์ assets ยกเว้นไฟล์ที่ชื่อตรงกับ keep_name (ไม่สนนามสกุล)
    ตัวอย่าง: background.png, background.jpg จะไม่ถูกลบ
    """
    folder = Path(folder).resolve()

    if not folder.is_dir():
        print(f"ไม่พบโฟลเดอร์: {folder}")
        return

    deleted_count = 0
    failed_count = 0

    for path in folder.iterdir():
        if not path.is_file():
            continue  # ข้ามโฟลเดอร์และ symlink

        name_without_ext = path.stem  # ชื่อไฟล์ไม่รวม extension

        if name_without_ext == keep_name:
            continue  # ข้ามไฟล์ที่ต้องการเก็บไว้

        try:
            path.unlink(missing_ok=True)
            deleted_count += 1
        except PermissionError:
            print(f"ไม่มีสิทธิ์ลบ: {path}")
            failed_count += 1
        except Exception as e:
            print(f"ลบไม่สำเร็จ {path}: {e}")
            failed_count += 1

    if deleted_count > 0 or failed_count > 0:
        print(f"clean_assets เสร็จสิ้น: ลบสำเร็จ {deleted_count} ไฟล์, ล้มเหลว {failed_count} ไฟล์")


# ตัวอย่างการใช้งาน (comment เท่านั้น)
"""
# แตกไฟล์
extractor = ExtractThread("mods/samp.zip", "extracted/mods")
extractor.finished.connect(lambda success, msg: print("สำเร็จ" if success else "ล้มเหลว", msg))
extractor.start()

# ค้นหา gta_sa.exe
gta_path = find_gta_sa("C:/Games")
if gta_path:
    print("พบ GTA SA ที่:", gta_path)

# ล้างไฟล์ใน assets
clean_assets("assets", keep_name="bg")

# เปิด samp.exe พร้อมเชื่อมต่อเซิร์ฟเวอร์
launch_samp("C:/Games/GTA San Andreas/gta_sa.exe", "127.1.1", "7777")
"""