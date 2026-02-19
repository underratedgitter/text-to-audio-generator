"""
Audio-only entry point.
Generate a voiceover MP3 from text input.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import Config, FileManager, Logger
from voiceover import VoiceoverGenerator


class AudioPipeline:
    """Minimal text-to-audio pipeline."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = Config(config_path)
        self.logger = Logger.setup('AudioPipeline', self.config)
        self.file_manager = FileManager(self.config)
        self.voiceover_generator = VoiceoverGenerator(self.config)

    def generate_audio(self, text: str, output_id: str = None) -> dict:
        """Generate audio file from raw text input."""
        if not text or not text.strip():
            raise ValueError("Input text is empty")

        video_dir = self.file_manager.create_video_directory(output_id)
        script_data = {
            'full_script': text.strip(),
            'word_count': len(text.strip().split())
        }

        voiceover_data = self.voiceover_generator.generate_voiceover(script_data, video_dir)

        result = {
            'status': 'success',
            'output_dir': str(video_dir),
            'audio_file': voiceover_data['audio_file'],
            'duration_seconds': voiceover_data['duration_seconds'],
            'engine': voiceover_data['engine'],
            'voice': voiceover_data['voice']
        }

        self.logger.info("Audio generation completed")
        self.logger.info(f"Output: {voiceover_data['audio_file']}")
        return result


def _read_text_from_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()


def main():
    parser = argparse.ArgumentParser(
        description='Generate audio (MP3) from your text input'
    )

    parser.add_argument(
        '--text',
        type=str,
        help='Text to convert into audio'
    )

    parser.add_argument(
        '--text-file',
        type=str,
        help='Path to a text file to convert into audio'
    )

    parser.add_argument(
        '--output-id',
        type=str,
        help='Optional output folder name under output/ (default: timestamp)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )

    args = parser.parse_args()

    if args.text and args.text_file:
        print("Error: Use only one of --text or --text-file")
        sys.exit(1)

    if args.text:
        input_text = args.text
    elif args.text_file:
        try:
            input_text = _read_text_from_file(args.text_file)
        except Exception as exc:
            print(f"Error reading text file: {exc}")
            sys.exit(1)
    else:
        print("Enter text to convert to audio. Press Enter twice to finish:")
        lines = []
        while True:
            line = input()
            if not line.strip() and lines:
                break
            lines.append(line)
        input_text = "\n".join(lines)

    pipeline = AudioPipeline(args.config)

    try:
        result = pipeline.generate_audio(input_text, output_id=args.output_id)
        print("\n✓ Audio generated successfully")
        print(f"  Audio file: {result['audio_file']}")
        print(f"  Duration: {result['duration_seconds']:.1f} seconds")
        print(f"  Output directory: {result['output_dir']}")
        sys.exit(0)
    except Exception as exc:
        print(f"\n✗ Audio generation failed: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    main()
