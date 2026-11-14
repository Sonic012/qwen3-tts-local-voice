#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
PYTHON="${PYTHON:-python3}"
VENV="${VENV:-$PROJECT_DIR/.venv-qwen3tts}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python not found: $PYTHON" >&2
  exit 2
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required for MP3 conversion. Install it first (brew install ffmpeg)." >&2
  exit 2
fi

if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install \
  'mlx>=0.32.4' \
  'mlx-audio>=0.6.5' \
  soundfile \
  numpy \
  huggingface_hub \
  transformers \
  safetensors \
  sentencepiece \
  regex \
  tqdm \
  mlx-whisper

echo "Environment ready: $VENV"
echo "Download the model: $VENV/bin/python $(dirname "$0")/download_model.py --dest $PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit"
