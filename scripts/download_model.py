from pathlib import Path
import argparse
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from config import config


def download_hf_model(model_name: str, save_path: str):
    """Download a Hugging Face snapshot directly to disk without loading weights.

    This is what src/core/slm_model.py actually loads via
    AutoModelForCausalLM.from_pretrained(save_path), so this stays the default path.
    """
    from huggingface_hub import snapshot_download

    Path(save_path).mkdir(parents=True, exist_ok=True)
    print(f"Downloading {model_name}...")
    print("Saving model and tokenizer files directly to disk (weights are not loaded into RAM)...")
    snapshot_download(repo_id=model_name, local_dir=save_path)
    # The Hub may return a partial local directory when the network is blocked.
    # Check the shards without loading model weights into memory.
    destination = Path(save_path)
    index = destination / 'model.safetensors.index.json'
    if index.exists():
        shards = set(json.loads(index.read_text(encoding='utf-8'))['weight_map'].values())
        missing = [name for name in shards if not (destination / name).is_file()]
        if missing:
            raise RuntimeError(f'Model download incomplete; missing weight files: {missing}')
    elif not any(destination.glob('*.safetensors')) and not any(destination.glob('pytorch_model*.bin')):
        raise RuntimeError('Model download incomplete: no model weight files found.')
    print(f"Model saved to {save_path}")


def download_single_file(url: str, name: str, sha256):
    """Resumable, hash-verified download of one file (e.g. a .gguf) via the
    network-resilience layer. Use this only if you have a separate loader
    (e.g. llama-cpp-python) that actually reads that file -- slm_model.py
    does NOT, so this does not feed the default SLM pipeline.
    """
    from src.network.download_manager import DownloadManager

    dest = Path(config.MODEL_PATH).parent / name
    dm = DownloadManager()
    path = dm.download(url, dest, expected_sha256=sha256, resume=True)
    print(f"Saved: {path}")
    return path


def main():
    p = argparse.ArgumentParser(description="CampusMind model downloader")
    p.add_argument("model", nargs="?", default="microsoft/Phi-3-mini-4k-instruct",
                    help="HF model id to download as tokenizer+weights directory (default: the configured SLM)")
    p.add_argument("save_path", nargs="?", default=config.MODEL_PATH,
                    help="Destination directory for the HF model (default: config.MODEL_PATH)")
    p.add_argument("--url", default=None,
                    help="Alternate mode: download one raw file (e.g. a .gguf) instead of an HF model directory")
    p.add_argument("--name", default=None, help="Output filename for --url mode, e.g. model.gguf")
    p.add_argument("--sha256", default=None, help="Optional expected SHA256 for --url mode")
    args = p.parse_args()

    if args.url:
        if not args.name:
            p.error("--name is required when using --url")
        download_single_file(args.url, args.name, args.sha256)
    else:
        download_hf_model(args.model, args.save_path)


if __name__ == "__main__":
    main()
