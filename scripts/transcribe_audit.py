#!/usr/bin/env python3
import argparse
from pathlib import Path

import mlx_whisper


def main():
    parser = argparse.ArgumentParser(description="Transcribe generated voice assets for prompt-leak audit.")
    parser.add_argument("--audio", nargs="+", required=True)
    parser.add_argument("--model", default="mlx-community/whisper-tiny")
    parser.add_argument("--language", default="zh")
    args = parser.parse_args()

    for audio in args.audio:
        path = Path(audio)
        result = mlx_whisper.transcribe(
            str(path),
            path_or_hf_repo=args.model,
            language=args.language,
            verbose=False,
        )
        print(f"{path.name}: {result.get('text', '').strip()}")


if __name__ == "__main__":
    main()
