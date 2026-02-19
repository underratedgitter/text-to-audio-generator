"""
Voiceover Generation Module
Generates AI voiceover from script using FREE TTS engines.
Supports: edge-tts (recommended), gTTS (backup)
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

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
        
        if self.engine == 'edge-tts':
            duration = self._generate_edge_tts(clean_text, output_path)
        elif self.engine == 'gtts':
            duration = self._generate_gtts(clean_text, output_path)
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")
        
        # Create voiceover data
        voiceover_data = {
            'audio_file': str(output_path),
            'duration_seconds': duration,
            'engine': self.engine,
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
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Remove scene markers and format text for TTS"""
        import re
        
        # Remove [SCENE: ...] markers
        text = re.sub(r'\[SCENE:[^\]]+\]', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\n+', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _generate_edge_tts(self, text: str, output_path: Path) -> float:
        """
        Generate voiceover using Edge-TTS (FREE, high quality)
        Returns: Duration in seconds
        """
        if edge_tts is None:
            raise ImportError("edge-tts not installed. Install with: pip install edge-tts")
        
        # Run async TTS generation
        asyncio.run(self._async_edge_tts(text, output_path))
        
        # Get audio duration
        duration = self._get_audio_duration(output_path)
        
        return duration
    
    async def _async_edge_tts(self, text: str, output_path: Path):
        """Async method for Edge-TTS"""
        # Adjust voice parameters
        rate = self._format_rate(self.speaking_rate)
        pitch_str = self._format_pitch(self.pitch)
        
        # Generate speech
        communicate = edge_tts.Communicate(text, self.voice, rate=rate, pitch=pitch_str)
        await communicate.save(str(output_path))
    
    def _generate_gtts(self, text: str, output_path: Path) -> float:
        """
        Generate voiceover using gTTS (FREE, basic quality)
        Fallback option if Edge-TTS fails
        Returns: Duration in seconds
        """
        if gTTS is None:
            raise ImportError("gtts not installed. Install with: pip install gtts")
        
        try:
            # Create TTS object
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to file
            tts.save(str(output_path))
            
            # Get duration
            duration = self._get_audio_duration(output_path)
            
            return duration
        
        except Exception as e:
            self.logger.error(f"Error generating gTTS voiceover: {e}")
            raise
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(str(audio_path))
            return len(audio) / 1000.0  # Convert ms to seconds
        except ImportError:
            # Fallback: estimate from script
            self.logger.warning("pydub not installed, using estimated duration")
            # Rough estimate: 150 words per minute
            with open(audio_path, 'rb'):
                # Assume 2.5 words per second average
                return 180.0  # Default estimate
        except Exception as e:
            self.logger.warning(f"Could not determine audio duration: {e}")
            return 180.0  # Default estimate
    
    def _format_rate(self, speaking_rate: float) -> str:
        """Format speaking rate for Edge-TTS"""
        # Edge-TTS format: "+50%" or "-25%"
        if speaking_rate == 1.0:
            return "+0%"
        
        percentage = int((speaking_rate - 1.0) * 100)
        return f"{percentage:+d}%"
    
    def _format_pitch(self, pitch: int) -> str:
        """Format pitch for Edge-TTS"""
        # Edge-TTS format: "+10Hz" or "-5Hz"
        if pitch == 0:
            return "+0Hz"
        return f"{pitch:+d}Hz"
    
    def list_available_voices(self):
        """List all available voices for Edge-TTS"""
        if edge_tts is None:
            self.logger.error("edge-tts not installed")
            return []
        
        async def get_voices():
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
