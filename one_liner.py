#!/usr/bin/env python3
"""Generate a spooky one-liner using OpenAI if configured, otherwise pick from a fallback list."""
from __future__ import annotations

import argparse
import os
import random
import sys

FALLBACK = [
    "I smell candy... and something else.",
    "The shadows told me your name.",
    "Don't look behind the pumpkin.",
    "Who left the door open to the other side?",
    "This pumpkin prefers souls to seeds.",
]


def generate(prompt: str | None = None) -> str:
    """Return a short one-liner. If OpenAI credentials are present, try using the API, otherwise fallback."""
    # Minimal: prefer environment OPENAI_API_KEY if available; otherwise use fallback.
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_ALT")
    if key:
        try:
            import requests

            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt or "Write a single spooky one-liner."}],
                "max_tokens": 60,
                "temperature": 0.8,
            }
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            resp.raise_for_status()
            j = resp.json()
            # best-effort extraction depending on response shape
            text = j.get("choices", [{}])[0].get("message", {}).get("content")
            if text:
                return text.strip().replace("\n", " ").strip('"')
        except Exception:
            # fall back quietly
            pass

    return random.choice(FALLBACK)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", help="Optional prompt for the LLM")
    args = p.parse_args()
    print(generate(args.prompt))


if __name__ == "__main__":
    main()
