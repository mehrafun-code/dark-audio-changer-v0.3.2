import subprocess
from pathlib import Path


def run(cmd: list[str]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{r.stderr[-1500:]}")


def extract_audio(video: Path, out_wav: Path):
    run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(out_wav)])


def speed_up(src: Path, dst: Path, tempo: float):
    """atempo ek baar me 0.5-2.0 support karta hai."""
    filters, t = [], tempo
    while t > 2.0:
        filters.append("atempo=2.0")
        t /= 2.0
    filters.append(f"atempo={t:.3f}")
    run(["ffmpeg", "-y", "-i", str(src), "-filter:a", ",".join(filters), str(dst)])


def merge(video: Path, dub_wav: Path, out_mp4: Path):
    run(["ffmpeg", "-y", "-i", str(video), "-i", str(dub_wav),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out_mp4)])
