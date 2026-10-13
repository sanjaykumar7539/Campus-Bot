from pathlib import Path
from src.core.knowledge_sync import KnowledgeSyncManager


def test_has_source_documents_detects_supported_file(tmp_path, monkeypatch):
    import src.core.knowledge_sync as ks
    monkeypatch.setattr(ks.config, 'DATA_DIR', str(tmp_path))
    (tmp_path / 'notice.pdf').write_bytes(b'%PDF')
    assert KnowledgeSyncManager().has_source_documents() is True


def test_has_source_documents_ignores_unknown_file(tmp_path, monkeypatch):
    import src.core.knowledge_sync as ks
    monkeypatch.setattr(ks.config, 'DATA_DIR', str(tmp_path))
    (tmp_path / 'image.jpg').write_bytes(b'x')
    assert KnowledgeSyncManager().has_source_documents() is False


def test_bootstrap_skips_when_not_needed(monkeypatch):
    manager = KnowledgeSyncManager()
    monkeypatch.setattr(manager, 'needs_bootstrap', lambda: False)
    monkeypatch.setattr(manager, 'rebuild', lambda: (_ for _ in ()).throw(AssertionError('should not rebuild')))
    assert manager.bootstrap_if_needed() is False
