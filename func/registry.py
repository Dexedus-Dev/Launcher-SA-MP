import winreg
import os
from pathlib import Path
from typing import Optional, Union


class SampRegistry:
    """
    จัดการ Registry สำหรับ Launcher SA-MP / GTA SA
    - เก็บ/ดึง version ของ launcher
    - เก็บ/ดึง path ของ gta_sa.exe
    - เก็บ/ดึง PlayerName (ตามมาตรฐาน SA-MP)
    
    ใช้เฉพาะ HKEY_CURRENT_USER → ไม่ต้องสิทธิ์ admin
    """

    def __init__(self, launcher_name: str = "MySampLauncher"):
        self.root = winreg.HKEY_CURRENT_USER
        # เส้นทางสำหรับข้อมูลของ launcher เราเอง
        self.app_reg_path = fr"SOFTWARE\{launcher_name}"
        # เส้นทางมาตรฐานของ SA-MP client (ที่เกมจริงใช้)
        self.samp_reg_path = r"SOFTWARE\SAMP"

    # -------------------------------------------------------------------------
    #                   ส่วนจัดการข้อมูลของ Launcher เรา
    # -------------------------------------------------------------------------

    def _open_app_key(self, create: bool = False) -> Optional[winreg.HKEYType]:
        """ เปิด key ของ launcher (สร้างใหม่ถ้า create=True) """
        try:
            if create:
                return winreg.CreateKey(self.root, self.app_reg_path)
            else:
                return winreg.OpenKey(self.root, self.app_reg_path, 0, winreg.KEY_READ)
        except FileNotFoundError:
            return None
        except OSError as e:
            print(f"เปิด registry key ล้มเหลว: {e}")
            return None

    def set_version(self, version: str) -> bool:
        """ บันทึก version ของ launcher """
        key = self._open_app_key(create=True)
        if not key:
            return False
        try:
            winreg.SetValueEx(key, "version", 0, winreg.REG_SZ, version.strip())
            return True
        except Exception as e:
            print(f"บันทึก version ล้มเหลว: {e}")
            return False
        finally:
            winreg.CloseKey(key)

    def get_version(self) -> Optional[str]:
        """ ดึง version ของ launcher """
        key = self._open_app_key(create=False)
        if not key:
            return None
        try:
            value, _ = winreg.QueryValueEx(key, "version")
            return value.strip()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"ดึง version ล้มเหลว: {e}")
            return None
        finally:
            winreg.CloseKey(key)

    def set_app_value(self, name: str, value: str) -> bool:
        """ บันทึกค่าต่าง ๆ ลงใน registry ของ launcher (ทั่วไป) """
        key = self._open_app_key(create=True)
        if not key:
            return False
        try:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value).strip())
            return True
        except Exception as e:
            print(f"บันทึกค่า {name} ล้มเหลว: {e}")
            return False
        finally:
            winreg.CloseKey(key)

    def get_app_value(self, name: str) -> Optional[str]:
        """ ดึงค่าต่าง ๆ จาก registry ของ launcher """
        key = self._open_app_key(create=False)
        if not key:
            return None
        try:
            value, _ = winreg.QueryValueEx(key, name)
            return value.strip()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"ดึงค่า {name} ล้มเหลว: {e}")
            return None
        finally:
            winreg.CloseKey(key)

    # -------------------------------------------------------------------------
    #                   ส่วนจัดการข้อมูล SA-MP มาตรฐาน
    # -------------------------------------------------------------------------

    def _open_samp_key(self, create: bool = False) -> Optional[winreg.HKEYType]:
        """ เปิด key SOFTWARE\\SAMP (สร้างใหม่ถ้า create=True) """
        try:
            if create:
                return winreg.CreateKey(self.root, self.samp_reg_path)
            else:
                return winreg.OpenKey(self.root, self.samp_reg_path, 0, winreg.KEY_READ)
        except FileNotFoundError:
            return None
        except OSError as e:
            print(f"เปิด SAMP registry ล้มเหลว: {e}")
            return None

    def save_gta_path(self, path: Union[str, Path]) -> bool:
        """
        บันทึก path ของ gta_sa.exe ลง registry (เหมือนที่ SA-MP client ทำ)
        """
        path_str = str(Path(path).resolve())  # แปลงเป็น absolute path เสมอ
        if not os.path.isfile(path_str):
            print(f"ไฟล์ไม่ถูกต้อง: {path_str}")
            return False

        key = self._open_samp_key(create=True)
        if not key:
            return False

        try:
            winreg.SetValueEx(key, "gta_sa_exe", 0, winreg.REG_SZ, path_str)
            return True
        except Exception as e:
            print(f"บันทึก gta_sa_exe ล้มเหลว: {e}")
            return False
        finally:
            winreg.CloseKey(key)

    def get_gta_path(self) -> Optional[str]:
        """ ดึง path ของ gta_sa.exe จาก registry SA-MP """
        key = self._open_samp_key(create=False)
        if not key:
            return None
        try:
            value, _ = winreg.QueryValueEx(key, "gta_sa_exe")
            path = Path(value).resolve()
            return str(path) if path.is_file() else None
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"ดึง gta_sa_exe ล้มเหลว: {e}")
            return None
        finally:
            winreg.CloseKey(key)

    def save_player_name(self, name: str) -> bool:
        """ บันทึกชื่อผู้เล่น (PlayerName) ลง registry SA-MP """
        name = name.strip()
        if not name or len(name) > 24:  # SA-MP จำกัดชื่อยาวสุด 24 ตัวอักษร
            print(f"ชื่อไม่ถูกต้องหรือยาวเกิน: '{name}'")
            return False

        key = self._open_samp_key(create=True)
        if not key:
            return False

        try:
            winreg.SetValueEx(key, "PlayerName", 0, winreg.REG_SZ, name)
            return True
        except Exception as e:
            print(f"บันทึก PlayerName ล้มเหลว: {e}")
            return False
        finally:
            winreg.CloseKey(key)

    def get_player_name(self) -> Optional[str]:
        """ ดึงชื่อผู้เล่นจาก registry SA-MP """
        key = self._open_samp_key(create=False)
        if not key:
            return None
        try:
            value, _ = winreg.QueryValueEx(key, "PlayerName")
            return value.strip()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"ดึง PlayerName ล้มเหลว: {e}")
            return None
        finally:
            winreg.CloseKey(key)


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    reg = SampRegistry(launcher_name="CoolSampLauncher")

    # Launcher version
    reg.set_version("1.2.3")
    print("Version:", reg.get_version())

    # GTA Path
    reg.save_gta_path(r"C:\Games\GTA San Andreas\gta_sa.exe")
    print("GTA Path:", reg.get_gta_path())

    # Player Name
    reg.save_player_name("Master_TH")
    print("Player Name:", reg.get_player_name())