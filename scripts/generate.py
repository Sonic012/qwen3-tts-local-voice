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


def preflight_manifest(manifest):
    if not isinstance(manifest.get("personas"), dict):
        raise SystemExit("manifest error: 'personas' must be an object")
    if not isinstance(manifest.get("lines"), list) or not manifest["lines"]:
        raise SystemExit("manifest error: 'lines' must be a non-empty array")

    for index, line in enumerate(manifest["lines"], start=1):
        for field in ("id", "voice", "text", "file"):
            if not line.get(field):
                raise SystemExit(f"manifest error: line {index} is missing '{field}'")
        if line["voice"] not in manifest["personas"]:
            raise SystemExit(
                f"manifest error: line {index} references unknown voice '{line['voice']}'"
            )
        if not str(line["file"]).endswith((".mp3", ".wav")):
            raise SystemExit(
                f"manifest error: line {index} target must end with .mp3 or .wav"
            )


def resolve_target(line, project_dir):
    target = Path(line["file"])
    if not target.is_absolute():
        target = project_dir / target
    return target


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


def write_audio(results, wav_path):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.concatenate([np.asarray(result.audio) for result in results])
    sf.write(wav_path, audio, int(results[0].sample_rate))


def synthesize(model, *, text, instruct, language, wav_path):
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
    write_audio(results, wav_path)


def synthesize_clone(model, *, text, ref_audio, ref_text, language, wav_path):
    results = list(
        model.generate(
            text=clean_spoken_text(text),
            ref_audio=str(Path(ref_audio).expanduser().resolve()),
            ref_text=ref_text,
            lang_code=language,
            verbose=False,
        )
    )
    if not results:
        raise RuntimeError("model returned no audio")
    write_audio(results, wav_path)


def load_clone_model(clone_model_path, cache={}):
    if "model" not in cache:
        cache["model"] = load_model(clone_model_path)
    return cache["model"]


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
    preflight_manifest(manifest)
    lines = manifest["lines"]
    if args.limit:
        lines = lines[: args.limit]

    project_dir = Path(args.project_dir).expanduser().resolve()
    completed = []
    skipped = []
    failed = []
    for index, line in enumerate(lines, start=1):
        target = resolve_target(line, project_dir)
        if args.skip_existing and target.exists():
            skipped.append(line["id"])
            print(f"skip {index}/{len(lines)}: {line['id']}")
            continue
        try:
            persona = manifest["personas"][line["voice"]]
            temporary = Path(args.output_dir) / "tmp" / f"{line['id']}_000.wav"
            if persona.get("ref_audio") and persona.get("ref_text"):
                clone_model = load_clone_model(args.clone_model)
                synthesize_clone(
                    clone_model,
                    text=line["text"],
                    ref_audio=persona["ref_audio"],
                    ref_text=persona["ref_text"],
                    language=args.lang,
                    wav_path=temporary,
                )
            else:
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


def dry_run(args):
    manifest = load_json(args.manifest)
    preflight_manifest(manifest)
    lines = manifest["lines"]
    if args.limit:
        lines = lines[: args.limit]

    project_dir = Path(args.project_dir).expanduser().resolve()
    planned = []
    would_skip = []
    for line in lines:
        target = resolve_target(line, project_dir)
        if args.skip_existing and target.exists():
            would_skip.append(line["id"])
        else:
            planned.append(target)

    print(f"dry-run: would generate {len(planned)}, would skip {len(would_skip)}")
    for target in planned:
        print(f"  generate -> {target}")
    for line_id in would_skip:
        print(f"  skip -> {line_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate fixed voice assets with local Qwen3-TTS."
    )
    parser.add_argument("mode", choices=["auditions", "batch"])
    parser.add_argument("--model", help="Local MLX VoiceDesign model directory.")
    parser.add_argument(
        "--clone-model", help="Local MLX Base model directory for voice-clone lines."
    )
    parser.add_argument("--designs", help="Design JSON path for auditions.")
    parser.add_argument("--manifest", help="Manifest JSON path for batch mode.")
    parser.add_argument(
        "--project-dir", default=".", help="Project root used to resolve manifest file paths."
    )
    parser.add_argument("--output-dir", default="assets/audio/voice")
    parser.add_argument("--lang", default="Chinese")
    parser.add_argument("--roles", help="Comma-separated role ids for auditions.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print batch targets without loading a model.",
    )
    args = parser.parse_args()

    if args.mode == "auditions":
        if not args.designs:
            parser.error("--designs is required for auditions")
        if args.dry_run:
            parser.error("--dry-run is only supported for batch")
        if not args.model:
            parser.error("--model is required for auditions")
        model = load_model(args.model)
        audition(args, model)
        return

    if not args.manifest:
        parser.error("--manifest is required for batch")
    if args.dry_run:
        dry_run(args)
        return
    if not args.model:
        parser.error("--model is required for batch")

    manifest = load_json(args.manifest)
    preflight_manifest(manifest)
    needs_clone_model = any(
        persona.get("ref_audio") and persona.get("ref_text")
        for persona in manifest["personas"].values()
    )
    if needs_clone_model and not args.clone_model:
        parser.error(
            "--clone-model is required because the manifest contains voice-clone personas"
        )

    model = load_model(args.model)
    batch(args, model)


if __name__ == "__main__":
    main()
