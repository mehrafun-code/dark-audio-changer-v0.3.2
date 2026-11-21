import os
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
# Resources (VERSION, static) PyInstaller bundle ke andar; data exe ke bagal me
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
APP_DIR = Path(sys.executable).parent if FROZEN else BASE_DIR
DATA_DIR = APP_DIR / "data"
VERSION = (BASE_DIR / "VERSION").read_text().strip()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
# cpu = sabke liye safe. GPU (cuda) ke liye alag CUDA libraries chahiye
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
VOICE_MALE = os.getenv("VOICE_MALE", "hi-IN-MadhurNeural")
VOICE_FEMALE = os.getenv("VOICE_FEMALE", "hi-IN-SwaraNeural")
TARGET_LANG = os.getenv("TARGET_LANG", "hi")
MAX_SPEEDUP = float(os.getenv("MAX_SPEEDUP", "1.5"))
