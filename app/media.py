"""Helper functions (no web framework needed): HTTP range parsing + waveform peaks."""
import re
import wave
from pathlib import Path

import numpy as np


def parse_range(header: str | None, size: int):
    """Return (start, end, is_partial) ya None agar range galat hai."""
    if not header:
        return 0, size - 1, False
    m = re.match(r"bytes=(\d*)-(\d*)$", header.strip())
    if not m:
        return 0, size - 1, False
    g1, g2 = m.groups()
    if g1 == "" and g2 == "":
        return 0, size - 1, False
    if g1 == "":
        start, end = max(size - int(g2), 0), size - 1
    else:
        start = int(g1)
        end = min(int(g2), size - 1) if g2 else size - 1
    if start > end or start >= size:
        return None
    return start, end, True


def wav_peaks(path: Path, bins: int = 1200) -> dict:
    with wave.open(str(path), "rb") as w:
        n, sr, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError("Sirf 16-bit WAV supported hai")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if len(data) == 0:
        return {"duration": 0.0, "peaks": [0.0] * bins}
    idx = np.linspace(0, len(data), bins + 1).astype(int)
    peaks = []
    for a, b in zip(idx[:-1], idx[1:]):
        peaks.append(float(np.abs(data[a:b]).max()) / 32768.0 if b > a else 0.0)
    return {"duration": n / sr, "peaks": peaks}
