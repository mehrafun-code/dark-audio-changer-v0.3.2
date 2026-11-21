# Changelog

## 0.3.4 (build 7)
- Fix: Google translate "Too many requests" error. Ab har line ke beech gap, rate-limit par ruk kar dobara try. Phir bhi fail ho to English line rehti hai jise editor me theek kar sakte ho
- **Manual voice chunna**: upload ke time "Auto / Sab Male / Sab Female"
- **Voice Editor**: dub se pehle har line ka Male/Female chuno aur Hindi text edit karo (Sab Male, Sab Female, Auto wapas buttons)
- Dub ke baad bhi galat voice theek karke **DUBARA BANAO** (pehle ki bani awaaz cache hoti hai, isliye jaldi hota hai)
- Time button par click karke video us line par sun sakte ho

## 0.3.3 (build 6)
- Fix: `cublas64_12.dll is not found` error. Whisper ab default CPU par chalta hai (`WHISPER_DEVICE=cpu`), GPU error aaye to apne aap CPU par fallback

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
