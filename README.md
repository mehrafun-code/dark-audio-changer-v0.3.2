# Dark Audio Changer (English → Hindi)

Video upload karo, Hindi dub milegi. Male awaaz ki jagah male Hindi voice, female ki jagah female.

## Software ki tarah chalao (sabse aasan)
**Windows:** repo ka folder kholo aur `Start_DarkAudioChanger.bat` par double click karo.
Pehli baar ye apne aap Python libraries aur FFmpeg install karega (internet chahiye, 5-10 minute). Uske baad app ki apni window khulti hai.
Python **3.11** chahiye: https://www.python.org/downloads/release/python-3119/ (install me "Add python.exe to PATH" tick karna).

**Mac / Linux:** terminal me `./run.sh`

> `app/static/index.html` ko seedha double click karke mat kholo. Server ke bina upload aur logo kaam nahi karte.

## Preview Studio
Dub hone ke baad video ke saath: original audio aur Hindi dub ki waveform, timeline (click/drag se seek), awaaz mixer (Original / Dub / Dono) aur live transcript.

## Run (Docker)
```bash
cp .env.example .env     # ANTHROPIC_API_KEY daalo (optional)
docker compose up --build
```
Browser me kholo: http://localhost:8000

## Run (manual)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Structure
```
launcher.py                  desktop window launcher
Start_DarkAudioChanger.bat   Windows one-click start
run.sh                       Mac/Linux start
app/
  main.py        API (FastAPI) + media streaming
  media.py       range requests, waveform peaks
  pipeline.py    poori dubbing pipeline
  gender.py      male/female detection
  translate.py   Claude / Google translation
  audio_utils.py ffmpeg helpers
  config.py      settings (.env)
  static/        web UI + logo.png, favicon.png
```

## Roadmap
- v0.4: Demucs (background music rakhna), pyannote speaker diarization
- v0.5: Voice cloning (XTTS-v2), more languages
