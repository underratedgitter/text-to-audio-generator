# Text-to-Audio Generator

Turns text into an MP3 voiceover, from the command line or a small desktop window. Uses free TTS engines — no API key, no per-character billing.

---

## Engines

| Engine | Notes |
|---|---|
| **edge-tts** (default) | Microsoft Edge's neural voices. Natural enough for narration, and free. |
| **gTTS** | Google Translate's TTS. Flatter, but a dependable fallback. |

Both are imported defensively — if one isn't installed, the tool still runs on the other rather than failing at import.

Set the engine and voice in `config/config.yaml`:

```yaml
tts:
  engine: "edge-tts"           # edge-tts or gtts
  voice: "en-US-JennyNeural"
  speaking_rate: 1.0
  pitch: 0
```

`edge-tts --list-voices` shows what else is available — hundreds of voices across dozens of languages.

---

## Install

```bash
pip install -r requirements.txt
python verify_setup.py
```

`verify_setup.py` checks your Python version, each required package, ffmpeg, the config file and the output directories, then tells you exactly what is missing — rather than letting you find out on first run.

`pydub` is optional and only used for accurate duration reporting; ffmpeg likewise.

---

## Command line

```bash
# straight from an argument
python src/main.py --text "Welcome to the lecture on distributed systems."

# from a file
python src/main.py --text-file script.txt

# name the output folder instead of taking a timestamp
python src/main.py --text-file script.txt --output-id lecture-04

# a different config
python src/main.py --text-file script.txt --config config/slow-voice.yaml
```

| Flag | Does |
|---|---|
| `--text` | text to convert, inline |
| `--text-file` | path to a file to convert |
| `--output-id` | output folder under `output/`; defaults to a timestamp |
| `--config` | config file; defaults to `config/config.yaml` |

Output lands in `output/<id>/` alongside a JSON record of what was generated.

---

## Desktop window

```bash
python src/dashboard.py
```

A small Tkinter interface: pick or paste a script, press **Generate Voiceover**, watch the status line. Same engine underneath — the GUI is a front end over `VoiceoverGenerator`, not a second implementation.

---

## Layout

```
src/
  main.py         CLI entry point and argument parsing
  voiceover.py    VoiceoverGenerator — engine selection, synthesis, duration
  dashboard.py    Tkinter front end over the same generator
  utils.py        Config, Logger, FileManager
config/
  config.yaml     engine, voice, rate, pitch, logging, output paths
verify_setup.py   preflight check for dependencies and directories
```

Configuration is read through a small `Config` helper with dotted lookups (`tts.voice`), so a missing key falls back to a default instead of raising.
