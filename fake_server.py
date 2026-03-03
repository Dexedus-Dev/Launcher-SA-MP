# SA-MP UDP Proxy
# เป็นระบบกัน Check Ip และ Port ของ Server จริง โดยจะทำการ Forward ข้อมูลจาก Client ไปยัง Server และจาก Server กลับไปยัง Client
# ซึ่งจะทำให้ตรวจสอบด้วยโปรแกรม เช่น Wireshark ได้ยากขึ้น เพราะจะเห็นแค่การสื่อสารระหว่าง Client กับ Proxy เท่านั้น ไม่เห็นการสื่อสารกับ Server จริง
# แต่ มีข้อเสียคือ อาจจะมี Latency เพิ่มขึ้นเล็กน้อย และอาจจะมีปัญหาเรื่องการเชื่อมต่อหาก Proxy ไม่เสถียร หรือมีการปิด Proxy โดยไม่ตั้งใจ
# และ หากมีการโจมตีแบบ DDoS หรือ Flooding มาที่ Proxy ก็อาจจะทำให้ Proxy ล่มได้ ดังนั้น ควรใช้ Proxy นี้ในสภาพแวดล้อมที่มีความปลอดภัย และไม่เปิดเผยต่อสาธารณะมากนัก

import socket
import threading
import argparse
import time

class SampUDPProxy:

    def __init__(self,
                 local_host="127.0.0.1",
                 local_port=7777,
                 real_server=("168.222.20.211", 7777)):

        self.LOCAL_HOST = local_host
        self.LOCAL_PORT = local_port
        self.REAL_SERVER = real_server

        self.proxy = None
        self.server = None

        self.client_addr = None
        self.running = False

        self.t1 = None
        self.t2 = None

    # ======================
    # START
    # ======================
    def start(self):

        if self.running:
            print("Proxy already running")
            return

        print("Starting SA-MP UDP Proxy...")

        self.running = True

        # Game side
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.proxy.bind((self.LOCAL_HOST, self.LOCAL_PORT))

        # Internet side
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.connect(self.REAL_SERVER)

        # buffer
        self.proxy.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)

        self.t1 = threading.Thread(
            target=self.client_to_server,
            daemon=True
        )

        self.t2 = threading.Thread(
            target=self.server_to_client,
            daemon=True
        )

        self.t1.start()
        self.t2.start()

        print("✅ Proxy Running")

    # ======================
    # STOP
    # ======================
    def stop(self):

        if not self.running:
            print("Proxy not running")
            return

        print("Stopping Proxy...")

        self.running = False

        try:
            self.proxy.close()
        except:
            pass

        try:
            self.server.close()
        except:
            pass

        self.client_addr = None

        print("✅ Proxy Stopped")

    # ======================
    # CLIENT → SERVER
    # ======================
    def client_to_server(self):

        while self.running:
            try:
                data, addr = self.proxy.recvfrom(65535)

                self.client_addr = addr
                print("CLIENT → SERVER:", data)

                self.server.send(data)

            except:
                break

    # ======================
    # SERVER → CLIENT
    # ======================
    def server_to_client(self):

        while self.running:
            try:
                data = self.server.recv(65535)

                print("SERVER → CLIENT:", data)

                if self.client_addr:
                    self.proxy.sendto(data, self.client_addr)

            except:
                break

def run_proxy():
    parser = argparse.ArgumentParser(
        description="SA-MP UDP Proxy"
    )

    parser.add_argument(
        "--local-ip",
        default="127.0.0.1"
    )

    parser.add_argument(
        "--local-port",
        type=int,
        default=7777
    )

    parser.add_argument(
        "--server-ip",
        required=True
    )

    parser.add_argument(
        "--server-port",
        type=int,
        default=7777
    )

    args = parser.parse_args()

    proxy = SampUDPProxy(
        local_host=args.local_ip,
        local_port=args.local_port,
        real_server=(args.server_ip, args.server_port)
    )

    proxy.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        proxy.stop()

# ======================
# USAGE
# ======================

if __name__ == "__main__":
    run_proxy()
