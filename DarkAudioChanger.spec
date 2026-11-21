# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [("app/static", "app/static"), ("VERSION", ".")]
binaries = []
hidden = [
    "app.main", "app.pipeline", "app.gender", "app.translate", "app.media", "app.audio_utils", "app.config",
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto", "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto", "uvicorn.lifespan.on", "multipart", "python_multipart",
]
for pkg in ["faster_whisper", "ctranslate2", "av", "onnxruntime", "tokenizers", "huggingface_hub",
            "librosa", "soundfile", "soxr", "lazy_loader", "audioread", "pooch", "numba", "llvmlite",
            "edge_tts", "certifi", "deep_translator", "anthropic", "webview", "clr_loader", "pythonnet"]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hidden += h
    except Exception as e:
        print("collect_all skipped:", pkg, e)

a = Analysis(["launcher.py"], pathex=["."], binaries=binaries, datas=datas,
             hiddenimports=hidden, hookspath=[], runtime_hooks=[],
             excludes=["tkinter", "matplotlib", "IPython", "pytest"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="DarkAudioChanger",
          debug=False, strip=False, upx=False, console=False, icon="assets/icon.ico")
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="DarkAudioChanger")
