# Text to Audio Generator

Minimal Python CLI to convert text into an MP3 voiceover.

## What it does

- Accepts text directly (`--text`) or from a file (`--text-file`)
- Generates audio with `edge-tts` (default) or `gTTS`
- Saves output to `output/<timestamp>/voiceover.mp3`

## Setup

```bash
cd "Faceless-youtube-video-pipeline"
pip install -r requirements.txt
```

## Usage

### Dashboard (recommended)

```bash
python src/dashboard.py
```

This opens a desktop GUI window.

### Interactive mode

```bash
cd src
python main.py
```

### Text argument

```bash
python main.py --text "Hello, this is my narration."
```

### Text file

```bash
python main.py --text-file ../my_script.txt
```

### Custom output folder name

```bash
python main.py --text "Sample" --output-id my_audio_run
```

## Configuration

Edit `config/config.yaml`:

```yaml
tts:
  engine: "edge-tts"
  voice: "en-US-JennyNeural"
  speaking_rate: 1.0
  pitch: 0
```

## Quick verify

```bash
python verify_setup.py
```
