"""AI Newsroom — Public Day India
ડબલ-ક્લિક એન્ટ્રી પોઈન્ટ: સર્વર શરૂ કરે અને બ્રાઉઝર ખોલે.
"""
import threading
import time
import webbrowser

import uvicorn

from newsroom.server import app

HOST = "127.0.0.1"
PORT = 4700


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
