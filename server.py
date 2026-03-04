import http.server
import socketserver
import os
import sys
import json
import urllib.request
import urllib.error
import ssl

# Configuration
ADMIN_USER = os.environ.get('ADMIN_USER', 'Mashhurbek')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Mashhurbek_2006@')

PORT = int(os.environ.get("PORT", 8080))
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api-proxy":
            self.handle_proxy()
        elif self.path == "/api/login":
            self.handle_login()
        else:
            super().do_POST()

    def do_GET(self):
        if self.path.startswith("/api-proxy"):
            self.handle_proxy()
        else:
            super().do_GET()

    def handle_login(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            u = data.get('username', '')
            p = data.get('password', '')
            
            if u.lower() == ADMIN_USER.lower() and p == ADMIN_PASS:
                response = {"status": "success", "message": "Authenticated"}
                self.send_response(200)
            else:
                response = {"status": "error", "message": "Invalid credentials"}
                self.send_response(401)
                
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(400, str(e))

    def handle_proxy(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        target_url = self.headers.get('X-Target-URL')
        auth_header = self.headers.get('Authorization')

        if not target_url:
            self.send_error(400, "Missing X-Target-URL header")
            return

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(target_url, data=body, method=self.command)
            if auth_header:
                req.add_header('Authorization', auth_header)
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, context=ctx) as response:
                self.send_response(response.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.read())

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Target-URL, Authorization, Content-Type')
        self.end_headers()

def run_server():
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"--- MikroTik User Manager - PRODUCTION READY ---")
            print(f"Listening on: 0.0.0.0:{PORT}")
            print(f"Login API: /api/login")
            print(f"Proxy active at: /api-proxy")
            print(f"-----------------------------------------------")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:
            print(f"Error: Port {PORT} is busy. Please choose another port.")
        else:
            print(f"Error starting server: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

if __name__ == "__main__":
    run_server()

