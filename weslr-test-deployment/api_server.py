#!/usr/bin/env python3
"""Simple API server for WESLR test deployment.

Public-demo mode fails closed by default. Frontend flags are not security
boundaries; this API boundary must also block upload/operator/stateful surfaces
when WESLR_PRODUCT_MODE is public_demo_readonly or unset.
"""

import base64
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer


def _find_repo_root(start: Path) -> Path:
    """Resolve the WESLR repo root from a nested runtime file path."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "main.py").is_file() and (candidate / "weslr").is_dir():
            return candidate
    raise RuntimeError(f"Could not locate WESLR repo root from: {start}")


REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
sys.path.insert(0, str(REPO_ROOT))

from weslr.public_demo_chat import public_demo_chat  # noqa: E402
from weslr.public_demo_policy import (  # noqa: E402
    is_feature_allowed,
    is_public_demo_mode,
    operator_visibility_response,
    public_demo_block_response,
)
from weslr_backend_contract import (  # noqa: E402
    chat,
    check_operator_visibility,
    get_continuity_status,
    get_conversation_list,
    get_operator_summary,
    route_file,
    upload_file,
)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

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
            if not is_feature_allowed("operator_summary"):
                self.send_json(public_demo_block_response("operator_summary"), status=403)
                return
            self.send_json(get_operator_summary())
        elif self.path == "/api/contract/operator/visibility":
            if not is_feature_allowed("operator_panel"):
                self.send_json(operator_visibility_response())
                return
            self.send_json(check_operator_visibility())
        elif self.path == "/api/contract/conversations":
            self.send_json(get_conversation_list())
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        if self.path == "/api/chat":
            data = json.loads(body) if body else {}
            message = data.get("message", "")
            if is_public_demo_mode():
                self.send_json(public_demo_chat(message))
                return
            self.send_json(chat(message))
        elif self.path == "/api/contract/file-route":
            if not is_feature_allowed("file_route"):
                self.send_json(public_demo_block_response("file_route"), status=403)
                return
            data = json.loads(body) if body else {}
            self.send_json(route_file(data.get("filepath", ""), data.get("user_query", "")))
        elif self.path == "/api/contract/upload-file":
            if not is_feature_allowed("file_upload"):
                self.send_json(public_demo_block_response("file_upload"), status=403)
                return
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
