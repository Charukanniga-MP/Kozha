#!/usr/bin/env python3
"""Dependency-free local server for eyeballing SiGML in the CWASA avatar.

Serves ``public/`` at ``/`` and ``data/`` at ``/data/`` (mirrors the routing the
FastAPI app uses) WITHOUT importing the heavy translate stack (spaCy/argos). Use
it to review hand-authored ASL signs:

    python3 scripts/serve_local.py            # -> http://localhost:8000/asl_review.html
    python3 scripts/serve_local.py --port 9000

Ctrl-C to stop.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO / "public"
DATA = REPO / "data"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("/data/"):
            return str(DATA / clean[len("/data/"):])
        if clean in ("", "/"):
            return str(PUBLIC / "asl_review.html")
        return str(PUBLIC / clean.lstrip("/"))

    def do_POST(self) -> None:
        clean = self.path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/api/ai/predict-chat":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
            import json
            try:
                data = json.loads(post_data)
            except Exception:
                data = {}
            
            current_input = (data.get('current_input') or '').strip()
            latest_speech = (data.get('latest_speech') or '').strip()
            speaker_name = (data.get('speaker_name') or 'Remote Party').strip()
            
            predictions = []
            if current_input:
                inp_lower = current_input.lower()
                if inp_lower.startswith('yes'):
                    predictions = [
                        f"{current_input}, I will be there.",
                        f"{current_input}, I can join after class.",
                        f"{current_input}, I agree completely."
                    ]
                elif inp_lower.startswith('no') or inp_lower.startswith('sorry'):
                    predictions = [
                        f"{current_input}, I won't be able to make it.",
                        f"{current_input}, I have another meeting.",
                        f"{current_input}, let me check my schedule first."
                    ]
                elif inp_lower.startswith('can you') or inp_lower.startswith('could you'):
                    predictions = [
                        f"{current_input} send me the details?",
                        f"{current_input} repeat that in sign language?",
                        f"{current_input} call me back later?"
                    ]
                elif inp_lower.startswith('what') or inp_lower.startswith('where') or inp_lower.startswith('when'):
                    predictions = [
                        f"{current_input} time does it start?",
                        f"{current_input} should we meet?",
                        f"{current_input} is the location?"
                    ]
                else:
                    predictions = [
                        f"{current_input} will be great!",
                        f"{current_input} sounds good to me.",
                        f"{current_input} let's coordinate soon."
                    ]
            elif latest_speech:
                speech_lower = latest_speech.lower()
                if any(w in speech_lower for w in ['coming', 'come', 'join', 'tomorrow', 'today', 'meet', 'time']):
                    predictions = [
                        "Yes, I will be there on time!",
                        "Yes, I can join after class.",
                        "Sorry, I won't be able to make it."
                    ]
                elif any(w in speech_lower for w in ['how are', 'how do', 'doing', 'hello', 'hi', 'hey']):
                    predictions = [
                        "I am doing great, thank you! How about you?",
                        "Everything is going well!",
                        "Glad to connect with you on Signify!"
                    ]
                else:
                    predictions = [
                        f"That sounds great, {speaker_name}!",
                        "Thanks for sharing that.",
                        "Could you explain that in sign language?"
                    ]
            else:
                predictions = [
                    "Hello! Great to connect with you.",
                    "I can hear you clearly.",
                    "How can I help you today?"
                ]
            
            response_bytes = json.dumps({'status': 'success', 'predictions': predictions[:3]}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
            return

        self.send_error(501, f"Unsupported method ({self.command!r})")

    def end_headers(self) -> None:
        # No caching — we re-emit the curated SiGML between review rounds.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args) -> None:  # quieter console
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler))
    url = f"http://localhost:{args.port}/asl_review.html"
    print(f"Serving public/ + /data on {url}\n(Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
