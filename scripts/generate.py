#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def clean_spoken_text(text):
    return re.sub(r"\[[^\]]+\]|<[^>]+>", "", text).strip()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_model(path):
    from mlx_audio.tts.utils import load_model as load_mlx_model

    return load_mlx_model(str(Path(path).expanduser().resolve()))


def wav_to_mp3(wav_path, mp3_path):
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path),
        ],
        check=True,
    )


def synthesize(model, *, text, instruct, language, wav_path):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    results = list(
        model.generate_voice_design(
            text=clean_spoken_text(text),
            instruct=instruct,
            language=language,
            verbose=False,
        )
    )
    if not results:
        raise RuntimeError("model returned no audio")
    audio = np.concatenate([np.asarray(result.audio) for result in results])
    sf.write(wav_path, audio, int(results[0].sample_rate))


def audition(args, model):
    designs = load_json(args.designs)["designs"]
    if args.roles:
        selected = set(args.roles.split(","))
        designs = [item for item in designs if item["role"] in selected]
    if not designs:
        raise SystemExit("No matching designs.")

    output_dir = Path(args.output_dir) / "auditions"
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, design in enumerate(designs, start=1):
        role = design["role"]
        prefix = f"{index:02d}-{role}"
        wav = output_dir / "wav" / f"{prefix}_000.wav"
        synthesize(
            model,
            text=design["texts"][0],
            instruct=design["description"],
            language=args.lang,
            wav_path=wav,
        )
        mp3 = output_dir / f"{prefix}.mp3"
        wav_to_mp3(wav, mp3)
        results.append({"role": role, "wav": str(wav), "mp3": str(mp3)})
        print(f"audition {index}/{len(designs)}: {role} -> {mp3}")
    (output_dir / "auditions.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def batch(args, model):
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    lines = manifest["lines"]
    if args.limit:
        lines = lines[: args.limit]

    project_dir = Path(args.project_dir).expanduser().resolve()
    completed = []
    skipped = []
    failed = []
    for index, line in enumerate(lines, start=1):
        target = Path(line["file"])
        if not target.is_absolute():
            target = project_dir / target
        if args.skip_existing and target.exists():
            skipped.append(line["id"])
            print(f"skip {index}/{len(lines)}: {line['id']}")
            continue
        try:
            persona = manifest["personas"][line["voice"]]
            temporary = Path(args.output_dir) / "tmp" / f"{line['id']}_000.wav"
            synthesize(
                model,
                text=line["text"],
                instruct=persona["instruction"],
                language=args.lang,
                wav_path=temporary,
            )
            wav_to_mp3(temporary, target)
            temporary.unlink(missing_ok=True)
            completed.append(line["id"])
            print(f"generated {index}/{len(lines)}: {line['id']} -> {target}")
        except Exception as exc:
            failed.append({"id": line["id"], "error": str(exc)[:500]})
            print(f"failed {index}/{len(lines)}: {line['id']}: {exc}", file=sys.stderr)

    manifest["status"] = "generated" if not failed else "partial"
    manifest["results"] = {
        "generated": completed,
        "skipped": skipped,
        "failed": failed,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"done: generated={len(completed)} skipped={len(skipped)} failed={len(failed)}")
    if failed:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate fixed voice assets with local Qwen3-TTS VoiceDesign.")
    parser.add_argument("mode", choices=["auditions", "batch"])
    parser.add_argument("--model", required=True, help="Local MLX VoiceDesign model directory.")
    parser.add_argument("--designs", help="Design JSON path for auditions.")
    parser.add_argument("--manifest", help="Manifest JSON path for batch mode.")
    parser.add_argument("--project-dir", default=".", help="Project root used to resolve manifest file paths.")
    parser.add_argument("--output-dir", default="assets/audio/voice")
    parser.add_argument("--lang", default="Chinese")
    parser.add_argument("--roles", help="Comma-separated role ids for auditions.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    if args.mode == "auditions" and not args.designs:
        parser.error("--designs is required for auditions")
    if args.mode == "batch" and not args.manifest:
        parser.error("--manifest is required for batch")

    model = load_model(args.model)
    if args.mode == "auditions":
        audition(args, model)
    else:
        batch(args, model)


if __name__ == "__main__":
    main()
