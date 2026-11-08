import pytest

import shutil
import sys
import types

from utils import Config
import voiceover as voiceover_module
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


def test_generate_voiceover_removes_empty_file_after_failure(generator, tmp_path, monkeypatch):
    output_path = tmp_path / "voiceover.mp3"

    def fail_after_writing_empty_file(text, path):
        # TTS engines create the target file before streaming audio, so a
        # failure mid-stream can leave an empty file behind.
        path.write_bytes(b"")
        raise RuntimeError("TTS service unavailable")

    def fail_also(text, path):
        raise RuntimeError("gTTS unavailable")

    monkeypatch.setattr(generator, "_generate_edge_tts", fail_after_writing_empty_file)
    monkeypatch.setattr(generator, "_generate_gtts", fail_also)
    monkeypatch.setattr(
        generator, "_generate_offline_tts", fail_also
    )

    with pytest.raises(RuntimeError):
        generator.generate_voiceover({"full_script": "Hello world."}, tmp_path)

    assert not output_path.exists()


def test_generate_voiceover_rejects_engine_producing_empty_file(generator, tmp_path, monkeypatch):
    output_path = tmp_path / "voiceover.mp3"

    def produce_empty_file(text, path):
        path.write_bytes(b"")

    def fallback_also_fails(text, path):
        raise RuntimeError("fallback also failed")

    monkeypatch.setattr(generator, "_generate_edge_tts", produce_empty_file)
    monkeypatch.setattr(generator, "_generate_gtts", fallback_also_fails)
    monkeypatch.setattr(generator, "_generate_offline_tts", fallback_also_fails)

    with pytest.raises(RuntimeError):
        generator.generate_voiceover({"full_script": "Hello world."}, tmp_path)

    assert not output_path.exists()


def test_generate_voiceover_falls_back_to_gtts_when_edge_tts_fails(
    generator, tmp_path, monkeypatch
):
    output_path = tmp_path / "voiceover.mp3"

    def failing_edge_tts(text, path):
        path.write_bytes(b"")
        raise RuntimeError("edge-tts 403")

    def working_gtts(text, path):
        path.write_bytes(b"fake mp3 bytes")

    monkeypatch.setattr(generator, "_generate_edge_tts", failing_edge_tts)
    monkeypatch.setattr(generator, "_generate_gtts", working_gtts)

    result = generator.generate_voiceover({"full_script": "Hello world."}, tmp_path)

    assert result["engine"] == "gtts"
    assert output_path.exists()
    assert output_path.read_bytes() == b"fake mp3 bytes"


def test_generate_voiceover_falls_back_offline_when_all_online_engines_fail(
    generator, tmp_path, monkeypatch
):
    output_path = tmp_path / "voiceover.mp3"

    def failing_writer(text, path):
        path.write_bytes(b"")
        raise RuntimeError("engine unreachable")

    def working_offline(text, path):
        path.write_bytes(b"offline mp3 bytes")

    monkeypatch.setattr(generator, "_generate_edge_tts", failing_writer)
    monkeypatch.setattr(generator, "_generate_gtts", failing_writer)
    monkeypatch.setattr(generator, "_generate_offline_tts", working_offline)

    result = generator.generate_voiceover({"full_script": "Hello world."}, tmp_path)

    assert result["engine"] == "offline"
    assert output_path.exists()
    assert output_path.read_bytes() == b"offline mp3 bytes"


def test_generate_voiceover_all_engines_fail_raises_last_error(
    generator, tmp_path, monkeypatch
):
    output_path = tmp_path / "voiceover.mp3"

    def failing_writer(text, path):
        path.write_bytes(b"")
        raise RuntimeError("engine down")

    monkeypatch.setattr(generator, "_generate_edge_tts", failing_writer)
    monkeypatch.setattr(generator, "_generate_gtts", failing_writer)
    monkeypatch.setattr(generator, "_generate_offline_tts", failing_writer)

    with pytest.raises(RuntimeError):
        generator.generate_voiceover({"full_script": "Hello world."}, tmp_path)

    assert not output_path.exists()


def test_generate_offline_tts_renders_and_converts(generator, tmp_path, monkeypatch):
    output_path = tmp_path / "voiceover.mp3"

    class FakePyttsxEngine:
        def setProperty(self, key, value):
            assert key == "rate"

        def runAndWait(self):
            pass

        def stop(self):
            pass

    # Simulate a macOS backend that appends .aiff to the requested name
    def fake_init():
        engine = FakePyttsxEngine()

        def save_to_file(text, path):
            with open(str(path) + ".aiff", "wb") as fh:
                fh.write(b"fake aiff bytes")

        engine.save_to_file = save_to_file
        return engine

    fake_pyttsx3 = types.SimpleNamespace(init=fake_init)

    def fake_run(command, check=None, capture_output=None, text=None):
        # ffmpeg invoked as: ffmpeg -y -i <render> -codec:a libmp3lame <out>
        out_path = command[-1]
        assert out_path.endswith("voiceover.mp3")
        with open(out_path, "wb") as fh:
            fh.write(b"fake mp3 bytes")
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(voiceover_module.subprocess, "run", fake_run)
    monkeypatch.setattr(voiceover_module, "pyttsx3", fake_pyttsx3)
    monkeypatch.setattr(shutil, "which", lambda name: "/fake/ffmpeg" if name == "ffmpeg" else None)

    generator._generate_offline_tts("Hello offline.", output_path)

    assert output_path.read_bytes() == b"fake mp3 bytes"


def test_generate_offline_tts_raises_when_backend_writes_nothing(
    generator, tmp_path, monkeypatch
):
    output_path = tmp_path / "voiceover.mp3"

    class FakePyttsxEngine:
        def setProperty(self, key, value):
            pass

        def save_to_file(self, text, path):
            pass  # write nothing — broken backend

        def runAndWait(self):
            pass

        def stop(self):
            pass

    monkeypatch.setattr(
        voiceover_module, "pyttsx3", types.SimpleNamespace(init=lambda: FakePyttsxEngine())
    )

    with pytest.raises(RuntimeError):
        generator._generate_offline_tts("Hello offline.", output_path)
