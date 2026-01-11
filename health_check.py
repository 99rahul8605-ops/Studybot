"""
Health check endpoint for Render
"""
import os
import threading
import time
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

logger = logging.getLogger(__name__)

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

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port  # Return original even if all are in use

def run_health_server():
    """Run health check server on an available port."""
    port = int(os.getenv('PORT', 8080))
    
    # Try to find available port
    available_port = find_available_port(port)
    
    if available_port != port:
        print(f"⚠️ Port {port} is in use, using port {available_port} instead")
    
    try:
        server = HTTPServer(('0.0.0.0', available_port), HealthHandler)
        print(f'✅ Health check server running on port {available_port}')
        server.serve_forever()
    except OSError as e:
        print(f"❌ Failed to start health server on port {available_port}: {e}")
        # Try one more time with random port
        try:
            server = HTTPServer(('0.0.0.0', 0), HealthHandler)
            actual_port = server.server_address[1]
            print(f'✅ Health check server running on random port {actual_port}')
            server.serve_forever()
        except Exception as e2:
            print(f"❌ Failed to start health server: {e2}")

def start_health_server():
    """Start health server in a separate thread."""
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Give it a moment to start
    time.sleep(1)
    
    return health_thread

if __name__ == '__main__':
    run_health_server()
