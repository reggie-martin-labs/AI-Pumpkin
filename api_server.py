#!/usr/bin/env python3
"""Simple API server that serves the repo and exposes /generate to produce a one-liner, WAV, envelope and frames.

No external dependencies. Designed to be run from the project root.
"""
from __future__ import annotations

import json
import threading
import subprocess
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs

ROOT = Path('.').absolute()


def timestamp(prefix='output') -> str:
    return datetime.now().strftime(f"{prefix}-%Y%m%d-%H%M%S-%f")


class APIHandler(SimpleHTTPRequestHandler):
    server_version = "AI-Pumpkin-API/0.1"

    def do_POST(self):
        if self.path != '/generate':
            self.send_error(HTTPStatus.NOT_FOUND, 'Unknown endpoint')
            return

        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length).decode('utf-8') if length else ''
        params = {}
        if body:
            try:
                params = json.loads(body)
            except Exception:
                params = parse_qs(body)

        text = params.get('text') or params.get('prompt')
        if isinstance(text, list):
            text = text[0]

        try:
            from one_liner import generate
            if text:
                text_to_use = text
            else:
                text_to_use = generate(None)

            name = timestamp('output')
            wav = ROOT / f"{name}.wav"
            env = ROOT / f"{name}.envelope.json"
            frames = ROOT / f"{name}.frames.json"

            # Run TTS (no playback)
            cmd_tts = [sys.executable, 'tts_smoke.py', text_to_use, '--out', str(wav), '--no-play']
            self.log_message('Running TTS: %s', ' '.join(cmd_tts))
            subprocess.run(cmd_tts, check=True)

            # Compute envelope
            cmd_env = [sys.executable, 'envelope.py', str(wav), '--frame-ms', '30', '--out', str(env)]
            self.log_message('Running envelope: %s', ' '.join(cmd_env))
            subprocess.run(cmd_env, check=True)

            # Build frames
            cmd_vis = [sys.executable, 'visualize.py', str(env), '--out', str(frames)]
            self.log_message('Running visualize: %s', ' '.join(cmd_vis))
            subprocess.run(cmd_vis, check=True)

            resp = {'audio': wav.name, 'frames': frames.name, 'text': text_to_use}
            data = json.dumps(resp).encode('utf-8')
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except subprocess.CalledProcessError as e:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            msg = {'error': 'generation failed', 'detail': str(e)}
            data = json.dumps(msg).encode('utf-8')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            msg = {'error': 'server error', 'detail': str(e)}
            data = json.dumps(msg).encode('utf-8')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)


def run(host='0.0.0.0', port=8000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"AI-Pumpkin API server serving {ROOT} at http://{host}:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down server...')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8000)
    args = p.parse_args()
    run(port=args.port)
