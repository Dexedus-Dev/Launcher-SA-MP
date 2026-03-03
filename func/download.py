import requests
import certifi
import hashlib
from pathlib import Path
from typing import Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread


def file_hash(path: str | Path, algo: str = "sha256", chunk: int = 1024 * 1024) -> str:
    """
    คำนวณ hash ของไฟล์ (ค่าเริ่มต้น sha256)
    อ่านไฟล์แบบ streaming เพื่อรองรับไฟล์ขนาดใหญ่
    """
    try:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"ไม่พบไฟล์: {path}")

        h = hashlib.new(algo)
        with path.open("rb") as f:
            while True:
                data = f.read(chunk)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    except Exception as e:
        raise RuntimeError(f"คำนวณ hash ไม่สำเร็จ: {e}")


class DownloadWorker(QObject):
    """
    Worker สำหรับดาวน์โหลดไฟล์ใน thread แยก
    รองรับการรายงานความคืบหน้า + ยกเลิกการดาวน์โหลด
    """
    progress = pyqtSignal(int)          # ส่งเปอร์เซ็นต์ (0-100)
    finished = pyqtSignal(str)          # ส่ง path ที่บันทึกสำเร็จ
    error = pyqtSignal(str)             # ส่งข้อความ error
    canceled = pyqtSignal()             # แจ้งเมื่อถูกยกเลิกโดยผู้ใช้

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self._running = True
        self._canceled = False

    def cancel(self):
        """ เรียกเมื่อต้องการยกเลิกการดาวน์โหลด """
        self._running = False
        self._canceled = True

    def run(self):
        """
        ฟังก์ชันหลักที่ทำงานใน thread แยก
        """
        try:
            # ใช้ streaming + timeout ที่เหมาะสม
            with requests.get(
                self.url,
                stream=True,
                timeout=(10, 30),           # connect=10s, read=30s
                verify=certifi.where()
            ) as response:

                response.raise_for_status()

                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                last_percent = -1

                # สร้าง parent directory ถ้ายังไม่มี
                Path(self.save_path).parent.mkdir(parents=True, exist_ok=True)

                with open(self.save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not self._running:
                            # ถูกยกเลิก → ลบไฟล์ที่ดาวน์โหลดไม่ครบ
                            try:
                                Path(self.save_path).unlink(missing_ok=True)
                            except:
                                pass
                            if self._canceled:
                                self.canceled.emit()
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                # ลดการ emit ซ้ำซ้อน (ป้องกัน UI กระตุก)
                                if percent != last_percent:
                                    self.progress.emit(percent)
                                    last_percent = percent

            # ดาวน์โหลดสำเร็จ
            self.finished.emit(self.save_path)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"ข้อผิดพลาดการเชื่อมต่อ: {e}")

        except OSError as e:
            self.error.emit(f"ข้อผิดพลาดการเขียนไฟล์: {e}")

        except Exception as e:
            self.error.emit(f"เกิดข้อผิดพลาดไม่คาดคิด: {type(e).__name__} - {e}")


class Downloader:
    """
    คลาส wrapper ใช้ง่ายจาก MainWindow หรือ UI อื่น ๆ
    จัดการ thread + worker ให้อัตโนมัติ
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.thread: QThread | None = None
        self.worker: DownloadWorker | None = None

    def start_download(
        self,
        url: str,
        save_path: str,
        on_progress: Callable[[int], None],
        on_finished: Callable[[str], None],
        on_error: Callable[[str], None],
        on_canceled: Optional[Callable[[], None]] = None
    ):
        """
        เริ่มดาวน์โหลดไฟล์
        """
        if self.thread and self.thread.isRunning():
            return  # ยังมีงานเก่าอยู่ ห้ามเริ่มใหม่ซ้ำ

        self.thread = QThread()
        self.worker = DownloadWorker(url, save_path)

        # ย้าย worker ไปทำงานใน thread แยก
        self.worker.moveToThread(self.thread)

        # เชื่อมสัญญาณ
        self.worker.progress.connect(on_progress)
        self.worker.finished.connect(on_finished)
        self.worker.error.connect(on_error)
        if on_canceled:
            self.worker.canceled.connect(on_canceled)

        # เมื่อ thread เริ่ม → เรียก run()
        self.thread.started.connect(self.worker.run)

        # เมื่อ worker เสร็จ (ทั้งสำเร็จและ error) → ปิด thread
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.canceled.connect(self.thread.quit)

        # ทำความสะอาดเมื่อ thread จบ
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.canceled.connect(self.worker.deleteLater)

        # เริ่ม thread
        self.thread.start()

    def cancel(self):
        """
        ยกเลิกการดาวน์โหลดปัจจุบัน (ถ้ามี)
        """
        if self.worker:
            self.worker.cancel()

    def is_running(self) -> bool:
        """ ตรวจสอบว่ากำลังดาวน์โหลดอยู่หรือไม่ """
        return self.thread is not None and self.thread.isRunning()

    def cleanup(self):
        """ เรียกเมื่อต้องการเคลียร์ทรัพยากร (เช่น ปิดโปรแกรม) """
        if self.is_running():
            self.cancel()
        if self.thread and not self.thread.isFinished():
            self.thread.quit()
            self.thread.wait(3000)  # รอสูงสุด 3 วินาที


# ตัวอย่างการใช้งาน (comment เท่านั้น)
"""
downloader = Downloader()

def on_progress(percent):
    print(f"ดาวน์โหลด {percent}%")

def on_done(path):
    print(f"ดาวน์โหลดสำเร็จ → {path}")

def on_error(msg):
    print(f"เกิดข้อผิดพลาด: {msg}")

downloader.start_download(
    url="https://example.com/bigfile.zip",
    save_path="downloads/bigfile.zip",
    on_progress=on_progress,
    on_finished=on_done,
    on_error=on_error
)

# ระหว่างดาวน์โหลด เรียกยกเลิกได้
# downloader.cancel()
"""