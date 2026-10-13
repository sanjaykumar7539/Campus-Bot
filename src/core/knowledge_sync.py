from __future__ import annotations

from pathlib import Path
from config import config


class KnowledgeSyncManager:
    """Keeps local documents and the vector index synchronized safely."""

    def needs_bootstrap(self) -> bool:
        vector_dir = Path(config.VECTOR_DB_PATH)
        if not vector_dir.exists() or not any(vector_dir.iterdir()):
            return True
        try:
            from src.core.vector_store import VectorStore
            compatible, _ = VectorStore().compatibility()
            return not compatible
        except Exception:
            return True

    def has_source_documents(self) -> bool:
        root = Path(config.DATA_DIR)
        if not root.exists():
            return False
        supported = {'.pdf', '.txt', '.md', '.html', '.htm', '.csv', '.json', '.xml', '.docx', '.xlsx', '.pptx'}
        return any(p.is_file() and p.suffix.lower() in supported for p in root.rglob('*'))

    def rebuild(self) -> bool:
        from src.core.document_loader import DocumentLoader
        from src.core.text_processor import TextProcessor
        from src.core.vector_store import VectorStore

        documents = DocumentLoader().load_directory(config.DATA_DIR)
        if not documents:
            return False
        chunks = TextProcessor().split_documents(documents)
        if not chunks:
            return False
        VectorStore().rebuild_from_documents(chunks)
        print(f'Knowledge bootstrap/sync complete: {len(chunks)} chunks.')
        return True

    def bootstrap_if_needed(self) -> bool:
        if not self.needs_bootstrap():
            return False
        if not self.has_source_documents():
            print('Knowledge bootstrap skipped: no local source documents yet.')
            return False
        return self.rebuild()
