# Qwen3-TTS Local Voice

A portable agent skill for generating **fixed character voice assets** locally on Apple Silicon with Qwen3-TTS VoiceDesign and MLX. It is designed for games, visual novels, audio dramas, and other projects where every line must be a stable, pre-generated file rather than runtime browser speech.

## What It Covers

- Voice auditions from natural-language character descriptions.
- Batch generation from a fixed voice manifest.
- Optional CustomVoice and Base voice-clone workflows.
- MP3/WAV output with deterministic file names.
- Prompt-leakage checks and local transcription audit.
- Instructions for wiring generated files into a game or app.

## Requirements

- macOS on Apple Silicon (M1/M2/M3/M4).
- Python with a compatible MLX wheel.
- `ffmpeg` for MP3 conversion.
- 16 GB RAM is enough for the 1.7B 8-bit VoiceDesign model; leave about 6 GB of headroom.

## Quick Start

```bash
git clone https://github.com/Sonic012/qwen3-tts-local-voice.git
cd qwen3-tts-local-voice

PROJECT_DIR="$PWD"
bash scripts/setup_env.sh "$PROJECT_DIR"
source "$PROJECT_DIR/.venv-qwen3tts/bin/activate"

python scripts/download_model.py \
  --dest "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit"
```

Generate two character auditions:

```bash
python scripts/generate.py auditions \
  --model "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit" \
  --designs "$PROJECT_DIR/examples/voice-designs.example.json" \
  --output-dir "$PROJECT_DIR/assets/audio/voice" \
  --roles lin,an
```

Auditions are written to `assets/audio/voice/auditions/`. Listen before generating a large batch.

Generate a fixed manifest:

```bash
python scripts/generate.py batch \
  --project-dir "$PROJECT_DIR" \
  --model "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit" \
  --manifest "$PROJECT_DIR/examples/manifest.example.json" \
  --output-dir "$PROJECT_DIR/assets/audio/voice" \
  --skip-existing
```

Validate targets before loading a model:

```bash
python scripts/generate.py batch \
  --project-dir "$PROJECT_DIR" \
  --manifest "$PROJECT_DIR/examples/manifest.example.json" \
  --output-dir "$PROJECT_DIR/assets/audio/voice" \
  --skip-existing \
  --dry-run
```

## Install as an Agent Skill

Copy or symlink this repository into the skills directory used by your agent host. Common locations include `$HOME/.agents/skills` or a host-configured skills path:

```bash
SKILLS_DIR="${SKILLS_DIR:-$HOME/.agents/skills}"
git clone https://github.com/Sonic012/qwen3-tts-local-voice.git "$SKILLS_DIR/qwen3-tts-local-voice"
```

Then invoke it explicitly:

```text
Use $qwen3-tts-local-voice to generate a fixed voice pack for this project. Generate auditions first.
```

## Input Files

- `examples/voice-designs.example.json` — role descriptions and audition lines.
- `examples/manifest.example.json` — fixed dialogue lines and output paths.
- `references/manifest-schema.md` — field reference.
- `references/workflow.md` — model behavior, prompt hygiene, and the optional voice-cloning workflow.

## Important Behavior

VoiceDesign is called through `model.generate_voice_design(text, instruct, language)` directly. Do not call a generic multi-model wrapper with an `instruct` argument: routing differs between MLX versions and has caused voice-design instructions to leak into the generated speech.

Only the `text` field is spoken. Remove tags such as `[sad]`, `<whisper>`, markdown, and production notes before synthesis. Keep each `instruct` description in one language; avoid mixing English abbreviations into an otherwise Chinese instruction.

## Project Layout

```text
.
├── SKILL.md
├── examples/
├── references/
├── scripts/
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

## License

The skill code and scripts in this repository are released under the MIT License. Qwen3-TTS, MLX, MLX Audio, and model weights remain subject to their upstream licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
