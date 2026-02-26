#!/bin/bash
# Start Celery worker in the background
celery -A apis worker --loglevel=info --concurrency=2 &

# Start a minimal HTTP server to satisfy Azure App Service health probes
python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, sys

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Celery worker running')
    def log_message(self, format, *args):
        pass  # Suppress access logs

HTTPServer(('0.0.0.0', 8000), HealthHandler).serve_forever()
"
