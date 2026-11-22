"""User settings: save folder, temp/work folder, auto-save. Config ~/.dark_audio_changer/settings.json me."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import config

CFG_DIR = Path.home() / ".dark_audio_changer"
CFG_FILE = CFG_DIR / "settings.json"
JOB_DIR_RE = re.compile(r"^[0-9a-f]{12}$")


def _load() -> dict:
    try:
        return json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict):
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def default_output() -> Path:
    return Path.home() / "Downloads" / "DarkAudioChanger"


def default_work() -> Path:
    return config.DATA_DIR


def output_dir() -> Path:
    return Path(_load().get("output_dir") or default_output())


def work_dir() -> Path:
    return Path(_load().get("work_dir") or default_work())


def models_dir() -> Path:
    return work_dir() / "models"


def auto_save() -> bool:
    return bool(_load().get("auto_save", False))


def apply_temp():
    """Python/pydub/ffmpeg ki temporary files bhi work folder me jayein (C: drive me nahi)."""
    t = work_dir() / "tmp"
    t.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(t)
    for k in ("TMP", "TEMP", "TMPDIR"):
        os.environ[k] = str(t)


def _check_writable(p: Path) -> Path:
    p = Path(os.path.expandvars(os.path.expanduser(str(p))))
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".write_test"
        probe.write_text("ok")
        probe.unlink()
    except Exception as e:
        raise ValueError(f"Is folder me likh nahi sakte: {p} ({e})")
    return p


def update(out=None, work=None, auto=None):
    d = _load()
    if out is not None:
        if out.strip():
            d["output_dir"] = str(_check_writable(Path(out.strip())))
        else:
            d.pop("output_dir", None)
    if work is not None:
        if work.strip():
            d["work_dir"] = str(_check_writable(Path(work.strip())))
        else:
            d.pop("work_dir", None)
    if auto is not None:
        d["auto_save"] = bool(auto)
    _save(d)
    apply_temp()


def dir_size(p: Path) -> int:
    total = 0
    try:
        for root, _dirs, files in os.walk(p):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except Exception:
        pass
    return total


def _jobs_size() -> int:
    w = work_dir()
    total = dir_size(w / "tmp")
    if w.exists():
        for c in w.iterdir():
            if c.is_dir() and JOB_DIR_RE.match(c.name):
                total += dir_size(c)
    return total


def snapshot() -> dict:
    return {
        "output_dir": str(output_dir()),
        "work_dir": str(work_dir()),
        "auto_save": auto_save(),
        "default_output": str(default_output()),
        "default_work": str(default_work()),
        "work_size_mb": round(_jobs_size() / 1048576),
        "models_mb": round(dir_size(models_dir()) / 1048576),
    }


def cleanup(skip_dirs: set[str]) -> int:
    """Purane job folders aur tmp saaf karo (models nahi). Freed bytes return."""
    freed = 0
    w = work_dir()
    if not w.exists():
        return 0
    for c in w.iterdir():
        if c.is_dir() and JOB_DIR_RE.match(c.name) and str(c) not in skip_dirs:
            freed += dir_size(c)
            shutil.rmtree(c, ignore_errors=True)
    t = w / "tmp"
    if t.exists():
        for c in t.iterdir():
            try:
                freed += dir_size(c) if c.is_dir() else c.stat().st_size
                shutil.rmtree(c, ignore_errors=True) if c.is_dir() else c.unlink()
            except Exception:
                pass
    return freed


def pick_folder(title: str = "Folder chuno", initial: str | None = None):
    """Native folder-chooser dialog kholo. Cancel par None."""
    try:
        if sys.platform == "win32":
            esc = lambda t: t.replace("'", "''")
            ps = (
                "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$o=New-Object System.Windows.Forms.Form;$o.TopMost=$true;"
                "$f=New-Object System.Windows.Forms.FolderBrowserDialog;"
                f"$f.Description='{esc(title)}';$f.ShowNewFolderButton=$true;"
                + (f"$f.SelectedPath='{esc(initial)}';" if initial else "")
                + "if($f.ShowDialog($o) -eq 'OK'){[Console]::Out.Write($f.SelectedPath)}"
            )
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps],
                               capture_output=True, text=True, encoding="utf-8", timeout=600)
            return r.stdout.strip() or None
        if sys.platform == "darwin":
            r = subprocess.run(["osascript", "-e", f'POSIX path of (choose folder with prompt "{title}")'],
                               capture_output=True, text=True, timeout=600)
            return r.stdout.strip().rstrip("/") or None
        r = subprocess.run(["zenity", "--file-selection", "--directory", f"--title={title}"],
                           capture_output=True, text=True, timeout=600)
        return r.stdout.strip() or None
    except Exception:
        return None
