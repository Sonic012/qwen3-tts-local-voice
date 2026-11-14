---
name: qwen3-tts-local-voice
description: Generate fixed character voice assets locally with Qwen3-TTS VoiceDesign on Apple Silicon. Use for game or story dialogue, role auditions, batch MP3 generation, and offline voice production without a cloud TTS key.
---

# Qwen3-TTS Local Voice

Use this skill when the requested output is a set of **pre-generated character voice recordings** for a game, visual novel, audio drama, or interactive story. The target environment is macOS on Apple Silicon with MLX.

This skill does not use runtime browser TTS. It produces fixed WAV/MP3 assets that the application selects and plays by cue ID.

## Workflow

1. Create the isolated environment from the repository root:

   ```bash
   PROJECT_DIR="$PWD"
   bash scripts/setup_env.sh "$PROJECT_DIR"
   source "$PROJECT_DIR/.venv-qwen3tts/bin/activate"
   ```

   Use `PYTHON=python3.13` or another Python version with a matching `mlx` wheel if the default Python does not work. `ffmpeg` is required for MP3 conversion.

2. Download the VoiceDesign model:

   ```bash
   python scripts/download_model.py \
     --dest "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit"
   ```

   The default MLX 8-bit VoiceDesign model is about 2.87 GB and needs roughly 6 GB of working memory. It fits a 16 GB M-series Mac; avoid running another large model at the same time.

3. Prepare these two input files:

   - A **design file** with one entry per role: role id, pure-language voice description, and a short audition line.
   - A **manifest file** with one entry per fixed line: id, role, scene, clean spoken text, and output file.

   Read [references/manifest-schema.md](references/manifest-schema.md) when creating or changing them.

4. Generate auditions before batch generation:

   ```bash
   python scripts/generate.py auditions \
     --project-dir "$PROJECT_DIR" \
     --model "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit" \
     --designs "$PROJECT_DIR/examples/voice-designs.example.json" \
     --output-dir "$PROJECT_DIR/assets/audio/voice" \
     --roles lin,an
   ```

   Listen to every role before generating the full set. A voice design description should describe age, gender, timbre, pace, emotion, recording feel, and language.

5. Audit the generated audio:

   ```bash
   python scripts/transcribe_audit.py \
     --audio "$PROJECT_DIR/assets/audio/voice/auditions/01-lin.mp3"
   ```

   This uses local MLX Whisper. The transcript should contain the intended spoken line and no voice-design instruction, English prompt fragment, or markup tag.

6. Batch-generate the fixed assets. Use `--dry-run` first to validate the manifest and print output paths:

   ```bash
   python scripts/generate.py batch \
     --project-dir "$PROJECT_DIR" \
     --manifest "$PROJECT_DIR/examples/manifest.example.json" \
     --output-dir "$PROJECT_DIR/assets/audio/voice" \
     --skip-existing \
     --dry-run

   python scripts/generate.py batch \
     --project-dir "$PROJECT_DIR" \
     --model "$PROJECT_DIR/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit" \
     --manifest "$PROJECT_DIR/examples/manifest.example.json" \
     --output-dir "$PROJECT_DIR/assets/audio/voice" \
     --skip-existing
   ```

7. Rebuild the consuming application and verify that it loads only the fixed MP3 paths. Do not re-enable browser TTS as a fallback in a production build.

## Non-Negotiable Details

- Call `model.generate_voice_design(text=..., instruct=..., language=...)` directly. Do not route VoiceDesign through a generic multi-model `generate_audio(..., instruct=...)` helper: generic routing can differ by MLX version and has produced prompt leakage.
- `text` is the **only** content that should be spoken. Strip `[tags]`, `<tags>`, markdown, and any production notes before synthesis.
- Keep `instruct` in one language and do not include English abbreviations or words such as `OS`, `pirates`, `style`, or `prompt` inside an otherwise Chinese description. Mixed-language instructions can leak into the generated audio.
- Drama 3/Fish Audio tags are not Qwen3-TTS VoiceDesign syntax. Remove `<whisper>`, `[resigned]`, and similar tags before calling Qwen3.
- Use one reference clip per role and the Base voice-clone model if the same voice must remain stable across dozens of lines. A VoiceDesign model re-designs the voice on every call, which can drift.
- Keep generated assets out of source control when the project does not want large binaries. Store the manifest and design specs, and regenerate deterministically.
- Do not clone a real person's voice without documented consent. Prefer fictional voice-design descriptions for characters.
- To use the production voice-clone path, add `ref_audio` and `ref_text` to a persona and pass `--clone-model` pointing to the Base model. The script verifies this requirement before loading a model.

## Files

- `scripts/setup_env.sh` — creates the MLX environment and installs dependencies.
- `scripts/download_model.py` — downloads the MLX VoiceDesign model.
- `scripts/generate.py` — auditions and batch fixed-voice generation.
- `scripts/transcribe_audit.py` — local transcription audit for prompt leakage.
- `references/workflow.md` — model sizing, troubleshooting, and the optional clone-voice stage.
- `references/manifest-schema.md` — design and manifest formats.
