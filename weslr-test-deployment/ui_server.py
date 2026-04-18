#!/usr/bin/env python3
"""Simple UI server for Weslr test deployment"""
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir('/data/data/com.termux/files/home/.openclaw/workspace/weslr-ui')

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

if __name__ == "__main__":
    port = 8087
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"UI Server running on http://0.0.0.0:{port}/")
    print(f"Serving from: /data/data/com.termux/files/home/.openclaw/workspace/weslr-ui")
    server.serve_forever()
