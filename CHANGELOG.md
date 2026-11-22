# Changelog

## 0.4.1 (build 11)
- **English line bhi editable** (Whisper ki galti theek karo) aur uska apna Play (original awaaz) - Hindi line ke jaise; edit karke TRANSLATE dabao to naya English translate hota hai
- Hindi line ka apna gol Play (dub awaaz turant sunao), English ka alag Play
- **AWAAZ EDIT** har line ke liye: Speed (-50% se +50%), Pitch (-30 se +30 Hz), Volume (-12 se +12 dB), Sync (-2 se +2 sec), RESET
- Emotion andaaz 8: Normal, Josh, Khushi, Dheere, Udaas, Gussa, Chillana, Fusfusa
- HINDI SUNO me speed/pitch/volume/andaaz sab turant lagta hai
- Line number (#1, #2...) dikhta hai

## 0.4.0 (build 10)
- **Translation theek**: ab Claude (agar API key ho) -> Google -> doosra Google -> MyMemory, 4 tareeke. Sirf wahi result maana jata hai jisme Hindi (devanagari) ho. Jo line translate na ho wo laal warning ke saath dikhti hai (pehle chup-chap English reh jati thi)
- Settings me **Claude API key** (optional) - slang ('bro', 'bruh') ka natural bolchal wali Hindi me translation, timing ke hisaab se chhoti/lambi
- **Har line ke aage Play (original video me sirf wahi line chalti hai)**, **HINDI SUNO** (us line ki dub awaaz turant sunao), **TRANSLATE** (sirf us line ko dobara translate), **HINGLISH -> देवनागरी**
- Hindi text editable, video par **Hindi caption** aur transcript me Hindi dikhta hai
- **Awaaz zyada natural**: har line ka andaaz (Normal / Josh / Dheere / Gussa), original awaaz ki loudness se auto-suggest, lambi line ke liye awaaz ki speed natural tareeke se badhti hai, sab lines barabar loudness par
- "Sab line Hindi me translate karo" button, aur dub se pehle English-jaisi lines ki warning

## 0.3.6 (build 9)
- Fix: `[WinError 2] The system cannot find the file specified` (Hindi awaaz banate waqt). pydub ko `ffprobe` chahiye tha jo exe me nahi tha. Ab awaaz seedha ffmpeg se wav me badalti hai (ffprobe ki zaroorat nahi) aur workflow `ffprobe.exe` bhi saath rakhta hai
- Workflow ek hi `main.yml` me (Linux check + Windows build)

## 0.3.5 (build 8)
- Fix: Hindi awaaz `403 Invalid response status` (purana edge-tts). Ab `edge-tts>=7.0.0`, 3 baar retry, aur saaf error message
- **Video preview review se pehle hi**: dub banne se pehle original video + original audio waveform + timeline dikhte hain (browser-safe `preview.mp4` banti hai, mkv/mov bhi chalenge)
- **Folder settings**: dub video kahan save ho (CHUNO button se folder chuno), temp/kaam ki files kahan rahein (C: drive ki jagah koi bhi drive), Whisper model bhi usi folder me
- Auto-save option, TEMP SAAF KARO button, DEFAULT PAR WAPAS
- Python/ffmpeg ki temporary files bhi chune hue work folder me
- Awaaz banne me error aaye to dobara analyze nahi karna padta: editor khula rehta hai, seedha DUB BANAO se retry
- Save/Download file ka naam ab original video ke naam par: `<naam>_hindi.mp4`

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
