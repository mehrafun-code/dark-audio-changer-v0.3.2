import mimetypes
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, settings
from .media import parse_range, wav_peaks
from .pipeline import STYLES, analyze, render, speak_preview
from .translate import translate_all, translit

app = FastAPI(title="Dark Audio Changer", version=config.VERSION)
JOBS: dict[str, dict] = {}
STATIC = Path(__file__).parent / "static"
PRIVATE = {"output", "input", "workdir"}

try:
    settings.apply_temp()
except Exception:
    pass


# ---------------- helpers ----------------
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


def _wd(j: dict) -> Path:
    return Path(j["workdir"])


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    i = 2
    while True:
        cand = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not cand.exists():
            return cand
        i += 1


def _save_copy(j: dict) -> Path:
    dest = settings.output_dir()
    dest.mkdir(parents=True, exist_ok=True)
    stem = Path(j.get("name") or "video").stem
    target = _unique(dest / f"{stem}_hindi.mp4")
    shutil.copy2(j["output"], target)
    return target


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


# ---------------- background work ----------------
def _progress(job_id: str):
    def progress(msg, pct):
        JOBS[job_id].update(status="processing", message=msg, progress=pct)
    return progress


def _render_work(job_id: str):
    j = JOBS[job_id]
    try:
        settings.apply_temp()
        out, segs = render(Path(j["input"]), _wd(j), j["segments"], _progress(job_id))
        j.update(status="done", output=str(out), segments=segs, progress=100,
                 message="Dub taiyar hai.", saved_path=None)
        if settings.auto_save():
            try:
                j["saved_path"] = str(_save_copy(j))
            except Exception as e:
                j["message"] = f"Dub taiyar hai (auto-save nahi hua: {e})"
    except Exception as e:
        j.update(status="error", message=str(e))


def _analyze_work(job_id: str, video: Path, gender_mode: str, review: bool):
    j = JOBS[job_id]
    try:
        settings.apply_temp()
        j["segments"], j["notes"] = analyze(video, _wd(j), _progress(job_id), gender_mode)
    except Exception as e:
        j.update(status="error", message=str(e))
        return
    if review:
        j.update(status="review", progress=48, message="Video sun lo aur voice check karo, phir DUB BANAO dabao.")
    else:
        _render_work(job_id)


# ---------------- API ----------------
class SegEdit(BaseModel):
    id: int
    gender: str
    hindi: str
    style: str = "normal"


class RenderBody(BaseModel):
    segments: list[SegEdit]


class SettingsBody(BaseModel):
    output_dir: Optional[str] = None
    work_dir: Optional[str] = None
    auto_save: Optional[bool] = None
    api_key: Optional[str] = None


class PickBody(BaseModel):
    initial: Optional[str] = None
    title: Optional[str] = None


class SpeakBody(BaseModel):
    text: str
    gender: str = "male"
    style: str = "normal"


class TranslateBody(BaseModel):
    texts: list[str]
    seconds: Optional[list[float]] = None


class TranslitBody(BaseModel):
    text: str


@app.post("/api/speak")
def speak(b: SpeakBody):
    """Ek line ki Hindi awaaz sunne ke liye (editor)."""
    if not b.text.strip():
        raise HTTPException(400, "Pehle Hindi text likho")
    try:
        path = speak_preview(b.text.strip(), "female" if b.gender == "female" else "male",
                             b.style if b.style in STYLES else "normal")
    except Exception as e:
        raise HTTPException(502, str(e))
    return FileResponse(path, media_type="audio/mpeg")


@app.post("/api/translate")
def translate(b: TranslateBody):
    return translate_all(b.texts, b.seconds)


@app.post("/api/translit")
def translit_api(b: TranslitBody):
    try:
        return {"text": translit(b.text)}
    except Exception as e:
        raise HTTPException(502, f"Devanagari me nahi badal paye: {e}")


@app.get("/api/version")
def version():
    return {"version": config.VERSION}


@app.get("/api/settings")
def get_settings():
    return settings.snapshot()


@app.post("/api/settings")
def set_settings(b: SettingsBody):
    try:
        settings.update(b.output_dir, b.work_dir, b.auto_save, b.api_key)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return settings.snapshot()


@app.post("/api/pick-folder")
def pick_folder(b: PickBody):
    return {"path": settings.pick_folder(b.title or "Folder chuno", b.initial)}


@app.post("/api/cleanup")
def cleanup():
    busy = {k for k, j in JOBS.items() if j.get("status") in ("queued", "processing")}
    freed = settings.cleanup({JOBS[k]["workdir"] for k in busy})
    for k in list(JOBS):
        if k not in busy and not Path(JOBS[k]["workdir"]).exists():
            del JOBS[k]
    return {"freed_mb": round(freed / 1048576), **settings.snapshot()}


@app.post("/api/dub")
async def dub(bg: BackgroundTasks, file: UploadFile = File(...),
              gender_mode: str = Form("auto"), review: str = Form("1")):
    if gender_mode not in ("auto", "male", "female"):
        gender_mode = "auto"
    job_id = uuid.uuid4().hex[:12]
    folder = settings.work_dir() / job_id
    try:
        folder.mkdir(parents=True, exist_ok=True)
        settings.apply_temp()
        video = folder / ("input" + Path(file.filename or "v.mp4").suffix)
        with open(video, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as e:
        raise HTTPException(400, f"Temp folder me file nahi likh sake: {e}")
    JOBS[job_id] = {"status": "queued", "message": "Queue me hai", "progress": 0,
                    "input": str(video), "workdir": str(folder), "name": file.filename or "video.mp4"}
    bg.add_task(_analyze_work, job_id, video, gender_mode, review == "1")
    return {"job_id": job_id}


@app.post("/api/render/{job_id}")
def rerender(job_id: str, body: RenderBody, bg: BackgroundTasks):
    """Review/edit ke baad (ya dub ke baad dobara) awaaz banao."""
    j = _job(job_id)
    if j.get("status") not in ("review", "done", "error") or not j.get("segments"):
        raise HTTPException(409, "Abhi kaam chal raha hai")
    edits = {e.id: e for e in body.segments}
    for seg in j["segments"]:
        e = edits.get(seg["id"])
        if e:
            seg["gender"] = "female" if e.gender == "female" else "male"
            seg["hindi"] = e.hindi
            seg["style"] = e.style if e.style in STYLES else "normal"
            seg["tr_failed"] = False
    j.update(status="processing", progress=50, message="Awaaz ban rahi hai...")
    bg.add_task(_render_work, job_id)
    return {"ok": True}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    return {k: v for k, v in _job(job_id).items() if k not in PRIVATE}


@app.get("/api/media/{job_id}/{kind}")
def media(job_id: str, kind: str, request: Request):
    j = _job(job_id)
    wd = _wd(j)
    preview = wd / "preview.mp4"
    files = {
        "video": preview if preview.exists() else Path(j["input"]),  # original awaaz ke saath
        "dub": wd / "dub.wav",          # sirf Hindi dub awaaz
        "original": wd / "audio.wav",
    }
    if j.get("output"):
        files["final"] = Path(j["output"])
    path = files.get(kind)
    if not path or not path.exists():
        raise HTTPException(404, "File nahi mili")
    mt = "audio/wav" if path.suffix == ".wav" else (mimetypes.guess_type(path.name)[0] or "video/mp4")
    return _ranged(request, path, mt)


@app.get("/api/peaks/{job_id}/{track}")
def peaks(job_id: str, track: str):
    j = _job(job_id)
    name = {"original": "audio.wav", "dub": "dub.wav"}.get(track)
    p = _wd(j) / (name or "")
    if not name or not p.exists():
        raise HTTPException(404, "Track nahi mila")
    return wav_peaks(p)


@app.get("/api/download/{job_id}")
def download(job_id: str):
    j = _done(job_id)
    stem = Path(j.get("name") or "video").stem
    return FileResponse(j["output"], media_type="video/mp4", filename=f"{stem}_hindi.mp4")


@app.post("/api/save/{job_id}")
def save(job_id: str):
    """Dub video ko chune hue output folder me save karo aur folder kholo."""
    j = _done(job_id)
    try:
        target = _save_copy(j)
    except Exception as e:
        raise HTTPException(500, f"Save nahi hua: {e}")
    _reveal(target.parent)
    return {"path": str(target)}


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
