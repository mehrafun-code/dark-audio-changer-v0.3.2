import json
import re
import time

from . import config


def _claude(texts: list[str]) -> list[str]:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        "Translate these English dialogue lines into natural, spoken Hindi (Devanagari), "
        "like in a movie dub. Keep each line short and conversational. "
        "Return ONLY a JSON array of strings, same order and same length.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    msg = client.messages.create(
        model=config.CLAUDE_MODEL, max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    out = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\[.*\]", out, re.S)
    result = json.loads(m.group(0))
    if len(result) != len(texts):
        raise ValueError("Translation length mismatch")
    return result


def _google_one(tr, text: str) -> str:
    """Ek line translate karo. Rate-limit aaye to ruk kar dobara try."""
    if not text.strip():
        return text
    for attempt in range(6):
        try:
            return tr.translate(text) or text
        except Exception:
            if attempt == 5:
                break
            time.sleep(1.5 * (2 ** attempt))  # 1.5, 3, 6, 12, 24 sec
    return text  # fail hua: English rehne do, user review me theek kar sakta hai


def _google(texts: list[str]) -> list[str]:
    from deep_translator import GoogleTranslator
    tr = GoogleTranslator(source="auto", target=config.TARGET_LANG)
    out = []
    for t in texts:
        out.append(_google_one(tr, t))
        time.sleep(config.TRANSLATE_DELAY)  # 5 requests/sec limit se bachne ke liye
    return out


def translate_all(texts: list[str]) -> list[str]:
    if config.ANTHROPIC_API_KEY:
        try:
            out = []
            for i in range(0, len(texts), 40):  # batches
                out += _claude(texts[i:i + 40])
            return out
        except Exception as e:
            print("Claude translate failed, fallback to Google:", e)
    return _google(texts)
