import pytest

from utils import Config
from voiceover import VoiceoverGenerator


@pytest.fixture
def generator(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
tts:
  engine: edge-tts
  voice: en-US-JennyNeural
  speaking_rate: 1.0
  pitch: 0
logging:
  level: INFO
  log_file: {tmp_path / 'pipeline.log'}
output:
  base_directory: {tmp_path / 'output'}
""",
        encoding="utf-8",
    )
    return VoiceoverGenerator(Config(str(config_file)))


def test_clean_text_removes_scene_markers(generator):
    text = "[SCENE: Opening]\nHello there.\n\n\n\n[SCENE: End]\nGoodbye."
    cleaned = generator._clean_text_for_tts(text)

    assert "SCENE" not in cleaned
    assert "Hello there." in cleaned
    assert "Goodbye." in cleaned
    assert "\n\n\n" not in cleaned


def test_format_rate_default_is_zero_percent(generator):
    assert generator._format_rate(1.0) == "+0%"


@pytest.mark.parametrize(
    "rate,expected",
    [
        (1.5, "+50%"),
        (0.5, "-50%"),
        (0.9, "-10%"),
        (1.1, "+10%"),
    ],
)
def test_format_rate(generator, rate, expected):
    assert generator._format_rate(rate) == expected


def test_format_pitch_default_is_zero_hz(generator):
    assert generator._format_pitch(0) == "+0Hz"


@pytest.mark.parametrize(
    "pitch,expected",
    [
        (10, "+10Hz"),
        (-5, "-5Hz"),
    ],
)
def test_format_pitch(generator, pitch, expected):
    assert generator._format_pitch(pitch) == expected


def test_estimate_duration_scales_with_word_count(generator):
    ten_words = " ".join(["word"] * 10)
    twenty_words = " ".join(["word"] * 20)

    assert generator._estimate_duration(twenty_words) == pytest.approx(
        2 * generator._estimate_duration(ten_words)
    )


def test_estimate_duration_scales_inversely_with_speaking_rate(generator):
    text = " ".join(["word"] * 10)
    normal = generator._estimate_duration(text)

    generator.speaking_rate = 2.0
    faster = generator._estimate_duration(text)

    assert faster == pytest.approx(normal / 2)


def test_generate_voiceover_rejects_empty_script(generator, tmp_path):
    script_data = {"full_script": "[SCENE: Opening]\n\n"}

    with pytest.raises(ValueError):
        generator.generate_voiceover(script_data, tmp_path)
