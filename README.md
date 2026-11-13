# Text-to-Audio Generator

Turns text into an MP3 voiceover, from the command line or a small desktop window. Uses free TTS engines — no API key, no per-character billing.

---

## Engines

| Engine | Notes |
|---|---|
| **edge-tts** (default) | Microsoft Edge's neural voices. Natural enough for narration, and free. |
| **gTTS** | Google Translate's TTS. Flatter, but a dependable fallback. |
| **offline** | System speech synthesizer via pyttsx3. Works with zero internet; requires ffmpeg for MP3 conversion. |

All engines are imported defensively — if an engine is not installed, the tool skips it rather than failing at import.

When generating audio, `VoiceoverGenerator` uses an automatic fallback chain: it tries the configured engine first, then attempts any remaining available engines (`edge-tts`, `gtts`, `offline`) before raising an error. If an engine fails mid-stream or produces an empty file, the partial file is cleaned up before trying the next engine.

Set the engine and voice in `config/config.yaml`:

```yaml
tts:
  engine: "edge-tts"           # edge-tts, gtts, or offline
  voice: "en-US-JennyNeural"
  speaking_rate: 1.0
  pitch: 0
```

`edge-tts --list-voices` shows what else is available for Edge-TTS — hundreds of voices across dozens of languages.

---

## Install

Requires Python 3.8+.

```bash
pip install -r requirements.txt
python verify_setup.py
```

`verify_setup.py` checks your Python version, required packages, ffmpeg, the config file, and output directories before first run.

Dependencies:
- `edge-tts` and `gtts` provide online speech generation.
- `pyttsx3` provides the offline fallback engine.
- `ffmpeg` is required when using the `offline` engine (to convert synthesizer output to MP3) and for `pydub` duration measurement. Online engines do not require ffmpeg.
- `pydub` is optional and used for accurate audio duration reporting; on Python 3.13+, `audioop-lts` is installed to maintain compatibility. If `pydub` is unavailable, duration is estimated from word count and speaking rate (~150 wpm).

To verify the offline fallback independently without internet:

```bash
python verify_offline.py
```

---

## Testing

Run the unit test suite:

```bash
pytest tests
```

Tests run offline without invoking remote TTS services, covering text cleaning, rate/pitch formatting, duration estimation, fallback order, path traversal guards, and configuration loading.

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

# interactive input (prompts for multi-line text; press Enter on empty line to finish)
python src/main.py
```

| Flag | Does |
|---|---|
| `--text` | text to convert, inline |
| `--text-file` | path to a file to convert |
| `--output-id` | output folder under `output/`; defaults to a timestamp |
| `--config` | config file; defaults to `config/config.yaml` |

Output lands in `output/<id>/` (`voiceover.mp3`) alongside `voiceover_metadata.json` recording the engine, duration, word count, and timestamp.

---

## Desktop window

```bash
python src/dashboard.py
```

A small Tkinter interface: pick or paste a script, press **Generate Voiceover**, watch the status line. Audio generation runs in a background thread to keep the window responsive. Same engine underneath — the GUI is a front end over `VoiceoverGenerator`, not a second implementation.

---

## Layout

```
src/
  main.py            CLI entry point, interactive input, argument parsing
  voiceover.py       VoiceoverGenerator — engine selection, synthesis, fallback chain, duration
  dashboard.py       Tkinter front end over the same generator
  utils.py           Config, Logger, FileManager, SafetyChecker
config/
  config.yaml        engine, voice, rate, pitch, logging, output paths
tests/
  test_voiceover.py  tests for text cleaning, rate/pitch formatting, fallbacks
  test_utils.py      tests for config lookups, path safety, file manager
verify_offline.py    driver to test offline pyttsx3 fallback with online engines disabled
verify_setup.py      preflight check for dependencies and directories
```

Configuration is read through a `Config` helper with dotted lookups (`tts.voice`), so a missing key falls back to a default instead of raising.
