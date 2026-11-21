import asyncio
import hashlib
from pathlib import Path

import edge_tts
from faster_whisper import WhisperModel
from pydub import AudioSegment

from . import config
from .audio_utils import extract_audio, speed_up, merge
from .gender import detect_gender
from .translate import translate_all

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(config.WHISPER_MODEL, device=config.WHISPER_DEVICE, compute_type="int8")
    return _model


def transcribe(wav):
    """English speech -> segments. GPU/CUDA error aaye to CPU par fallback."""
    global _model
    try:
        segs, _ = get_model().transcribe(str(wav), language="en", vad_filter=True)
        return list(segs)
    except Exception as e:
        if config.WHISPER_DEVICE != "cpu" and any(k in str(e).lower() for k in ("cublas", "cuda", "cudnn")):
            _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
            segs, _ = _model.transcribe(str(wav), language="en", vad_filter=True)
            return list(segs)
        raise


def tts(text: str, voice: str, out: Path):
    asyncio.run(edge_tts.Communicate(text, voice).save(str(out)))


def voice_for(gender: str) -> str:
    return config.VOICE_FEMALE if gender == "female" else config.VOICE_MALE


def analyze(video: Path, workdir: Path, progress, gender_mode: str = "auto"):
    """Stage 1: audio -> English text -> gender -> Hindi text. Awaaz abhi nahi banti."""
    workdir.mkdir(parents=True, exist_ok=True)
    wav = workdir / "audio.wav"

    progress("Audio nikal rahe hain...", 5)
    extract_audio(video, wav)

    progress("Speech-to-text (English)...", 15)
    raw = transcribe(wav)
    segments = [{"id": i, "start": s.start, "end": s.end, "text": s.text.strip()}
                for i, s in enumerate(x for x in raw if x.text.strip())]
    if not segments:
        raise RuntimeError("Video me koi speech nahi mili.")

    progress("Male/Female pehchan...", 35)
    for s in segments:
        if gender_mode in ("male", "female"):
            s["auto_gender"] = s["gender"] = gender_mode
        else:
            s["auto_gender"] = s["gender"] = detect_gender(wav, s["start"], s["end"])

    progress("Hindi translation...", 45)
    hindi = translate_all([s["text"] for s in segments])
    for s, h in zip(segments, hindi):
        s["hindi"] = h
    return segments


def render(video: Path, workdir: Path, segments: list, progress):
    """Stage 2: Hindi text + gender se awaaz banao, mix karo, video me jodo."""
    wav = workdir / "audio.wav"
    total_ms = int(AudioSegment.from_file(wav).duration_seconds * 1000) + 1000
    mix = AudioSegment.silent(duration=total_ms, frame_rate=24000).set_channels(1)

    n = len(segments)
    for i, s in enumerate(segments):
        progress(f"Hindi awaaz ban rahi hai ({i+1}/{n})...", 50 + int(40 * i / max(n, 1)))
        text = (s.get("hindi") or "").strip()
        if not text:
            continue
        voice = voice_for(s.get("gender", "male"))
        key = hashlib.md5(f"{voice}|{text}".encode("utf-8")).hexdigest()[:12]
        raw = workdir / f"tts_{key}.mp3"
        if not raw.exists():  # pehle bani hui awaaz dobara use hogi
            tts(text, voice, raw)
        clip = AudioSegment.from_file(raw)

        nxt = segments[i + 1]["start"] if i + 1 < n else s["end"] + 3
        slot = max(nxt - s["start"] - 0.1, 0.5) * 1000
        if len(clip) > slot:
            tempo = min(len(clip) / slot, config.MAX_SPEEDUP)
            fast = workdir / f"tts_{key}_{tempo:.2f}.mp3"
            if not fast.exists():
                speed_up(raw, fast, tempo)
            clip = AudioSegment.from_file(fast)
        mix = mix.overlay(clip, position=int(s["start"] * 1000))

    progress("Video me merge kar rahe hain...", 93)
    dub = workdir / "dub.wav"
    mix.export(dub, format="wav")
    out = workdir / "output.mp4"
    merge(video, dub, out)
    progress("Ho gaya!", 100)
    return out, segments
