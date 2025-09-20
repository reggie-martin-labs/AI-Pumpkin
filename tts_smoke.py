"""Azure-only minimal TTS smoke test that writes WAV and uses winsound for playback.

Why this change:
- Writing WAV avoids ffmpeg dependency and lets us use the Windows winsound API for reliable playback.
- Winsound can play synchronously (blocking) or asynchronously (non-blocking).
"""

import os
import sys
import argparse
import requests
import xml.sax.saxutils as saxutils
import time
import winsound


AZURE_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_REGION = os.environ.get("AZURE_SPEECH_REGION")


def ensure_creds():
    if not AZURE_KEY or not AZURE_REGION:
        print("ERROR: Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your environment.")
        print("PowerShell example: $env:AZURE_SPEECH_KEY='...' ; $env:AZURE_SPEECH_REGION='eastus'")
        sys.exit(1)


def get_token(key: str, region: str) -> str:
    url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    r = requests.post(url, headers={"Ocp-Apim-Subscription-Key": key})
    r.raise_for_status()
    return r.text


def synthesize_wav(text: str, key: str, region: str, voice: str = "en-US-JennyNeural") -> bytes:
    token = get_token(key, region)
    tts_url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/ssml+xml; charset=utf-8",
        # Request WAV PCM to avoid needing ffmpeg for playback
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        "User-Agent": "AI-Pumpkin-TTS-Simple",
    }
    ssml = f"""<?xml version='1.0' encoding='utf-8'?>
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
  <voice name='{voice}'>{saxutils.escape(text)}</voice>
</speak>"""
    r = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"))
    r.raise_for_status()
    return r.content


def save_file_bytes(data: bytes, path: str) -> str:
    path = os.path.abspath(path)
    try:
        with open(path, "wb") as f:
            f.write(data)
        return path
    except PermissionError:
        # Fallback to timestamped file
        base, ext = os.path.splitext(path)
        ts = time.strftime("%Y%m%d_%H%M%S")
        alt = f"{base}_{ts}{ext}"
        with open(alt, "wb") as f:
            f.write(data)
        print(f"Warning: could not write {path}, saved to {alt}")
        return alt


def play_blocking(path: str) -> None:
    # winsound.PlaySound blocks when SND_FILENAME is used without SND_ASYNC
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME)
    except Exception as e:
        print("winsound playback failed:", e)
        # Fallback: start associated app and wait (PowerShell)
        try:
            import subprocess
            ps_cmd = f"Start-Process -FilePath \"{path}\" -Wait"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        except Exception as e2:
            print("PowerShell blocking playback failed:", e2)
            print("Falling back to non-blocking start.")
            os.system(f"cmd.exe /c start \"\" \"{path}\"")


def play_nonblocking(path: str) -> None:
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        os.system(f"cmd.exe /c start \"\" \"{path}\"")


def main():
    parser = argparse.ArgumentParser(description="Azure WAV TTS smoke test")
    parser.add_argument("text", nargs="*", help="Text to speak")
    parser.add_argument("--voice", default="en-US-JennyNeural", help="Azure voice name")
    parser.add_argument("--out", default="output.wav", help="Output filename (will be .wav)")
    parser.add_argument("--block", action="store_true", help="Block until playback finishes")
    args = parser.parse_args()

    ensure_creds()

    text = "Hello from Azure Speech!"
    if args.text:
        text = " ".join(args.text)

    try:
        print("Requesting token and synthesizing...")
        audio = synthesize_wav(text, AZURE_KEY, AZURE_REGION, voice=args.voice)
    except requests.HTTPError as e:
        print("HTTP error during TTS:", e)
        try:
            print(e.response.status_code, e.response.text)
        except Exception:
            pass
        return
    except Exception as e:
        print("Error during TTS:", e)
        return

    out_name = args.out
    if not out_name.lower().endswith('.wav'):
        out_name = os.path.splitext(out_name)[0] + '.wav'

    out_path = save_file_bytes(audio, out_name)
    print(f"Saved: {out_path}")
    if args.block:
        print("Playing (blocking)...")
        play_blocking(out_path)
    else:
        print("Playing (non-blocking)...")
        play_nonblocking(out_path)


if __name__ == "__main__":
    main()
