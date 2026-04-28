import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"OK")
        self.wfile.flush()
    def log_message(self, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# শুধু bot.py চালাও — otp_monitor কে bot.py এর ভেতরে thread হিসেবে চালাতে হবে
subprocess.Popen(["python", "bot.py"])

while True:
    pass
