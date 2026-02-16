# SAMP Custom Launcher  
ตัวเรียกใช้งาน (Launcher) แบบกำหนดเองสำหรับเซิร์ฟเวอร์ San Andreas Multiplayer (SAMP)

![Preview Launcher](image.png)  
*(ใส่ภาพตัวอย่างจริงของ launcher ตรงนี้แนะนำ)*

## คุณสมบัติหลัก

- UI สวยงามสไตล์ Glassmorphism + Gradient
- แสดงสถานะเซิร์ฟเวอร์ (ออนไลน์/ออฟไลน์ + จำนวนผู้เล่น)
- ดาวน์โหลดและอัปเดตไฟล์เกมอัตโนมัติ (ตรวจสอบ SHA256)
- แสดงข่าวสาร / อัปเดตจากไฟล์ JSON
- บันทึกชื่อผู้เล่น (Player Name) ลง Registry
- ปุ่มเข้าสู่ Discord + เข้าเกมโดยตรง
- Notification แบบ slide-in สวย ๆ
- หน้าต่างแบบ Frameless (ไม่มี title bar ปกติ)

## ความต้องการของระบบ

- Windows 10 / 11 (64-bit)
- Python 3.9+ (แนะนำ 3.11–3.12)
- PyQt6
- GTA San Andreas + SAMP client ที่ติดตั้งแล้ว

## การติดตั้งและใช้งาน (สำหรับผู้ใช้ทั่วไป)

1. ดาวน์โหลดไฟล์ `.exe` ล่าสุดจาก [Releases](https://github.com/USERNAME/REPO/releases)
2. แตกไฟล์ (ถ้ามี)
3. ดับเบิลคลิกไฟล์ `.exe` เพื่อเปิด Launcher
4. กรอกชื่อผู้เล่น → กด **บันทึกการตั้งค่า**
5. กด **▶ เข้าเกม** เมื่อเซิร์ฟเวอร์ออนไลน์

**หมายเหตุ**: Launcher จะดาวน์โหลดไฟล์อัปเดตอัตโนมัติเมื่อตรวจพบเวอร์ชันใหม่

## การตั้งค่าไฟล์ `launcher_setting.json` (สำหรับเจ้าของเซิร์ฟเวอร์ / ผู้พัฒนา)

ไฟล์ JSON นี้เป็นหัวใจหลักของ launcher ทุกอย่างถูกกำหนดจากไฟล์นี้

### ตัวอย่างไฟล์ launcher_setting.json

```json
{
    "version": "1.2",
    "discord": "https://discord.gg/yourserver",
    "background_image": "http://127.0.0.1/background.jpg",
    "ICON_SERVER": "http://127.0.0.1/icon.jpg",
    "server_game": {
        "ip": "168.222.20.137",
        "port": "7777"
    },
    "game": {
        "download_url": "http://127.0.0.1/f.zip",
        "sha256": "8af325a45d64eff3a724c83bdf456232384ed8eab184f0f036d65f3198ef72a1"
    },
    "news": [
        {
            "title": "ยินดีต้อนรับสู่ SAMP Launcher!",
            "content": "นี่คือตัวเรียกใช้งานแบบกำหนดเองสำหรับโหมดผู้เล่นหลายคนของ San Andreas โปรดติดตามการอัปเดตและคุณสมบัติใหม่ ๆ!",
            "image": "http://127.0.0.1/icon.jpg",
            "date": "January 1, 2024"
        },
        {
            "title": "อัปเดตใหม่พร้อมใช้งาน",
            "content": "เวอร์ชัน 1.0 พร้อมให้ดาวน์โหลดแล้ว ซึ่งมีการปรับปรุงประสิทธิภาพและแก้ไขข้อผิดพลาดต่าง ๆ",
            "image": "http://127.0.0.1/icon.jpg",
            "date": "February 10, 2024"
        }
    ]
}
