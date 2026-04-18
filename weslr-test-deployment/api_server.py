#!/usr/bin/env python3
"""Simple API server for Weslr test deployment"""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/.openclaw/workspace')

from http.server import HTTPServer, BaseHTTPRequestHandler
from weslr_backend_contract import get_continuity_status, get_operator_summary, get_conversation_list, check_operator_visibility, route_file, upload_file
import json
import base64

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        if self.path == "/api/contract/continuity":
            self.send_json(get_continuity_status())
        elif self.path == "/api/contract/operator/summary":
            self.send_json(get_operator_summary())
        elif self.path == "/api/contract/operator/visibility":
            self.send_json(check_operator_visibility())
        elif self.path == "/api/contract/conversations":
            self.send_json(get_conversation_list())
        else:
            self.send_error(404)
    
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        if self.path == "/api/contract/file-route":
            data = json.loads(body) if body else {}
            self.send_json(route_file(data.get("filepath", ""), data.get("user_query", "")))
        elif self.path == "/api/contract/upload-file":
            data = json.loads(body) if body else {}
            self.send_json(upload_file(base64.b64decode(data.get("base64Content", "")), data.get("filename", "")))
        else:
            self.send_error(404)
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    port = 8091
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"API Server running on http://0.0.0.0:{port}/")
    server.serve_forever()
