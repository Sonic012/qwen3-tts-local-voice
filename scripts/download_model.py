import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


def main():
    parser = argparse.ArgumentParser(description="Download the MLX Qwen3-TTS VoiceDesign model.")
    parser.add_argument(
        "--repo",
        default="mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
        help="Hugging Face repository id.",
    )
    parser.add_argument(
        "--dest",
        default="models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
        help="Destination directory.",
    )
    args = parser.parse_args()
    destination = Path(args.dest).expanduser().resolve()
    snapshot_download(repo_id=args.repo, local_dir=str(destination))
    print(f"downloaded {args.repo} -> {destination}")


if __name__ == "__main__":
    main()
