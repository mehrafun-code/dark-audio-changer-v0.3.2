import mimetypes
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .media import parse_range, wav_peaks
from .pipeline import process

app = FastAPI(title="Dark Audio Changer", version=config.VERSION)
JOBS: dict[str, dict] = {}
STATIC = Path(__file__).parent / "static"
PRIVATE = {"output", "input"}


def _work(job_id: str, video: Path):
    def progress(msg, pct):
        JOBS[job_id].update(status="processing", message=msg, progress=pct)
    try:
        out, segs = process(video, config.DATA_DIR / job_id, progress)
        JOBS[job_id].update(status="done", output=str(out), segments=segs, progress=100, message="Dub taiyar hai.")
    except Exception as e:
        JOBS[job_id].update(status="error", message=str(e))


def _job(job_id: str) -> dict:
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "Job nahi mila")
    return j


def _done(job_id: str) -> dict:
    j = _job(job_id)
    if j.get("status") != "done":
        raise HTTPException(404, "Abhi ready nahi")
    return j


def _ranged(request: Request, path: Path, media_type: str):
    size = path.stat().st_size
    r = parse_range(request.headers.get("range"), size)
    if r is None:
        raise HTTPException(416, "Range galat hai")
    start, end, partial = r
    length = end - start + 1

    def chunks():
        with open(path, "rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                data = f.read(min(256 * 1024, left))
                if not data:
                    break
                left -= len(data)
                yield data

    headers = {"Accept-Ranges": "bytes", "Content-Length": str(length)}
    if partial:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return StreamingResponse(chunks(), status_code=206 if partial else 200,
                             media_type=media_type, headers=headers)


def _reveal(folder: Path):
    try:
        if sys.platform == "win32":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception:
        pass


@app.get("/api/version")
def version():
    return {"version": config.VERSION}


@app.post("/api/dub")
async def dub(bg: BackgroundTasks, file: UploadFile = File(...)):
    job_id = uuid.uuid4().hex[:12]
    folder = config.DATA_DIR / job_id
    folder.mkdir(parents=True, exist_ok=True)
    video = folder / ("input" + Path(file.filename or "v.mp4").suffix)
    with open(video, "wb") as f:
        shutil.copyfileobj(file.file, f)
    JOBS[job_id] = {"status": "queued", "message": "Queue me hai", "progress": 0, "input": str(video)}
    bg.add_task(_work, job_id, video)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    return {k: v for k, v in _job(job_id).items() if k not in PRIVATE}


@app.get("/api/media/{job_id}/{kind}")
def media(job_id: str, kind: str, request: Request):
    j = _done(job_id)
    folder = config.DATA_DIR / job_id
    files = {
        "video": Path(j["input"]),     # original video (original awaaz ke saath)
        "dub": folder / "dub.wav",     # sirf Hindi dub awaaz
        "original": folder / "audio.wav",
        "final": Path(j["output"]),    # dub wali final video
    }
    path = files.get(kind)
    if not path or not path.exists():
        raise HTTPException(404, "File nahi mili")
    mt = "audio/wav" if path.suffix == ".wav" else (mimetypes.guess_type(path.name)[0] or "video/mp4")
    return _ranged(request, path, mt)


@app.get("/api/peaks/{job_id}/{track}")
def peaks(job_id: str, track: str):
    _done(job_id)
    name = {"original": "audio.wav", "dub": "dub.wav"}.get(track)
    p = config.DATA_DIR / job_id / (name or "")
    if not name or not p.exists():
        raise HTTPException(404, "Track nahi mila")
    return wav_peaks(p)


@app.get("/api/download/{job_id}")
def download(job_id: str):
    j = _done(job_id)
    return FileResponse(j["output"], media_type="video/mp4", filename="dark_audio_changer_hindi.mp4")


@app.post("/api/save/{job_id}")
def save(job_id: str):
    """Software mode: dub video ko Downloads/DarkAudioChanger me save karo aur folder kholo."""
    j = _done(job_id)
    dest = Path.home() / "Downloads" / "DarkAudioChanger"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / f"dark_audio_changer_{job_id}.mp4"
    shutil.copy2(j["output"], target)
    _reveal(dest)
    return {"path": str(target)}


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
