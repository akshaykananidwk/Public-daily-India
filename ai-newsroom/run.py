"""AI Newsroom — Public Day India
ડબલ-ક્લિક એન્ટ્રી પોઈન્ટ: સર્વર શરૂ કરે અને બ્રાઉઝર ખોલે.
મોબાઈલથી પણ ખૂલે — એ જ WiFi પર ફોનમાં http://<PC-IP>:4700 ખોલો.
"""
import socket
import threading
import time
import webbrowser

import uvicorn

from newsroom.server import app

HOST = "0.0.0.0"          # મોબાઈલ/LAN એક્સેસ માટે (127.0.0.1 નહીં)
PORT = 4700


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    ip = lan_ip()
    print("=" * 52)
    print("  AI Newsroom ચાલુ થયું!")
    print(f"  આ કોમ્પ્યુટર પર:  http://127.0.0.1:{PORT}")
    print(f"  મોબાઈલ/બીજા ડિવાઈસ (એ જ WiFi):  http://{ip}:{PORT}")
    print("=" * 52)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
