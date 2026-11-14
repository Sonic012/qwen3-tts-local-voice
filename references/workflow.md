# Qwen3-TTS workflow notes

## Why direct VoiceDesign

Use `model.generate_voice_design()` directly. Generic `generate_audio(..., instruct=...)` wrappers can route differently across MLX versions and may expose the instruction as spoken content. The dedicated method takes exactly:

- `text`: the line to speak
- `instruct`: the voice description
- `language`: e.g. `Chinese`

## Prompt hygiene

Before synthesis, remove all markup and production notes:

```python
text = re.sub(r"\[[^\]]+\]|<[^>]+>", "", text).strip()
```

Do not put `[resigned]`, `<whisper>`, `[soft tone]`, or Fish Audio Drama tags in Qwen3 text. They are not Qwen3-TTS syntax. Do not mix English words such as `OS`, `pirates`, `prompt`, or `style` into a Chinese voice description; a leaked or misrouted instruction can surface them in the recording.

## Voice consistency

VoiceDesign can vary slightly on every call. For a small audition set that is acceptable. For a long fixed script:

1. Generate one clean reference clip per role with VoiceDesign.
2. Download `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`.
3. Use the Base model's `generate(text=..., ref_audio=..., ref_text=...)` for every line of that role.

This is the recommended production path when dozens of lines must sound like the same actor.

## Hardware

- Apple Silicon (M1/M2/M3/M4) macOS.
- 16 GB RAM is enough for the 1.7B 8-bit VoiceDesign model.
- Model size is about 2.9 GB; leave 6 GB of headroom.
- `ffmpeg` converts the generated WAV to the project's MP3 format.

## Audit

`transcribe_audit.py` uses local MLX Whisper. A clean result contains the intended line only. If it captures an English description, an instruction phrase, or tags, do not batch-generate: fix the text/instruct path first.

## Integration

The application should only map a cue id to a pre-generated file and play it. Do not use browser `speechSynthesis` in a production build, and do not silently fall back to a different TTS voice when a file is missing.
