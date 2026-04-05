#!/usr/bin/env python3
"""
Weslr Test Deployment - Dual Server Setup
Runs two independent HTTP servers:
- Port 8087: UI server (serves static files from weslr-ui/)
- Port 8091: API server (provides Weslr backend endpoints)
"""

import sys
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Add workspace to path
WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

from weslr_backend_contract import (
    get_continuity_status,
    get_operator_summary,
    get_conversation_list,
    check_operator_visibility,
    route_file,
    upload_file,
    chat,
)


# ==============================================================================
# API SERVER (Port 8091)
# ==============================================================================

class APIServerHandler(SimpleHTTPRequestHandler):
    """API server handler - serves Weslr backend endpoints."""
    
    def log_message(self, format, *args):
        pass  # Suppress logging
    
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
            self.send_error(404, "Unknown endpoint")
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        
        if self.path == "/api/contract/file-route":
            try:
                import json
                data = json.loads(body) if body else {}
                result = route_file(data.get("filepath", ""), data.get("user_query", ""))
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        elif self.path == "/api/contract/upload-file":
            try:
                import json, base64
                data = json.loads(body) if body else {}
                file_content = base64.b64decode(data.get("base64Content", ""))
                result = upload_file(file_content, data.get("filename", ""))
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        elif self.path == "/api/chat":
            try:
                import json
                data = json.loads(body) if body else {}
                message = data.get("message", "")
                result = chat(message)
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Unknown endpoint")
    
    def send_json(self, data, status=200):
        import json
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def run_api_server(host: str, port: int):
    """Run the API server."""
    handler = lambda *a, **kw: APIServerHandler(*a, directory=str(WORKSPACE), **kw)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"[API] Running on http://{host}:{port}/")
    print(f"[API] Endpoints:")
    print(f"[API]   GET  /api/contract/continuity")
    print(f"[API]   GET  /api/contract/operator/summary")
    print(f"[API]   GET  /api/contract/operator/visibility")
    print(f"[API]   GET  /api/contract/conversations")
    print(f"[API]   POST /api/contract/file-route")
    print(f"[API]   POST /api/contract/upload-file")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Stopped.")


# ==============================================================================
# UI SERVER (Port 8087)
# ==============================================================================

class UIServerHandler(SimpleHTTPRequestHandler):
    """UI server handler - serves static files from weslr-ui/."""
    
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_GET(self):
        import os
        # Add CORS headers to all responses
        super().do_GET()
        # Re-send headers with CORS
        self.send_response_original = self.send_response
        def send_response_with_cors(code, message=None):
            self.send_response_original(code, message)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_response = send_response_with_cors


def run_ui_server(host: str, port: int):
    """Run the UI server."""
    ui_dir = WORKSPACE / "weslr-ui"
    if not ui_dir.exists():
        print(f"[UI] ERROR: weslr-ui directory not found at {ui_dir}")
        sys.exit(1)
    
    handler = lambda *a, **kw: UIServerHandler(*a, directory=str(ui_dir), **kw)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"[UI] Running on http://{host}:{port}/")
    print(f"[UI] Serves: {ui_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[UI] Stopped.")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Weslr Test Deployment")
    parser.add_argument("--ui-port", type=int, default=8087, help="UI server port")
    parser.add_argument("--api-port", type=int, default=8091, help="API server port")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--only", choices=["ui", "api"], help="Run only one server")
    
    args = parser.parse_args()
    
    print("="*60)
    print("WESLR PRIVATE TEST DEPLOYMENT")
    print("="*60)
    print(f"Host: {args.host}")
    print(f"UI Port: {args.ui_port}")
    print(f"API Port: {args.api_port}")
    print()
    
    if args.only == "ui":
        run_ui_server(args.host, args.ui_port)
    elif args.only == "api":
        run_api_server(args.host, args.api_port)
    else:
        # Run both servers
        import multiprocessing
        import time
        
        # Start API server in subprocess
        api_proc = multiprocessing.Process(
            target=run_api_server,
            args=(args.host, args.api_port),
            daemon=True
        )
        api_proc.start()
        
        # Small delay to let API server start
        time.sleep(0.5)
        
        # Run UI server in main process
        run_ui_server(args.host, args.ui_port)


if __name__ == "__main__":
    main()
