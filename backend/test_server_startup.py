import sys
import os
import time
import urllib.request
import threading
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from main import app

class ServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8001):
        super().__init__()
        self.host = host
        self.port = port
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

def main():
    print("[*] Testing live Uvicorn server startup on 127.0.0.1:8001...")
    server = ServerThread(port=8001)
    server.start()
    time.sleep(1.5)

    try:
        url = "http://127.0.0.1:8001/api/health"
        req = urllib.request.urlopen(url, timeout=5)
        status = req.getcode()
        body = req.read().decode('utf-8')
        print(f"[OK] Live Health Endpoint Response: Status {status}, Body: {body}")

        # Test index.html serving
        url_index = "http://127.0.0.1:8001/"
        req_index = urllib.request.urlopen(url_index, timeout=5)
        assert req_index.getcode() == 200
        print("[OK] Live Frontend Index Page Served Successfully")

        # Test dash.html serving
        url_dash = "http://127.0.0.1:8001/dash.html"
        req_dash = urllib.request.urlopen(url_dash, timeout=5)
        assert req_dash.getcode() == 200
        print("[OK] Live Dashboard Page Served Successfully")

        # Test Swagger docs serving
        url_docs = "http://127.0.0.1:8001/docs"
        req_docs = urllib.request.urlopen(url_docs, timeout=5)
        assert req_docs.getcode() == 200
        print("[OK] Live Swagger Documentation Served Successfully (/docs)")

    finally:
        server.stop()
        server.join(timeout=2)
        print("[OK] Server shutdown completed.")

if __name__ == "__main__":
    main()

