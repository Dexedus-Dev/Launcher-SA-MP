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

## ขั้นตอนการ Build

1. ตรวจสอบ version ของ python แนะนำ 3.11.5
2. เข้าไปแก้ไขไฟล์ build.py ตามใจคุณ และสร้างโฟลเดอร์ assets
3. เปิด cmd / terminal ขึ้นมาพิมท์ `python -m venv venv`
4. `pip install -r requirements.txt`
5. จากนั้นสามารถ `python build.py` ได้เลย

**หมายเหตุ**: Launcher จะดาวน์โหลดไฟล์อัปเดตอัตโนมัติเมื่อตรวจพบเวอร์ชันใหม่

## การตั้งค่าไฟล์ `launcher_setting.json` (สำหรับเจ้าของเซิร์ฟเวอร์ / ผู้พัฒนา)

ไฟล์ JSON นี้เป็นหัวใจหลักของ launcher ทุกอย่างถูกกำหนดจากไฟล์นี้
```json
{
    "version": "1.2",
    "discord": "https://discord.gg/yourserver",
    "background_image": "https://yourdomain.com/bg.jpg",
    "ICON_SERVER": "https://yourdomain.com/server-icon.png",
    "server_game": {
        "ip": "168.222.20.137",
        "port": "7777"
    },
    "game": {
        "download_url": "https://yourdomain.com/update/v1.2-full.zip",
        "sha256": "8af325a45d64eff3a724c83bdf456232384ed8eab184f0f036d65f3198ef72a1"
    },
    "news": [
        {
            "title": "ยินดีต้อนรับสู่เซิร์ฟเวอร์!",
            "content": "เซิร์ฟเวอร์เปิดใหม่ มีระบบใหม่เพียบ ร่วมสนุกกันได้เลย!",
            "image": "https://yourdomain.com/news/welcome.jpg",
            "date": "March 15, 2025"
        },
        {
            "title": "อัปเดตครั้งใหญ่ V1.2",
            "content": "เพิ่มระบบงานใหม่, แก้บั๊ก, ปรับสมดุลอาวุธ",
            "image": "https://yourdomain.com/news/update-v12.jpg",
            "date": "March 20, 2025"
        }
    ]
}
