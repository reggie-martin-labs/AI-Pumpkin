#!/usr/bin/env python3
"""Convert envelope JSON to mouth frames and write a small frames JSON suitable for the viewer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List


def map_envelope_to_frames(envelope: List[dict], levels: int = 5) -> List[dict]:
    frames = []
    for f in envelope:
        t = f.get("time_s") if "time_s" in f else f.get("time")
        lvl = float(f.get("level", 0.0))
        discrete = int(round(min(max(lvl, 0.0), 1.0) * (levels - 1)))
        frames.append({"t": round(float(t), 3), "level": discrete})
    return frames


def main():
    p = argparse.ArgumentParser()
    p.add_argument("infile", help="Envelope JSON file")
    p.add_argument("--out", help="Output frames JSON", default=None)
    args = p.parse_args()

    inp = Path(args.infile)
    out = Path(args.out) if args.out else inp.with_name(inp.stem + ".frames.json")

    env = json.loads(inp.read_text())
    frames = map_envelope_to_frames(env)
    out.write_text(json.dumps(frames, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
