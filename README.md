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

## Audio Samples

These are real outputs generated with the VoiceDesign model on Apple Silicon. Click to listen:

| Voice | Language | Sample |
| --- | --- | --- |
| 低沉青年男声 · 守钟人 | Chinese | [▶ 试听](assets/audio/samples/zh-male-lin.mp3) |
| 轻柔女声 · 继承人 | Chinese | [▶ 试听](assets/audio/samples/zh-female-an.mp3) |
| Deep male narrator | English | [▶ Listen](assets/audio/samples/en-male-doc.mp3) |
| Clear female narrator | English | [▶ Listen](assets/audio/samples/en-female-narrator.mp3) |

### Example Prompts

**中文男声**

```text
用 qwen3-tts-local-voice 生成一条试音：
角色描述：27岁东亚男性，守钟人。低沉偏冷的青年男声，咬字克制，气息稳，带一点雨夜里的疲惫和警觉。中文普通话，电影悬疑游戏表演。
台词：父亲说钟声只准敲十二下。那多出来的一下，是给谁的？
```

**中文女声**

```text
用 qwen3-tts-local-voice 生成一条试音：
角色描述：25岁东亚女性，继承人。轻柔、偏高但不稚嫩的女声，表面礼貌克制，底下有紧绷和不安。不要甜腻，不要过度哭腔。中文普通话。
台词：今晚要宣读的补充页，不是我三个月前看见的那一版。
```

**English male**

```text
Use qwen3-tts-local-voice to generate an audition:
Voice description: A 45-year-old North American male documentary narrator. Deep, warm, and steady, with a calm gravitas and deliberate pacing. Neutral American English, studio-quality recording.
Line: The clock struck twelve. One chime was missing. Nobody in the house dared to say its name.
```

**English female**

```text
Use qwen3-tts-local-voice to generate an audition:
Voice description: A 28-year-old North American female game narrator. Clear, crisp, and slightly cool, with a controlled tension underneath. Not sweet, not overly emotional. Neutral American English, studio-quality recording.
Line: The page they are about to read is not the one I saw three months ago.
```

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
├── LICENSE.txt
└── THIRD_PARTY_NOTICES.md
```

## License

The skill code and scripts in this repository are released under the MIT License. Qwen3-TTS, MLX, MLX Audio, and model weights remain subject to their upstream licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
