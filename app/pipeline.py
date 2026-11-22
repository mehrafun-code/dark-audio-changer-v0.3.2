import asyncio
import hashlib
import statistics
import threading
import time
from pathlib import Path

import edge_tts
from faster_whisper import WhisperModel
from pydub import AudioSegment

from . import config, settings
from .audio_utils import extract_audio, make_preview, speed_up, merge, to_wav, volume_db
from .gender import detect_gender
from .translate import translate_all

_model = None

# style -> (rate %, pitch Hz, gain dB). Awaaz ko "padhi hui line" se zyada natural banane ke liye
STYLES = {
    "normal": (0, 0, 0.0),
    "josh": (12, 4, 3.0),        # excited / tez
    "khush": (6, 6, 1.0),        # khushi
    "dheere": (-10, -2, -3.0),   # calm / soft
    "udaas": (-15, -6, -4.0),    # udaas
    "gussa": (8, -2, 5.0),       # gussa
    "chillana": (10, 2, 7.0),    # loud / chillana
    "fusfusa": (-8, -3, -9.0),   # dheemi awaaz, fusfusahat
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(config.WHISPER_MODEL, device=config.WHISPER_DEVICE, compute_type="int8",
                              download_root=str(settings.models_dir()))
    return _model


def transcribe(wav):
    """English speech -> segments. GPU/CUDA error aaye to CPU par fallback."""
    global _model
    try:
        segs, _ = get_model().transcribe(str(wav), language="en", vad_filter=True)
        return list(segs)
    except Exception as e:
        if config.WHISPER_DEVICE != "cpu" and any(k in str(e).lower() for k in ("cublas", "cuda", "cudnn")):
            _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8",
                                  download_root=str(settings.models_dir()))
            segs, _ = _model.transcribe(str(wav), language="en", vad_filter=True)
            return list(segs)
        raise


def tts(text: str, voice: str, out: Path, rate: str = "+0%", pitch: str = "+0Hz", retries: int = 3):
    last = None
    for i in range(retries):
        try:
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(out)))
            if out.exists() and out.stat().st_size > 0:
                return
        except Exception as e:
            last = e
        out.unlink(missing_ok=True)
        time.sleep(1.5 * (i + 1))
    hint = ""
    if last is not None and "403" in str(last):
        hint = " (403: Windows ka date/time sahi karo aur app ka naya version use karo)"
    raise RuntimeError(f"Hindi awaaz service se connect nahi hui{hint}: {last}")


def voice_for(gender: str) -> str:
    return config.VOICE_FEMALE if gender == "female" else config.VOICE_MALE


def _fmt(n: int, unit: str) -> str:
    return f"{n:+d}{unit}"


def synth(text: str, gender: str, style: str, extra_rate: int, out: Path, rate_off: int = 0, pitch_off: int = 0):
    rate, pitch, _ = STYLES.get(style, STYLES["normal"])
    rate = _clamp(rate + rate_off + extra_rate, -70, 100)
    pitch = _clamp(pitch + pitch_off, -60, 60)
    tts(text, voice_for(gender), out, rate=_fmt(rate, "%"), pitch=_fmt(pitch, "Hz"))


def speak_preview(text: str, gender: str, style: str, rate_off: int = 0, pitch_off: int = 0, gain_off: float = 0.0) -> Path:
    """Ek line ki Hindi awaaz (editor me sunne ke liye)."""
    st = style if style in STYLES else "normal"
    d = settings.work_dir() / "tmp"
    d.mkdir(parents=True, exist_ok=True)
    gain = round(STYLES[st][2] + gain_off, 1)
    key = hashlib.md5(f"{gender}|{st}|{rate_off}|{pitch_off}|{gain}|{text}".encode("utf-8")).hexdigest()[:12]
    out = d / f"speak_{key}.mp3"
    if not out.exists() or out.stat().st_size == 0:
        raw = d / f"speak_{key}_raw.mp3"
        synth(text, gender, st, 0, raw, rate_off, pitch_off)
        if gain:
            volume_db(raw, out, gain)
            raw.unlink(missing_ok=True)
        else:
            raw.replace(out)
    return out


def _safe_preview(video: Path, out: Path):
    try:
        make_preview(video, out)
    except Exception:
        out.unlink(missing_ok=True)  # preview nahi bani: original video se chalega


def analyze(video: Path, workdir: Path, progress, gender_mode: str = "auto"):
    """Stage 1: audio -> English text -> gender/style -> Hindi text. Awaaz abhi nahi banti.
    Return (segments, notes)."""
    workdir.mkdir(parents=True, exist_ok=True)
    wav = workdir / "audio.wav"

    progress("Audio nikal rahe hain...", 5)
    extract_audio(video, wav)
    preview = workdir / "preview.mp4"
    prev_thread = threading.Thread(target=_safe_preview, args=(video, preview), daemon=True)
    prev_thread.start()  # whisper ke saath-saath preview video bhi ban jaye

    progress("Speech-to-text (English)...", 15)
    raw = transcribe(wav)
    segments = [{"id": i, "start": s.start, "end": s.end, "text": s.text.strip()}
                for i, s in enumerate(x for x in raw if x.text.strip())]
    if not segments:
        raise RuntimeError("Video me koi speech nahi mili.")

    progress("Male/Female aur awaaz ka andaaz pehchan rahe hain...", 35)
    audio = AudioSegment.from_wav(str(wav))
    dbs = []
    for s in segments:
        if gender_mode in ("male", "female"):
            s["auto_gender"] = s["gender"] = gender_mode
        else:
            s["auto_gender"] = s["gender"] = detect_gender(wav, s["start"], s["end"])
        part = audio[int(s["start"] * 1000):int(s["end"] * 1000)]
        db = part.dBFS if len(part) > 0 else float("-inf")
        s["loud_db"] = db if db != float("-inf") else -60.0
        dbs.append(s["loud_db"])
    med = statistics.median(dbs)
    for s in segments:  # zyada loud = josh, bahut dheema = dheere
        style = "normal"
        if len(segments) >= 3:
            if s["loud_db"] >= med + 3:
                style = "josh"
            elif s["loud_db"] <= med - 4:
                style = "dheere"
        s["auto_style"] = s["style"] = style

    progress("Hindi translation...", 45)
    res = translate_all([s["text"] for s in segments], [s["end"] - s["start"] for s in segments])
    failed = set(res["failed"])
    for i, (s, h) in enumerate(zip(segments, res["hindi"])):
        s["hindi"] = h
        s["tr_failed"] = i in failed
    notes = [res["note"]] if res["note"] else []

    progress("Preview video taiyar ho rahi hai...", 47)
    prev_thread.join()
    return segments, notes


def _clip_path(text: str, gender: str, style: str, extra: int, workdir: Path,
               rate_off: int = 0, pitch_off: int = 0) -> Path:
    key = hashlib.md5(f"{voice_for(gender)}|{style}|{extra}|{rate_off}|{pitch_off}|{text}".encode("utf-8")).hexdigest()[:12]
    raw = workdir / f"tts_{key}.mp3"
    wavp = workdir / f"tts_{key}.wav"
    if not wavp.exists() or wavp.stat().st_size == 0:  # pehle bani hui awaaz dobara use hogi
        if not raw.exists() or raw.stat().st_size == 0:
            synth(text, gender, style, extra, raw, rate_off, pitch_off)
        to_wav(raw, wavp)
    return wavp


def _level(clip: AudioSegment, style_gain: float) -> AudioSegment:
    """Har line ki awaaz barabar loudness par, style ke hisaab se thodi upar/neeche."""
    if clip.dBFS != float("-inf"):
        clip = clip.apply_gain(max(min(-18.0 - clip.dBFS, 12.0), -12.0) + style_gain)
    return clip.fade_in(8).fade_out(25)


def render(video: Path, workdir: Path, segments: list, progress):
    """Stage 2: Hindi text + gender + style se awaaz banao, mix karo, video me jodo."""
    wav = workdir / "audio.wav"
    total_ms = int(AudioSegment.from_wav(str(wav)).duration_seconds * 1000) + 1000
    mix = AudioSegment.silent(duration=total_ms, frame_rate=24000).set_channels(1)

    n = len(segments)
    for i, s in enumerate(segments):
        progress(f"Hindi awaaz ban rahi hai ({i+1}/{n})...", 50 + int(40 * i / max(n, 1)))
        text = (s.get("hindi") or "").strip()
        if not text:
            continue
        gender = s.get("gender", "male")
        style = s.get("style", "normal")
        if style not in STYLES:
            style = "normal"

        r_off, p_off = int(s.get("rate", 0) or 0), int(s.get("pitch", 0) or 0)
        g_off, shift = float(s.get("gain", 0) or 0), float(s.get("shift", 0) or 0)
        wavp = _clip_path(text, gender, style, 0, workdir, r_off, p_off)
        clip = AudioSegment.from_wav(str(wavp))

        nxt = segments[i + 1]["start"] if i + 1 < n else s["end"] + 3
        slot = max(nxt - s["start"] - 0.1, 0.5) * 1000
        if len(clip) > slot:
            # pehle awaaz ki speed khud badhao (natural), phir bhi lambi ho to atempo
            extra = min(int((len(clip) / slot - 1) * 100) + 3, 40)
            wavp = _clip_path(text, gender, style, extra, workdir, r_off, p_off)
            clip = AudioSegment.from_wav(str(wavp))
            if len(clip) > slot:
                tempo = min(len(clip) / slot, config.MAX_SPEEDUP)
                fast = workdir / f"{wavp.stem}_t{tempo:.2f}.wav"
                if not fast.exists():
                    speed_up(wavp, fast, tempo)
                clip = AudioSegment.from_wav(str(fast))
        clip = _level(clip, STYLES[style][2] + g_off)
        mix = mix.overlay(clip, position=max(0, int((s["start"] + shift) * 1000)))

    progress("Video me merge kar rahe hain...", 93)
    dub = workdir / "dub.wav"
    mix.export(dub, format="wav")
    out = workdir / "output.mp4"
    merge(video, dub, out)
    progress("Ho gaya!", 100)
    return out, segments
