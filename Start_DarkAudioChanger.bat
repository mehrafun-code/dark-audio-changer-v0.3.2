@echo off
setlocal
cd /d "%~dp0"
title Dark Audio Changer
echo.
echo  ===== DARK AUDIO CHANGER =====
echo.

if not exist "venv\Scripts\python.exe" (
  echo [1/3] Pehli baar setup ho raha hai, thoda time lagega...
  py -3.11 -m venv venv 2>nul
)
if not exist "venv\Scripts\python.exe" python -m venv venv 2>nul
if not exist "venv\Scripts\python.exe" (
  echo.
  echo Python nahi mila. Python 3.11 install karo:
  echo https://www.python.org/downloads/release/python-3119/
  echo Install karte waqt "Add python.exe to PATH" ko tick karna.
  pause
  exit /b 1
)

if not exist "venv\.ready" (
  echo [2/3] Libraries install ho rahi hain, internet chalu rakho...
  "venv\Scripts\python.exe" -m pip install --upgrade pip
  "venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
  if errorlevel 1 (
    echo.
    echo Install fail hua. Upar ka error mujhe bhejo.
    pause
    exit /b 1
  )
  echo ok> "venv\.ready"
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [3/3] FFmpeg install ho raha hai...
  winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
  echo.
  echo FFmpeg install hua. Ye window band karo aur Start_DarkAudioChanger.bat dobara chalao.
  echo Agar phir bhi error aaye to ffmpeg.org se FFmpeg khud install karo.
  pause
  exit /b 0
)

echo App khul rahi hai...
"venv\Scripts\python.exe" launcher.py
if errorlevel 1 pause
