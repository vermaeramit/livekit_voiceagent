"""Minimal token + static server for the browser client.

Mints LiveKit access tokens (signing needs the API secret, which must stay
server-side) and serves the static web client. Stdlib only — no extra deps
beyond livekit-api, which ships with livekit-agents.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from livekit import api

API_KEY = os.environ["LIVEKIT_API_KEY"]
API_SECRET = os.environ["LIVEKIT_API_SECRET"]
# URL the *browser* uses to reach LiveKit (host-mapped), NOT the compose-internal name.
PUBLIC_URL = os.environ.get("LIVEKIT_PUBLIC_URL", "ws://localhost:7880")
PORT = int(os.environ.get("PORT", "3000"))

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/token":
            q = parse_qs(parsed.query)
            room = q.get("room", ["playground"])[0]
            identity = q.get("identity", ["user"])[0]
            token = (
                api.AccessToken(API_KEY, API_SECRET)
                .with_identity(identity)
                .with_name(identity)
                .with_grants(api.VideoGrants(room_join=True, room=room))
                # Explicitly dispatch the named agent when this client joins —
                # guarantees the agent is in the room regardless of timing.
                .with_room_config(
                    api.RoomConfiguration(
                        agents=[api.RoomAgentDispatch(agent_name="voice-agent")]
                    )
                )
                .to_jwt()
            )
            body = json.dumps({"token": token, "url": PUBLIC_URL, "room": room}).encode()
            self._send(200, body, "application/json")
            return

        # static files
        rel = "index.html" if parsed.path in ("/", "") else parsed.path.lstrip("/")
        fpath = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not fpath.startswith(WEB_DIR) or not os.path.isfile(fpath):
            self._send(404, b"not found", "text/plain")
            return
        ctype = "text/html" if fpath.endswith(".html") else "application/octet-stream"
        with open(fpath, "rb") as f:
            self._send(200, f.read(), ctype)

    def log_message(self, fmt, *args):  # quieter logs
        print("token-server:", fmt % args)


if __name__ == "__main__":
    print(f"token server on :{PORT}  (LiveKit url for browser: {PUBLIC_URL})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
