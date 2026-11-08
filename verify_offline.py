"""Driver: run the real CLI pipeline with both online TTS engines disabled,
forcing the fully-offline pyttsx3 engine end-to-end."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import voiceover

voiceover.edge_tts = None  # simulate edge-tts not reachable
voiceover.gTTS = None      # simulate gTTS not reachable

import main as app

sys.argv = [
    "main.py",
    "--text",
    "This is the genuine no-internet disk fallback test.",
    "--output-id",
    "offline-verify",
]
app.main()
