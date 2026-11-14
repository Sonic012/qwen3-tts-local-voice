import importlib.util
import json
from pathlib import Path

import pytest


def load_generate():
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate.py"
    spec = importlib.util.spec_from_file_location("generate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("[sad]hello<whisper>", "hello"),
        ("  spaced  ", "spaced"),
        ("no markup", "no markup"),
    ],
)
def test_clean_spoken_text(raw, expected):
    assert load_generate().clean_spoken_text(raw) == expected


def test_preflight_manifest_rejects_unknown_voice():
    generate = load_generate()
    manifest = {"personas": {"a": {}}, "lines": [{"id": "x", "voice": "b", "text": "t", "file": "a.mp3"}]}
    with pytest.raises(SystemExit):
        generate.preflight_manifest(manifest)


def test_preflight_manifest_accepts_valid_example():
    generate = load_generate()
    manifest_path = Path(__file__).resolve().parents[1] / "examples" / "manifest.example.json"
    generate.preflight_manifest(json.loads(manifest_path.read_text()))


def test_resolve_target_handles_relative_and_absolute(tmp_path):
    generate = load_generate()
    absolute = tmp_path / "fixed.mp3"
    assert generate.resolve_target({"file": str(absolute)}, tmp_path) == absolute
    assert generate.resolve_target({"file": "relative.mp3"}, tmp_path) == tmp_path / "relative.mp3"
