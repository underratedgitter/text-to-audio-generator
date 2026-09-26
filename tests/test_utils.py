import logging

import pytest

from utils import Config, FileManager, SafetyChecker, format_duration, resolve_project_path


@pytest.fixture
def config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
output:
  base_directory: output
safety:
  blacklist_keywords:
    - banned
""",
        encoding="utf-8",
    )
    return Config(str(config_file))


def test_config_get_dot_notation(config):
    assert config.get("output.base_directory") == "output"


def test_config_get_missing_key_returns_default(config):
    assert config.get("nonexistent.key", "fallback") == "fallback"
    assert config.get("output.base_directory.too_deep") is None


def test_resolve_project_path_absolute_passthrough(tmp_path):
    absolute = tmp_path / "somewhere"
    assert resolve_project_path(absolute) == absolute


def test_resolve_project_path_relative_is_under_project_root():
    from utils import PROJECT_ROOT

    resolved = resolve_project_path("output")
    assert resolved == PROJECT_ROOT / "output"


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "00:00"),
        (59, "00:59"),
        (60, "01:00"),
        (125, "02:05"),
    ],
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


def test_create_video_directory_rejects_path_traversal(config, tmp_path):
    config.config["output"]["base_directory"] = str(tmp_path / "output")
    file_manager = FileManager(config)

    with pytest.raises(ValueError):
        file_manager.create_video_directory("../escape")

    with pytest.raises(ValueError):
        file_manager.create_video_directory("/absolute/path")


def test_create_video_directory_creates_subdirectories(config, tmp_path):
    config.config["output"]["base_directory"] = str(tmp_path / "output")
    file_manager = FileManager(config)

    video_dir = file_manager.create_video_directory("my-video")

    assert video_dir.exists()
    assert (video_dir / "intermediates").exists()


def test_safety_checker_flags_blacklisted_keywords(config):
    checker = SafetyChecker(config, logging.getLogger("test-safety"))

    is_safe, violations = checker.check_script_safety("this text contains a Banned word")

    assert is_safe is False
    assert violations == ["banned"]


def test_safety_checker_passes_clean_script(config):
    checker = SafetyChecker(config, logging.getLogger("test-safety"))

    is_safe, violations = checker.check_script_safety("this text is perfectly fine")

    assert is_safe is True
    assert violations == []
