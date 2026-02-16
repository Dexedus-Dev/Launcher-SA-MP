import socket
import struct


def build_packet(ip: str, port: int, opcode: bytes) -> bytes:
    """
    สร้าง packet สำหรับ query เซิร์ฟเวอร์ SA-MP
    """
    try:
        # แปลง string IP เป็น 4 bytes (เช่น "127.0.0.1" → b'\x7f\x00\x00\x01')
        ip_bytes = bytes(map(int, ip.split(".")))
        if len(ip_bytes) != 4:
            raise ValueError("IP ไม่ถูกต้อง (ต้องเป็น IPv4)")
    except (ValueError, TypeError):
        raise ValueError("รูปแบบ IP ไม่ถูกต้อง ต้องเป็น IPv4 เช่น 127.0.0.1")

    # port ใช้ little-endian 2 bytes
    port_bytes = struct.pack("<H", port)

    # สร้าง packet ตาม protocol SA-MP
    # b"SAMP" + IP(4 bytes) + PORT(2 bytes) + OPCODE(1 byte)
    return b"SAMP" + ip_bytes + port_bytes + opcode


def query_server(ip: str, port: int, timeout: float = 1.5) -> dict:
    """
    สอบถามข้อมูลเซิร์ฟเวอร์ SA-MP (opcode 'i' = basic server info)

    Parameters:
        ip      : str       - ที่อยู่ IP ของเซิร์ฟเวอร์
        port    : int       - พอร์ต (ส่วนใหญ่คือ 7777)
        timeout : float     - เวลารอสูงสุด (วินาที)

    Returns:
        dict ที่มีข้อมูลสถานะเซิร์ฟเวอร์
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        # สร้างและส่ง packet สำหรับ opcode 'i' (server info)
        packet = build_packet(ip, port, b"i")
        sock.sendto(packet, (ip, port))

        # รับข้อมูลตอบกลับ
        data, _ = sock.recvfrom(4096)

        if len(data) < 11 + 1 + 2 + 2 + 4:
            # ข้อมูลสั้นเกินไป → ถือว่าไม่สมบูรณ์
            return {
                "online": False,
                "passworded": False,
                "players": 0,
                "max_players": 0,
                "hostname": "ตอบกลับไม่สมบูรณ์"
            }

        offset = 11  # ข้ามส่วน header "SAMPxxxxxx"

        # ────────────────────────────────────────────────
        #           โครงสร้างข้อมูล opcode 'i'
        # ────────────────────────────────────────────────
        # offset 11  → passworded     (1 byte)
        # offset 12  → players        (2 bytes, uint16 LE)
        # offset 14  → max_players    (2 bytes, uint16 LE)
        # offset 16  → hostname_len   (4 bytes, uint32 LE)
        # offset 20  → hostname       (ความยาวตาม hostname_len)

        passworded = data[offset]
        offset += 1

        players = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        max_players = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        hostname_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        # ตรวจสอบว่ามีข้อมูล hostname พอหรือไม่
        if offset + hostname_len > len(data):
            hostname = "[ชื่อเซิร์ฟเวอร์ถูกตัด]"
        else:
            # ถอดรหัส hostname (ใช้ errors="replace" จะปลอดภัยกว่า ignore)
            hostname = data[offset:offset + hostname_len].decode("utf-8", errors="replace")

        return {
            "online": True,
            "passworded": bool(passworded),
            "players": int(players),
            "max_players": int(max_players),
            "hostname": hostname.strip()
        }

    except socket.timeout:
        return {
            "online": False,
            "passworded": False,
            "players": 0,
            "max_players": 0,
            "hostname": "หมดเวลา (timeout)"
        }

    except socket.gaierror:
        return {
            "online": False,
            "passworded": False,
            "players": 0,
            "max_players": 0,
            "hostname": "IP/โดเมน ไม่ถูกต้อง"
        }

    except ValueError as e:
        return {
            "online": False,
            "passworded": False,
            "players": 0,
            "max_players": 0,
            "hostname": f"ข้อผิดพลาด: {str(e)}"
        }

    except Exception as e:
        # จับข้อผิดพลาดอื่น ๆ ที่ไม่คาดคิด
        return {
            "online": False,
            "passworded": False,
            "players": 0,
            "max_players": 0,
            "hostname": f"เกิดข้อผิดพลาด: {type(e).__name__}"
        }

    finally:
        sock.close()


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    result = query_server("127.0.0.1", 7777, timeout=2.0)
    print(result)