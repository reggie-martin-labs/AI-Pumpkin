"""Compute a simple amplitude envelope (RMS) from an audio file.

Usage:
  python envelope.py output.mp3 --frame-ms 30 --out envelope.json

Produces a JSON array of {time_s, level} where level is RMS amplitude (0-1 approx).
"""
import sys
import json
from pathlib import Path
import argparse

import wave
import numpy as np


def rms(array):
    return np.sqrt(np.mean(np.square(array.astype(np.float64))))


def compute_envelope(path: Path, frame_ms: int = 30):
    # Read WAV file with wave to avoid ffmpeg dependency
    wf = wave.open(str(path), 'rb')
    sample_rate = wf.getframerate()
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    raw = wf.readframes(wf.getnframes())
    wf.close()

    dtype = None
    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    else:
        raise RuntimeError('Unsupported sample width: ' + str(sample_width))

    samples = np.frombuffer(raw, dtype=dtype)
    if channels > 1:
        samples = samples.reshape((-1, channels))
        samples = samples.mean(axis=1)

    frame_len = int(sample_rate * frame_ms / 1000)
    envelope = []
    for i in range(0, len(samples), frame_len):
        frame = samples[i : i + frame_len]
        if len(frame) == 0:
            continue
    # Normalize by max possible value for the sample width
    max_val = float(2 ** (8 * sample_width - 1) - 1)
    level = rms(frame) / max_val
        t = i / sample_rate
        envelope.append({"time_s": round(float(t), 3), "level": float(level)})
    return envelope


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", help="input audio file (mp3/wav)")
    p.add_argument("--frame-ms", type=int, default=30)
    p.add_argument("--out", default="envelope.json")
    args = p.parse_args()
    env = compute_envelope(Path(args.input), args.frame_ms)
    with open(args.out, "w") as f:
        json.dump(env, f, indent=2)
    print(f"Wrote {args.out} with {len(env)} frames")


if __name__ == "__main__":
    main()
