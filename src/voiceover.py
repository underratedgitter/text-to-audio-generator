"""
Voiceover Generation Module
Generates AI voiceover from script using FREE TTS engines.
Supports: edge-tts (recommended), gTTS (backup), pyttsx3 (offline, last resort)
"""

import asyncio
import shutil
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from utils import Config, Logger, FileManager


class VoiceoverGenerator:
    """Generate natural-sounding voiceover using free TTS engines"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.setup('Voiceover', config)
        self.file_manager = FileManager(config)

        # TTS settings
        self.engine = config.get('tts.engine', 'edge-tts')
        self.voice = config.get('tts.voice', 'en-US-JennyNeural')
        self.speaking_rate = config.get('tts.speaking_rate', 1.0)
        self.pitch = config.get('tts.pitch', 0)

    def generate_voiceover(self, script_data: Dict[str, Any], video_dir: Path) -> Dict[str, Any]:
        """
        Generate voiceover audio from script
        Returns: Voiceover data with timing information
        """
        self.logger.info(f"Generating voiceover using {self.engine}...")

        # Get full script text
        script_text = script_data['full_script']

        # Remove scene markers for TTS
        clean_text = self._clean_text_for_tts(script_text)

        # Generate audio file
        output_path = video_dir / 'voiceover.mp3'

        if not clean_text:
            raise ValueError("Nothing to speak: the text is empty once scene markers are removed")

        if self.engine not in ('edge-tts', 'gtts', 'offline'):
            raise ValueError(f"Unsupported TTS engine: {self.engine}")

        # Use a fallback chain so audio gets produced even when individual
        # engines fail: the configured engine first, then the online engines,
        # and finally the fully-offline engine — so a run never fails just
        # because the network does. Each engine only gets tried if installed.
        chain = [self.engine]
        for engine in ('edge-tts', 'gtts', 'offline'):
            if engine not in chain:
                chain.append(engine)
        engines_to_try = [
            engine for engine in chain
            if self._engine_available(engine)
        ]
        if not engines_to_try:
            raise RuntimeError(
                "No TTS engine is available. Install at least one of: "
                "edge-tts, gtts, pyttsx3 (pip install pyttsx3 for offline TTS)"
            )

        engine_used = self.engine
        last_error = None
        for engine in engines_to_try:
            try:
                if engine == 'edge-tts':
                    self._generate_edge_tts(clean_text, output_path)
                elif engine == 'gtts':
                    self._generate_gtts(clean_text, output_path)
                else:
                    self._generate_offline_tts(clean_text, output_path)

                if output_path.exists() and output_path.stat().st_size > 0:
                    engine_used = engine
                    last_error = None
                    break

                raise RuntimeError(
                    f"TTS engine '{engine}' did not produce a valid audio file"
                )
            except Exception as exc:
                last_error = exc
                self._remove_partial_output(output_path)
                remaining = engines_to_try[engines_to_try.index(engine) + 1:]
                if remaining:
                    self.logger.warning(
                        f"{engine} failed ({exc}). Falling back to '{remaining[0]}'..."
                    )

        if last_error is not None:
            raise last_error
        duration = self._get_audio_duration(output_path, clean_text)

        # Create voiceover data
        voiceover_data = {
            'audio_file': str(output_path),
            'duration_seconds': duration,
            'engine': engine_used,
            'voice': self.voice,
            'speaking_rate': self.speaking_rate,
            'word_count': len(clean_text.split()),
            'generated_at': self.file_manager.get_timestamp()
        }

        # Save metadata
        metadata_path = video_dir / 'voiceover_metadata.json'
        self.file_manager.save_json(voiceover_data, metadata_path)

        self.logger.info(f"Voiceover generated successfully. Duration: {duration:.1f}s")

        return voiceover_data

    def _engine_available(self, engine: str) -> bool:
        """Whether the requested engine's library is installed."""
        if engine == 'edge-tts':
            return edge_tts is not None
        if engine == 'gtts':
            return gTTS is not None
        if engine == 'offline':
            return pyttsx3 is not None
        return False

    def _remove_partial_output(self, output_path: Path) -> None:
        """TTS engines may leave a zero-byte or partial file when they fail
        mid-stream. Remove it so a failed run never looks like a success."""
        if output_path.exists():
            try:
                output_path.unlink()
                self.logger.info(
                    f"Removed incomplete voiceover file after failure: {output_path}"
                )
            except OSError as cleanup_exc:
                self.logger.warning(
                    f"Could not remove incomplete voiceover file: {cleanup_exc}"
                )

    def _clean_text_for_tts(self, text: str) -> str:
        """Remove scene markers and format text for TTS"""
        # Remove [SCENE: ...] markers
        text = re.sub(r'\[SCENE:[^\]]+\]', '', text)

        # Remove excessive whitespace
        text = re.sub(r'\n\n+', '\n\n', text)
        text = text.strip()

        return text

    def _generate_edge_tts(self, text: str, output_path: Path) -> None:
        """Generate voiceover using Edge-TTS (FREE, high quality)."""
        if edge_tts is None:
            raise ImportError("edge-tts not installed. Install with: pip install edge-tts")

        # Run async TTS generation
        asyncio.run(self._async_edge_tts(text, output_path))

    async def _async_edge_tts(self, text: str, output_path: Path):
        """Async method for Edge-TTS"""
        # Adjust voice parameters
        rate = self._format_rate(self.speaking_rate)
        pitch_str = self._format_pitch(self.pitch)

        # Generate speech
        communicate = edge_tts.Communicate(text, self.voice, rate=rate, pitch=pitch_str)
        await communicate.save(str(output_path))

    def _generate_gtts(self, text: str, output_path: Path) -> None:
        """
        Generate voiceover using gTTS (FREE, basic quality)
        Fallback option if Edge-TTS fails
        """
        if gTTS is None:
            raise ImportError("gtts not installed. Install with: pip install gtts")

        try:
            # Create TTS object
            tts = gTTS(text=text, lang='en', slow=False)

            # Save to file
            tts.save(str(output_path))

        except Exception as e:
            self.logger.error(f"Error generating gTTS voiceover: {e}")
            raise

    def _generate_offline_tts(self, text: str, output_path: Path) -> None:
        """Last-resort engine: renders with the OS speech synthesizer through
        pyttsx3 (works with zero internet), then converts the render to MP3.
        Requires ffmpeg on PATH for the MP3 conversion."""
        if pyttsx3 is None:
            raise ImportError(
                "pyttsx3 not installed. Install with: pip install pyttsx3"
            )

        if shutil.which('ffmpeg') is None:
            raise RuntimeError(
                "ffmpeg is required to convert the offline TTS output to "
                "MP3. Install ffmpeg and retry."
            )

        with tempfile.TemporaryDirectory() as tmpdirname:
            # macOS pyttsx3 backends write AIFF; render without the .mp3
            # suffix so backends can't get confused by the extension.
            render_path = Path(tmpdirname) / 'offline_render'
            self._run_offline_engine(text, render_path)

            # Some backends append their own suffix or write elsewhere;
            # find whatever non-empty file they produced.
            written = [
                p for p in Path(tmpdirname).iterdir()
                if p.is_file() and p.stat().st_size > 0
            ]
            if not written:
                raise RuntimeError("Offline TTS produced no audio output")
            render_path = written[0]

            # Convert with ffmpeg directly. pydub's from_file/export are
            # deliberately avoided here: they shell out to ffprobe, a separate
            # binary that many ffmpeg installs don't include, which would
            # needlessly kill the last-resort engine.
            command = [
                'ffmpeg', '-y',
                '-i', str(render_path),
                '-codec:a', 'libmp3lame',
                str(output_path),
            ]
            try:
                subprocess.run(
                    command, check=True, capture_output=True, text=True
                )
            except subprocess.CalledProcessError as exc:
                self.logger.error(
                    f"ffmpeg conversion failed: {exc.stderr.strip()[-500:]}"
                )
                raise RuntimeError(
                    "ffmpeg failed to convert the offline TTS render to MP3"
                ) from exc

    def _run_offline_engine(self, text: str, render_path: Path) -> None:
        """Run one pyttsx3 render pass. Init a fresh engine each time —
        pyttsx3 engines cannot be safely reused across save_to_file calls."""
        engine = pyttsx3.init()
        try:
            engine.setProperty('rate', max(50, int(200 * self.speaking_rate)))  # ~200 wpm default
            engine.save_to_file(text, str(render_path))
            engine.runAndWait()
        finally:
            try:
                engine.stop()
            except Exception:  # pragma: no cover - stop() failure is harmless
                pass

    def _get_audio_duration(self, audio_path: Path, text: str = "") -> float:
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(str(audio_path))
            return len(audio) / 1000.0  # Convert ms to seconds
        except ImportError:
            # pydub is optional; on Python 3.13+ it also needs audioop-lts (see requirements.txt).
            self.logger.warning("pydub unavailable, using estimated duration")
        except Exception as e:
            self.logger.warning(f"Could not determine audio duration: {e}")
        return self._estimate_duration(text)

    def _estimate_duration(self, text: str) -> float:
        """Estimate spoken length at ~150 words per minute, scaled by speaking rate.

        The previous fallback returned a flat 180 seconds for every input.
        """
        words = len(text.split())
        rate = self.speaking_rate if self.speaking_rate and self.speaking_rate > 0 else 1.0
        return round(words / 2.5 / rate, 1)

    def _format_rate(self, speaking_rate: float) -> str:
        """Format speaking rate for Edge-TTS"""
        # Edge-TTS format: "+50%" or "-25%"
        if speaking_rate == 1.0:
            return "+0%"

        # round, not int: 0.9 is -9.999... in floating point and int() made it -9%.
        percentage = round((speaking_rate - 1.0) * 100)
        return f"{percentage:+d}%"

    def _format_pitch(self, pitch: int) -> str:
        """Format pitch for Edge-TTS"""
        # Edge-TTS format: "+10Hz" or "-5Hz"
        if pitch == 0:
            return "+0Hz"
        return f"{pitch:+d}Hz"

    def list_available_voices(self) -> List[Dict[str, Any]]:
        """List all available voices for Edge-TTS"""
        if edge_tts is None:
            self.logger.error("edge-tts not installed")
            return []

        async def get_voices() -> List[Dict[str, Any]]:
            voices = await edge_tts.list_voices()
            return voices

        voices = asyncio.run(get_voices())

        # Filter to English voices
        english_voices = [v for v in voices if v['Locale'].startswith('en-')]

        return english_voices


# Recommended voices for different styles
RECOMMENDED_VOICES = {
    'female_professional': 'en-US-JennyNeural',
    'male_professional': 'en-US-GuyNeural',
    'female_friendly': 'en-US-AriaNeural',
    'male_friendly': 'en-US-ChristopherNeural',
    'british_female': 'en-GB-SoniaNeural',
    'british_male': 'en-GB-RyanNeural',
    'australian_female': 'en-AU-NatashaNeural',
    'australian_male': 'en-AU-WilliamNeural'
}


def main():
    """Standalone execution for testing"""
    config = Config()
    generator = VoiceoverGenerator(config)

    # List available voices
    print("\n=== RECOMMENDED VOICES ===")
    for style, voice_name in RECOMMENDED_VOICES.items():
        print(f"{style:25s} : {voice_name}")

    # Test voiceover generation
    file_manager = FileManager(config)
    video_dir = file_manager.create_video_directory('test_voiceover')

    # Create sample script
    script_data = {
        'full_script': """
[SCENE: Opening]
Have you ever wondered why the sky appears blue? The answer lies in the fascinating physics of light scattering.

[SCENE: Explanation]
Sunlight is made up of all colors of the rainbow. When it enters Earth's atmosphere, it collides with gas molecules. Blue light has a shorter wavelength, so it gets scattered in all directions much more than other colors. This is why we see a blue sky during the day.

[SCENE: Conclusion]
So next time you look up at that beautiful blue sky, remember—you're witnessing the physics of light in action. Don't forget to subscribe for more science content!
""",
        'word_count': 100
    }

    # Generate voiceover
    try:
        voiceover_data = generator.generate_voiceover(script_data, video_dir)
        print(f"\n✓ Voiceover generated: {voiceover_data['audio_file']}")
        print(f"  Duration: {voiceover_data['duration_seconds']:.1f} seconds")
        print(f"  Engine: {voiceover_data['engine']}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == '__main__':
    main()
