NEXT STEPS — AI-Pumpkin (short-lived resume file)

Purpose
- Quick resume notes so you (or the assistant) can pick up work later without re-reading long logs.

Where to find the repo
- Remote: https://github.com/reggie-martin-labs/AI-Pumpkin.git
- Local path I use: C:\Users\reggiemartin\AI-Pumpkin

Context snapshot
- Branch: main (latest pushed commit d26f036 — "MVP: Azure WAV TTS, envelope tool, README update")
- Virtualenv: `./.venv` (Python 3.11)
- Key files: `tts_smoke.py`, `envelope.py`, `requirements.txt`, `README.md`
- Generated file: `output.wav` (local, untracked)

Commands to resume (PowerShell)
1. Open project and activate venv
```powershell
code C:\Users\reggiemartin\AI-Pumpkin
cd C:\Users\reggiemartin\AI-Pumpkin
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Verify git & latest commits
```powershell
git fetch origin
git checkout main
git pull origin main
git status --short --branch
git log --oneline -n 5
```

3. Run TTS smoke test (blocking playback)
```powershell
python tts_smoke.py "Happy Spooky Halloween" --block
```
Expected: `output.wav` written and playback heard.

Next task (pick one)
- Implement `button_trigger.py` (keyboard fallback + serial) on branch `feat/button-trigger`.

If anything is unclear
- See `README.md` for more detailed run instructions.
- The assistant can be asked to continue from commit `d26f036` or to create the feature branch and implement `button_trigger.py` now.

Notes
- I committed and pushed the MVP to `main`. This file is on branch `wip/next-steps` and is short-lived—feel free to delete it after resuming.

— end of NEXT_STEPS.md
