"""
Startup script for Celery worker on Azure App Service.
Runs the Celery worker in a subprocess and a minimal HTTP server
to satisfy Azure's health probes.
"""
import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Start Celery worker as a subprocess
celery_proc = subprocess.Popen(
    [sys.executable, "-m", "celery", "-A", "apis", "worker", "--loglevel=info", "--concurrency=2"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Check if celery process is still alive
        status = "running" if celery_proc.poll() is None else "stopped"
        code = 200 if status == "running" else 503
        self.send_response(code)
        self.end_headers()
        self.wfile.write(f"Celery worker {status}".encode())

    def log_message(self, format, *args):
        pass

print("Starting health probe server on port 8000...")
HTTPServer(("0.0.0.0", 8000), HealthHandler).serve_forever()
