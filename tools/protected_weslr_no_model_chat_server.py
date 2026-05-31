from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from weslr.protected_no_model_chat_adapter import (
    build_protected_no_model_chat_response_v1,
    to_protected_no_model_chat_json_safe_v1,
    validate_protected_no_model_chat_response_v1,
)

DEFAULT_PORT = 8093
BANNER = "Owner-only WESLR no-model bounded renderer. Not public pilot."


def _render_page(response: dict[str, object] | None = None, error: str | None = None) -> str:
    response = response or {}
    response_text = str(response.get("response_text", ""))
    render_mode = str(response.get("render_mode", ""))
    selected_method_id = str(response.get("selected_method_id", ""))
    selected_shape_id = str(response.get("selected_shape_id", ""))
    selected_case_id = str(response.get("selected_case_id", ""))
    selected_route_id = str(response.get("selected_route_id", ""))
    safe_metadata = response.get("safe_metadata", {}) if isinstance(response, dict) else {}
    safe_metadata_json = json.dumps(safe_metadata, ensure_ascii=False, sort_keys=True, indent=2)
    error_html = f"<p style='color:#b00020'><strong>Error:</strong> {error}</p>" if error else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Protected WESLR No-Model Chat</title>
  <style>
    body {{ font-family: sans-serif; max-width: 920px; margin: 2rem auto; padding: 0 1rem; line-height: 1.45; }}
    textarea {{ width: 100%; min-height: 140px; }}
    input[type=text] {{ width: 100%; }}
    .banner {{ background: #111827; color: #fff; padding: 1rem; border-radius: 8px; }}
    .meta {{ background: #f3f4f6; padding: 1rem; border-radius: 8px; white-space: pre-wrap; }}
    .response {{ border: 1px solid #d1d5db; padding: 1rem; border-radius: 8px; white-space: pre-wrap; }}
    .status {{ color: #374151; }}
  </style>
</head>
<body>
  <div class="banner"><strong>{BANNER}</strong></div>
  <p class="status">model provider: none · public ready: false · chat adapter: protected no-model owner-only</p>
  {error_html}
  <form method="post" action="/api/respond">
    <label for="message">Message</label><br>
    <textarea name="message" id="message" placeholder="Enter owner test message"></textarea><br>
    <button type="submit">Render</button>
  </form>
  <h2>Response</h2>
  <div class="response">{response_text or '&nbsp;'}</div>
  <h3>Safe metadata summary</h3>
  <div class="meta">render mode: {render_mode}\nselected method: {selected_method_id}\nselected shape: {selected_shape_id}\nselected case: {selected_case_id}\nselected route: {selected_route_id}\n\n{safe_metadata_json}</div>
</body>
</html>"""


class ProtectedNoModelChatHandler(BaseHTTPRequestHandler):
    server_version = "ProtectedWeslrNoModelChat/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, html: str, status: int = 200) -> None:
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/respond":
            self._send_json({"ok": True, "banner": BANNER, "model_provider": "none", "public_ready": False, "chat_adapter": "protected_no_model_owner_only_v1"})
            return
        self._send_html(_render_page())

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        fields = parse_qs(body, keep_blank_values=True)
        message = fields.get("message", [""])[0]
        context_json = fields.get("context_json", [""])[0]
        context = {}
        if context_json.strip():
            try:
                context = json.loads(context_json)
            except json.JSONDecodeError:
                context = {"context_parse_error": True}
        try:
            response = build_protected_no_model_chat_response_v1(message, context_signals=context)
            validate_protected_no_model_chat_response_v1(response)
            if parsed.path == "/api/respond":
                self._send_json(to_protected_no_model_chat_json_safe_v1(response))
            else:
                self._send_html(_render_page(response=response))
        except Exception as exc:  # pragma: no cover - server path
            if parsed.path == "/api/respond":
                self._send_json({"ok": False, "error": str(exc), "banner": BANNER}, status=400)
            else:
                self._send_html(_render_page(error=str(exc)), status=400)


def run_server(host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    server = HTTPServer((host, port), ProtectedNoModelChatHandler)
    print(f"{BANNER} listening on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Protected owner-only WESLR no-model chat server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
