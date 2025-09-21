# feat/interactive-demo

This PR bundles the interactive demo for AI-Pumpkin.

What this adds

- `api_server.py` — local HTTP server. Provides POST `/generate` which:
  - generates a one-liner (via `one_liner.py` fallback/OpenAI if configured),
  - synthesizes WAV using `tts_smoke.py`,
  - computes amplitude envelope using `envelope.py`,
  - converts envelope into discrete frames using `visualize.py`,
  - returns JSON `{ audio: "<wav>", frames: "<frames.json>", text: "<one-liner>" }` and serves static files (including `viewer.html`).

- `viewer.html` — single-button browser UI ("Trick or Treat"). POSTs to `/generate`, plays audio and animates a pumpkin mouth using the returned frames.

- `run_demo.py` — convenience orchestrator. Useful flags:
  - `--open` — start the server and open `viewer.html` in a browser.
  - `--detach` — start `api_server.py` detached so the terminal is free.
  - `--no-play` — skip local winsound playback (browser will play the returned audio).

- `button_trigger.py` — keyboard HID trigger (Space by default) that POSTs to `/generate` so a physical keyboard-style button can trigger the flow.

Why

This makes the demo easy to run at events: a volunteer presses a single button and the projected pumpkin lip-syncs to a freshly generated spooky one-liner. It avoids needing Arduino/serial wiring by using keyboard HID buttons and a browser-based viewer.

Notes / Known limitations

- `api_server.py` is single-threaded and synchronous; long TTS runs will block the HTTP handler. Recommend adding a job-queue or async worker in a follow-up.
- Generated audio and frames are saved to the repo working directory; consider moving to a `generated/` folder and adding rotation/cleanup.
- Add a `/health` endpoint and PID-file check to avoid port 8000 collisions with other Python servers.

How to try it (PowerShell)

```powershell
. .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_demo.py --open --detach
# open the viewer (browser should open automatically) and click "Trick or Treat"
```

If you prefer to run server in foreground:

```powershell
python api_server.py --port 8000
```

Feedback requested

- Is the single-button viewer UX clear and accessible enough for event volunteers?
- Should the generated files be moved into `generated/` before merging?
- Any additional tests or CI steps you want added in this PR?