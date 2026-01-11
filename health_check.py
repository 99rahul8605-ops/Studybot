"""
Health check endpoint for Render
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
import time

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "telegram-bot"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_health_server():
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f'✅ Health check server running on port {port}')
    server.serve_forever()

def start_health_server():
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    return health_thread

if __name__ == '__main__':
    run_health_server()
