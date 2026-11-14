# Input formats

## Design file

```json
{
  "designs": [
    {
      "role": "lin",
      "title": "同一分钟 · 林澈",
      "description": "27岁东亚男性，守钟人。低沉偏冷的青年男声，咬字克制，气息稳，带一点雨夜里的疲惫和警觉。中文普通话，电影悬疑游戏表演。",
      "tags": ["低沉青年男声", "克制", "警觉"],
      "texts": ["父亲说钟声只准敲十二下。那多出来的一下，是给谁的？"]
    }
  ]
}
```

`description` is the voice-design instruction. Keep it in one language and avoid production abbreviations. `texts[0]` is the audition line and is the only content spoken.

## Fixed voice manifest

```json
{
  "personas": {
    "lin": {
      "instruction": "27岁东亚男性，守钟人。低沉偏冷的青年男声，咬字克制，气息稳。中文普通话，电影悬疑游戏表演。"
    }
  },
  "lines": [
    {
      "id": "intro-os__lin",
      "voice": "lin",
      "scene": "所选角色场景",
      "text": "先看清楚眼前的东西。今晚每个人都会说自己只做了该做的事。",
      "file": "assets/audio/voice/intro-os__lin.mp3"
    }
  ]
}
```

For Qwen3-TTS, `text` must be clean spoken text. Keep prompt markup in a separate field or remove it entirely. `file` is resolved from `--project-dir` in batch mode.

## Recommended naming

```text
assets/audio/voice/
  manifest.json
  voice-designs.json
  auditions/01-lin.mp3
  intro-os__lin.mp3
  beat-0-public-os__lin.mp3
```

Use a stable cue id in the application and resolve it to `<cue>__<role>.mp3` for first-person lines. Keep prologue and NPC-only lines fixed to their own file.
