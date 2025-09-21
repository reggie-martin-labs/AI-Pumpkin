#!/usr/bin/env python3
"""Keyboard-only button trigger for AI-Pumpkin (HID USB buttons)

This script listens for a configured key (default: SPACE) in the console and
on each press it:
  - Calls `tts_smoke.py` to synthesize a timestamped WAV file and blocks until
    playback finishes.
  - Runs `envelope.py` on the generated WAV and prints a small JSON array of
    discrete mouth frames to stdout.

Designed for HID keyboard-style USB buttons (they emulate a keyboard and send
space or another key). No serial / pyserial required.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def timestamped_filename(prefix: str = "output", ext: str = "wav") -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return f"{prefix}-{ts}.{ext}"


def run_tts_and_wait(text: str, out_path: Path) -> None:
    """Call tts_smoke.py to create WAV and block until playback completes.

    Assumes tts_smoke.py accepts `--out` and `--block` flags.
    """
    cmd = [sys.executable, "tts_smoke.py", text, "--out", str(out_path), "--block"]
    print(f"Running TTS: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def compute_envelope_and_print(wav_path: Path, frame_ms: int = 30) -> List[dict]:
    out_json = wav_path.with_suffix('.envelope.json')
    cmd = [sys.executable, "envelope.py", str(wav_path), "--frame-ms", str(frame_ms), "--out", str(out_json)]
    print(f"Computing envelope: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    data = json.loads(out_json.read_text())
    mouth = []
    for i, frame in enumerate(data):
        t = frame.get('time_s') if 'time_s' in frame else frame.get('time')
        level = float(frame.get('level', 0.0))
        discrete = int(round(min(max(level, 0.0), 1.0) * 4))
        mouth.append({"t": round(float(t), 3), "level": discrete})
    print(json.dumps(mouth, indent=2))
    return mouth


def keyboard_loop(trigger_key: bytes, text: str):
    print(f"Keyboard mode: press '{trigger_key.decode()}' (or Ctrl-C to quit)")
    try:
        import msvcrt
        import requests

        while True:
            ch = msvcrt.getch()
            if ch == trigger_key:
                print('Trigger pressed — requesting generation...')
                # Try to call local API server /generate; if not available, start it detached
                try:
                    resp = requests.post('http://localhost:8000/generate', json={})
                except Exception:
                    # start server detached
                    print('API server not running; starting detached server...')
                    import subprocess
                    subprocess.Popen([sys.executable, 'api_server.py'], cwd=str(Path('.').absolute()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # wait briefly and retry
                    import time
                    time.sleep(0.5)
                    resp = requests.post('http://localhost:8000/generate', json={})

                if resp.ok:
                    j = resp.json()
                    print('Generated:', j.get('text'))
                    print('Audio:', j.get('audio'), 'Frames:', j.get('frames'))
                else:
                    print('Generation failed:', resp.text)
            else:
                # ignore other keys
                continue
    except KeyboardInterrupt:
        print("Exiting keyboard loop")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--key", default=" ", help="Trigger key (single character). Default is space")
    p.add_argument("--text", default="Happy Spooky Halloween", help="Text to speak on trigger")
    args = p.parse_args()

    key = args.key
    if len(key) != 1:
        print("--key must be a single character (e.g. ' ' for space)")
        sys.exit(2)

    trigger_key = key.encode('utf-8')
    keyboard_loop(trigger_key, args.text)


if __name__ == "__main__":
    main()
