"""Cheap readiness checks for verified chat; does not load models."""
from pathlib import Path
import json
from config import config


def model_files_present(model_dir) -> bool:
    path = Path(model_dir)
    if not (path / 'config.json').is_file():
        return False
    for name in ('model.safetensors.index.json', 'pytorch_model.bin.index.json'):
        index = path / name
        if index.is_file():
            try:
                shards = set(json.loads(index.read_text(encoding='utf-8'))['weight_map'].values())
                return bool(shards) and all((path / shard).is_file() for shard in shards)
            except (OSError, ValueError, KeyError, TypeError):
                return False
    return (path / 'model.safetensors').is_file() or (path / 'pytorch_model.bin').is_file()


def check_readiness() -> dict:
    model_dir = Path(config.MODEL_PATH)
    vector_dir = Path(config.VECTOR_DB_PATH)
    model_present = model_files_present(model_dir)
    vector_present = vector_dir.exists() and any(vector_dir.iterdir()) if vector_dir.exists() else False
    manifest = vector_dir / 'manifest.json'
    try:
        from .verified_college_answers import verified_answers_available
        verified_answers_present = verified_answers_available()
    except (OSError, ValueError):
        verified_answers_present = False
    return {
        'model_present': model_present,
        'vector_db_present': vector_present,
        'manifest_present': manifest.exists(),
        'verified_answers_present': verified_answers_present,
        'ready_for_full_chat': verified_answers_present,
    }
