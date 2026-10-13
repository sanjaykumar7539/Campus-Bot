from pathlib import Path
from src.core.vector_store import VectorStore
from config import config

class FakeEmbedding: pass

def test_manifest_compatibility(tmp_path):
    v = VectorStore(str(tmp_path), embedding_engine=FakeEmbedding())
    v._write_manifest(10)
    ok, reason = v.compatibility()
    assert ok and reason == 'compatible'
    assert v.manifest()['embedding_model'] == config.EMBEDDING_MODEL

def test_missing_manifest_requests_rebuild(tmp_path):
    v = VectorStore(str(tmp_path), embedding_engine=FakeEmbedding())
    ok, reason = v.compatibility()
    assert not ok and 'rebuild' in reason.lower()
