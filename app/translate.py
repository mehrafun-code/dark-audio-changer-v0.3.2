"""English -> Hindi (Devanagari). Claude (best) -> Google (free) -> MyMemory (free) fallback chain."""
import json
import re
import time
import urllib.parse
import urllib.request

from . import config, settings

DEV = re.compile(r"[\u0900-\u097F]")


def _key() -> str:
    return settings.api_key() or config.ANTHROPIC_API_KEY


def has_hindi(text: str) -> bool:
    return bool(DEV.search(text or ""))


# ---------------- Claude ----------------
def _claude(items: list[tuple[str, float]]) -> list[str]:
    import anthropic
    client = anthropic.Anthropic(api_key=_key())
    payload = [{"en": t, "seconds": round(sec, 1)} for t, sec in items]
    prompt = (
        "You are a professional Hindi dubbing script writer. Translate each English dialogue line into natural, "
        "casual SPOKEN Hindi in Devanagari, the way young native speakers actually talk (not bookish, not word-by-word).\n"
        "Rules:\n"
        "- Keep the same meaning, emotion and attitude. Slang like 'bro' -> 'भाई' or 'यार', 'bruh' -> 'यार'.\n"
        "- The line must be speakable in about the given number of seconds; keep it similar in length.\n"
        "- Use punctuation (commas, '...', '!', '?') to create natural pauses and emphasis.\n"
        "- Write numbers as Hindi words. Keep personal names as names (in Devanagari).\n"
        "- Output ONLY a JSON array of strings, same order and same length as the input. No commentary.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    msg = client.messages.create(model=config.CLAUDE_MODEL, max_tokens=6000,
                                 messages=[{"role": "user", "content": prompt}])
    out = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\[.*\]", out, re.S)
    result = json.loads(m.group(0))
    if len(result) != len(items):
        raise ValueError("Translation length mismatch")
    return [str(x) for x in result]


# ---------------- free providers ----------------
def _gtx(text: str) -> str:
    q = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": config.TARGET_LANG, "dt": "t", "q": text})
    req = urllib.request.Request("https://translate.googleapis.com/translate_a/single?" + q,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    return "".join(part[0] for part in data[0] if part and part[0])


def _deep(text: str) -> str:
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="auto", target=config.TARGET_LANG).translate(text)


def _mymemory(text: str) -> str:
    from deep_translator import MyMemoryTranslator
    return MyMemoryTranslator(source="en-US", target="hi-IN").translate(text[:480])


FREE = (("Google", _gtx), ("Google2", _deep), ("MyMemory", _mymemory))


def _free_one(text: str):
    """(hindi, provider) ya (None, last_error)."""
    last = ""
    for name, fn in FREE:
        for attempt in range(3):
            try:
                r = (fn(text) or "").strip()
                if has_hindi(r):
                    return r, name
                break  # result me Hindi nahi: agla provider
            except Exception as e:
                last = f"{name}: {e}"
                time.sleep(1.2 * (attempt + 1))
    return None, last


def translate_all(texts: list[str], seconds: list[float] | None = None) -> dict:
    """Return {hindi:[...], failed:[idx], provider:str, note:str}."""
    secs = seconds or [3.0] * len(texts)
    out = list(texts)
    done = [False] * len(texts)
    providers, notes = set(), []

    if _key():
        try:
            for i in range(0, len(texts), 25):
                batch = list(zip(texts[i:i + 25], secs[i:i + 25]))
                for j, h in enumerate(_claude(batch)):
                    if has_hindi(h):
                        out[i + j], done[i + j] = h, True
            if any(done):
                providers.add("Claude")
        except Exception as e:
            notes.append(f"Claude translate nahi chala ({e}). Key check karo.")

    last_err = ""
    for i, t in enumerate(texts):
        if done[i] or not t.strip():
            done[i] = done[i] or not t.strip()
            continue
        h, info = _free_one(t)
        if h:
            out[i], done[i] = h, True
            providers.add(info)
        else:
            last_err = info
        time.sleep(config.TRANSLATE_DELAY)

    failed = [i for i, d in enumerate(done) if not d]
    if failed:
        notes.append(f"{len(failed)} line ka Hindi translation nahi ho paya"
                     + (f" ({last_err})" if last_err else "") + ".")
    return {"hindi": out, "failed": failed, "provider": "+".join(sorted(providers)) or "-", "note": " ".join(notes)}


def translit(text: str) -> str:
    """Hinglish (Roman) -> Devanagari. Google Input Tools."""
    q = urllib.parse.urlencode({"text": text, "itc": "hi-t-i0-und", "num": 1, "cp": 0, "cs": 1,
                                "ie": "utf-8", "oe": "utf-8", "app": "demopage"})
    req = urllib.request.Request("https://inputtools.google.com/request?" + q, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data[0] != "SUCCESS":
        raise RuntimeError("transliteration fail")
    return data[1][0][1][0]
