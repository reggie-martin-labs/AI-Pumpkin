#!/usr/bin/env python3
"""Simple orchestrator: generate one-liner, synthesize TTS (tts_smoke.py), compute envelope, create frames JSON, and open the viewer."""
from __future__ import annotations

import argparse
import json
import subprocess
import webbrowser
from pathlib import Path
import sys
import threading
import http.server
import socketserver

from one_liner import generate


def timestamped_wav(prefix='output') -> Path:
    from datetime import datetime
    ts = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    return Path(f"{prefix}-{ts}.wav")


def run(cmd):
    print('RUN:', ' '.join(str(x) for x in cmd))
    subprocess.check_call(cmd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--text', help='Optional text to speak (skips LLM)', default=None)
    p.add_argument('--open', action='store_true', help='Open the viewer after processing')
    p.add_argument('--no-play', action='store_true', help='Do not play audio locally (viewer will play it)')
    p.add_argument('--port', type=int, default=8000, help='Port to serve viewer from')
    p.add_argument('--detach', action='store_true', help='Start server detached and exit immediately')
    args = p.parse_args()

    text = args.text or generate(None)
    print('One-liner:', text)

    wav = timestamped_wav()
    tts_cmd = [sys.executable, 'tts_smoke.py', text, '--out', str(wav)]
    if args.open or args.no_play:
        tts_cmd.append('--no-play')
    else:
        tts_cmd.append('--block')
    run(tts_cmd)

    env_json = wav.with_suffix('.envelope.json')
    run([sys.executable, 'envelope.py', str(wav), '--frame-ms', '30', '--out', str(env_json)])

    frames_json = wav.with_suffix('.frames.json')
    run([sys.executable, 'visualize.py', str(env_json), '--out', str(frames_json)])

    print('Frames written to', frames_json)
    if args.open:
        # Start a simple HTTP server to serve the viewer and frames so viewer can fetch frames
        port = args.port
        viewer_url = f'http://localhost:{port}/viewer.html?frames={frames_json.name}&audio={wav.name}'

        if args.detach:
            # Start detached API server (api_server.py) so /generate is available
            import subprocess as _subp
            cmd = [sys.executable, 'api_server.py', '--port', str(port)]
            print('Starting detached API server:', ' '.join(cmd))
            _subp.Popen(cmd, cwd=str(Path('.').absolute()), stdout=_subp.DEVNULL, stderr=_subp.DEVNULL)
            print(f"Detached API server started at http://localhost:{port}/")
            webbrowser.open_new_tab(viewer_url)
            return

        handler = http.server.SimpleHTTPRequestHandler
        # Create the server instance so we can shut it down cleanly later
        httpd = socketserver.TCPServer(("", port), handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=False)
        t.start()
        print(f"Serving at http://localhost:{port}/")
        webbrowser.open_new_tab(viewer_url)

        try:
            print("Viewer open in browser. Press Enter to stop the local server and exit.")
            input()
        except KeyboardInterrupt:
            print("Interrupted, shutting down server...")
        finally:
            httpd.shutdown()
            t.join()


if __name__ == '__main__':
    main()
