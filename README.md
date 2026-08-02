<div align="center">

# 🎙️ Text-to-Audio Generator

*A flexible Python CLI + GUI to convert text into high-quality MP3 voiceovers in seconds.*

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![edge-tts](https://img.shields.io/badge/TTS-edge--tts%20%7C%20gTTS-0078D4?style=for-the-badge&logo=microsoft&logoColor=white)
![Output](https://img.shields.io/badge/Output-MP3-FF6B35?style=for-the-badge&logo=audacity&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

<br/>

[![Last Commit](https://img.shields.io/github/last-commit/underratedgitter/text-to-audio-generator?style=flat-square&color=purple)](https://github.com/underratedgitter/text-to-audio-generator/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/underratedgitter/text-to-audio-generator?style=flat-square&color=orange)](https://github.com/underratedgitter/text-to-audio-generator)

</div>

---

## 📌 Overview

A minimal but flexible Python tool for converting text into MP3 voiceovers. Supports multiple TTS engines, configurable voice settings, and both a desktop GUI and a CLI interface — perfect for narration scripts, accessibility tools, or content pipelines.

---

## ✨ Features

| Feature | Details |
|:---|:---|
| 🎚️ **Dual TTS Engines** | `edge-tts` (neural, high quality) or `gTTS` (Google TTS) |
| 🖥️ **Desktop GUI** | Tkinter-based dashboard for non-CLI users |
| ⌨️ **CLI Interface** | Pass text directly or read from a file |
| 📁 **Organised Output** | Saves to `output/<timestamp>/voiceover.mp3` automatically |
| ⚙️ **YAML Config** | Tune voice, speaking rate, and pitch via `config/config.yaml` |
| ✅ **Setup Verification** | Built-in `verify_setup.py` to confirm dependencies are ready |

---

## 🛠️ Tech Stack

| Component | Tool |
|:---|:---|
| **Runtime** | Python 3.10+ |
| **Primary TTS** | [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge neural voices |
| **Fallback TTS** | [gTTS](https://gtts.readthedocs.io/) — Google Text-to-Speech |
| **GUI** | Tkinter |
| **Config** | YAML (`config/config.yaml`) |

---

## 🔊 TTS Engine Comparison

| Feature | `edge-tts` (default) | `gTTS` |
|:---|:---:|:---:|
| Voice Quality | ⭐⭐⭐⭐⭐ Neural | ⭐⭐⭐ Standard |
| Offline Support | ❌ Requires internet | ❌ Requires internet |
| Voice Options | 300+ voices & locales | Limited |
| Speaking Rate Control | ✅ Yes | ⚠️ Limited |
| Pitch Control | ✅ Yes | ❌ No |

---

## 📁 Project Structure

```
text-to-audio-generator/
├── src/
│   ├── dashboard.py        # Tkinter GUI dashboard
│   ├── main.py             # CLI entry point
│   ├── voiceover.py        # TTS engine wrapper (edge-tts / gTTS)
│   ├── utils.py            # Helper utilities
│   └── __init__.py
├── config/
│   └── config.yaml         # Voice & engine configuration
├── output/                 # Generated MP3 files (auto-created)
│   └── <timestamp>/
│       └── voiceover.mp3
├── requirements.txt
├── verify_setup.py         # Dependency checker
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Internet connection (required for both TTS engines)

### Install

```bash
git clone https://github.com/underratedgitter/text-to-audio-generator.git
cd text-to-audio-generator
pip install -r requirements.txt
```

### Verify Setup

```bash
python verify_setup.py
```

---

## 🎛️ Usage

### GUI Dashboard (Recommended)

```bash
python src/dashboard.py
```

Opens a desktop window — type or paste your text and click Generate.

### CLI — Inline Text

```bash
python src/main.py --text "Hello, this is my narration."
```

### CLI — From File

```bash
python src/main.py --text-file my_script.txt
```

### CLI — Custom Output Name

```bash
python src/main.py --text "Sample narration" --output-id my_audio_run
```

### Interactive Mode

```bash
python src/main.py
# then follow the prompts
```

---

## ⚙️ Configuration

Edit `config/config.yaml` to change the TTS engine, voice, speaking rate, and pitch:

```yaml
tts:
  engine: "edge-tts"          # or "gtts"
  voice: "en-US-JennyNeural"  # edge-tts voice name
  speaking_rate: 1.0          # 0.5 (slow) to 2.0 (fast)
  pitch: 0                    # semitone offset, e.g. +5 or -3
```

### Popular `edge-tts` Voices

| Voice ID | Locale | Style |
|:---|:---|:---|
| `en-US-JennyNeural` | US English | Friendly, conversational |
| `en-US-GuyNeural` | US English | Professional, male |
| `en-GB-SoniaNeural` | British English | Clear, female |
| `en-IN-NeerjaNeural` | Indian English | Natural, female |

> Run `edge-tts --list-voices` to see all 300+ available voices.

---

## 📜 License

MIT © [Suraj Patel](https://github.com/underratedgitter)
