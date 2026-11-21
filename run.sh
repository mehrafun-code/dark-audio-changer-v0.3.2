#!/usr/bin/env bash
# Mac / Linux launcher
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
if [ ! -f venv/.ready ]; then
  pip install -r requirements-desktop.txt && touch venv/.ready || exit 1
fi
command -v ffmpeg >/dev/null || { echo "Pehle ffmpeg install karo (brew install ffmpeg / sudo apt install ffmpeg)"; exit 1; }
python launcher.py
