# Changelog

## 0.3.2 (build 5)
- **Windows ready-made app (installer nahi)**: GitHub Actions `Build Windows App` PyInstaller se `DarkAudioChanger.exe` wala zip banata hai (FFmpeg andar shamil)
- Launcher exe-safe: log file, error popup, ffmpeg console windows band
- `main.yml` sirf Linux syntax/Docker check, Windows build `windows.yml` me

## 0.3.1 (build 4)
- Naye repo ke liye poora package; workflow file ka naam `main.yml`, syntax check me `launcher.py` bhi shamil

## 0.3.0 (build 3)
- **Desktop software**: `Start_DarkAudioChanger.bat` (Windows) / `run.sh` (Mac, Linux) - double click se app apni window me khulti hai (`launcher.py`)
- **Preview Studio**: dub ke baad video preview, play/pause, speed, timeline par click/drag se seek
- Original audio aur Hindi dub audio ki alag waveforms, ek hi playhead aur time ruler ke saath
- Awaaz mixer: Original / Hindi dub / Dono, alag volume sliders
- Live transcript: abhi kaun bol raha hai (male/female), English aur Hindi line
- Save button (Downloads/DarkAudioChanger me save + folder khulta hai) aur Download button
- Fix: dub audio ab 24 kHz par banti hai (pehle 11 kHz se quality kharab thi)
- Fix: page seedha file se khola jaye to saaf warning dikhti hai (logo/upload fail ka karan)

## 0.2.0
- App ka naam Dark Audio Changer, naya sci-fi UI, logo

## 0.1.0
- Pehla version: upload -> English STT (Whisper) -> gender detect -> Hindi translate -> Hindi TTS -> merge video
