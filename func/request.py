import requests
import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


def get_config(url: str, timeout: int = 10) -> Optional[dict]:
    """
    ดึงไฟล์ JSON config จาก URL
    
    Returns:
        dict ถ้าสำเร็จ, None ถ้าล้มเหลว
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "MySampLauncher/1.0"},  # ช่วยให้บางเซิร์ฟเวอร์ไม่บล็อก
        )
        response.raise_for_status()
        
        # ตรวจสอบว่าเป็น JSON จริง ๆ
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("ข้อมูลที่ได้ไม่ใช่ JSON object")
            
        return data

    except requests.exceptions.Timeout:
        print(f"หมดเวลาในการดึง config จาก: {url}")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {e.response.status_code}: {url}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"ข้อผิดพลาดการเชื่อมต่อ: {e}")
        return None
        
    except ValueError as e:
        print(f"JSON ไม่ถูกต้อง: {e}")
        return None
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดไม่คาดคิดในการดึง config: {type(e).__name__} - {e}")
        return None


def save_image_from_url(
    url: str,
    folder: str = "assets",
    filename: Optional[str] = None,
    timeout: int = 15
) -> Optional[str]:
    """
    ดาวน์โหลดรูปภาพจาก URL และบันทึกในโฟลเดอร์ที่กำหนด
    
    Parameters:
        url      : ลิงก์รูปภาพ
        folder   : โฟลเดอร์ที่จะบันทึก (จะสร้างอัตโนมัติ)
        filename : ชื่อไฟล์ที่ต้องการ (ถ้าไม่ระบุ จะใช้ชื่อจาก URL)
        timeout  : เวลารอสูงสุด (วินาที)
    
    Returns:
        path ที่บันทึกสำเร็จ หรือ None ถ้าล้มเหลว
    """
    try:
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        save_dir = Path(folder).resolve()
        save_dir.mkdir(parents=True, exist_ok=True)

        # ดึงชื่อไฟล์จาก URL ถ้าไม่ได้ระบุ filename
        if not filename:
            parsed = urlparse(url)
            path_part = parsed.path.strip('/')
            if path_part:
                filename = os.path.basename(path_part)
            else:
                # fallback ถ้า URL ไม่มี path ชัดเจน (เช่น data:image/... หรือ query string เท่านั้น)
                filename = "downloaded_image.png"

        # ป้องกันชื่อไฟล์ที่อันตรายหรือมี path traversal
        filename = os.path.basename(filename)  # ตัดส่วน path ออกให้เหลือแค่ชื่อไฟล์
        if not filename:
            filename = "unnamed_image.png"

        filepath = save_dir / filename

        # ถ้าไฟล์ชื่อซ้ำ ให้เพิ่มเลขต่อท้าย (เช่น image(1).png)
        base, ext = os.path.splitext(filename)
        counter = 1
        while filepath.exists():
            new_name = f"{base}({counter}){ext}"
            filepath = save_dir / new_name
            counter += 1

        # ดาวน์โหลดแบบ streaming
        with requests.get(
            url,
            stream=True,
            timeout=(5, timeout),  # connect 5 วินาที, read timeout ตามที่ระบุ
            headers={"User-Agent": "MySampLauncher/1.0"}
        ) as response:
            
            response.raise_for_status()
            
            # ตรวจสอบว่าเป็นไฟล์ภาพจริง ๆ (optional แต่แนะนำ)
            content_type = response.headers.get("Content-Type", "").lower()
            if "image" not in content_type and not filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                raise ValueError(f"URL นี้ไม่ใช่ไฟล์ภาพ: {content_type}")

            with filepath.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # กรอง chunk ว่าง
                        f.write(chunk)

        print(f"บันทึกรูปภาพสำเร็จ: {filepath}")
        return str(filepath)

    except requests.exceptions.RequestException as e:
        print(f"ดาวน์โหลดรูปภาพล้มเหลว: {url} → {e}")
        return None

    except OSError as e:
        print(f"ข้อผิดพลาดการเขียนไฟล์: {filepath} → {e}")
        return None

    except Exception as e:
        print(f"เกิดข้อผิดพลาดไม่คาดคิดในการดาวน์โหลดรูปภาพ: {type(e).__name__} - {e}")
        return None


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # ทดสอบดึง config
    config = get_config("https://example.com/config.json")
    if config:
        print("Config:", config)

    # ทดสอบดาวน์โหลดรูปภาพ
    saved_path = save_image_from_url(
        "https://example.com/some-image.jpg",
        folder="assets/backgrounds",
        filename="welcome_bg.jpg"  # ถ้าต้องการกำหนดชื่อเอง
    )
    if saved_path:
        print(f"ไฟล์ถูกบันทึกที่: {saved_path}")