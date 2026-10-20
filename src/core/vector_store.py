import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional, Any
from config import config
from .embedding_engine import EmbeddingEngine

# Chroma telemetry is not used by CampusMind and older telemetry packages can
# emit noisy signature errors. Disable it before Chroma is imported.
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'False')
logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.CRITICAL)


class VectorStore:
    MANIFEST = 'manifest.json'

    def __init__(self, persist_directory: Optional[str] = None, embedding_engine: EmbeddingEngine | None = None):
        self.persist_dir = str(Path(persist_directory or config.VECTOR_DB_PATH).resolve())
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self._db = None

    @property
    def manifest_path(self) -> Path:
        return Path(self.persist_dir) / self.MANIFEST

    def _get_db(self):
        if self._db is None:
            if config.VECTOR_BACKEND == 'pgvector':
                from langchain_postgres import PGVector
                self._db = PGVector(embeddings=self.embedding_engine.get_embeddings(),
                    collection_name=config.PGVECTOR_COLLECTION, connection=config.PGVECTOR_URL, use_jsonb=True)
            else:
                from chromadb.config import Settings
                from langchain_community.vectorstores import Chroma
                self._db = Chroma(persist_directory=self.persist_dir,
                    embedding_function=self.embedding_engine.get_embeddings(),
                    client_settings=Settings(
                        anonymized_telemetry=False,
                        is_persistent=True,
                        persist_directory=self.persist_dir,
                    ))
        return self._db

    def _write_manifest(self, document_count: int):
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps({
            'embedding_model': config.EMBEDDING_MODEL,
            'chunk_size': config.CHUNK_SIZE,
            'chunk_overlap': config.CHUNK_OVERLAP,
            'document_count': document_count,
            'vector_backend': config.VECTOR_BACKEND,
        }, indent=2), encoding='utf-8')

    def manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def compatibility(self) -> tuple[bool, str]:
        info = self.manifest()
        if not info:
            return False, 'Vector DB manifest missing; rebuild recommended.'
        if info.get('embedding_model') != config.EMBEDDING_MODEL:
            return False, 'Embedding model changed; rebuild vector_db.'
        if info.get('chunk_size') != config.CHUNK_SIZE or info.get('chunk_overlap') != config.CHUNK_OVERLAP:
            return False, 'Chunk settings changed; rebuild vector_db.'
        if info.get('vector_backend', 'chroma') != config.VECTOR_BACKEND:
            return False, 'Vector backend changed; rebuild vector database.'
        return True, 'compatible'

    def create_from_documents(self, documents: List[Any]):
        if config.VECTOR_BACKEND == 'pgvector':
            db = self._get_db()
            # Keep inserts bounded for large institute corpora.
            batch_size = 2000
            for start in range(0, len(documents), batch_size):
                db.add_documents(documents[start:start + batch_size])
                print(f'Indexed {min(start + batch_size, len(documents))}/{len(documents)} chunks')
            self._write_manifest(len(documents))
            return db

        from chromadb.config import Settings
        from langchain_community.vectorstores import Chroma
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._db = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embedding_engine.get_embeddings(),
            client_settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True,
                persist_directory=self.persist_dir,
            ),
        )
        # Chroma rejects one huge add (for example 8092 > max 5461).
        # 5000 stays under that observed limit while remaining efficient.
        batch_size = 5000
        for start in range(0, len(documents), batch_size):
            batch = documents[start:start + batch_size]
            self._db.add_documents(batch)
            print(f'Indexed {min(start + batch_size, len(documents))}/{len(documents)} chunks')
        if hasattr(self._db, 'persist'):
            self._db.persist()
        self._write_manifest(len(documents))
        return self._db

    def rebuild_from_documents(self, documents: List[Any]):
        if config.VECTOR_BACKEND == 'pgvector':
            db = self._get_db()
            try:
                db.delete_collection()
            except Exception:
                pass
            self._db = None
            return self.create_from_documents(documents)
        if Path(self.persist_dir).exists():
            shutil.rmtree(self.persist_dir)
        self._db = None
        return self.create_from_documents(documents)

    def add_documents(self, documents: List[Any]):
        db = self._get_db()
        db.add_documents(documents)
        if hasattr(db, 'persist'):
            db.persist()
        self._write_manifest(self.get_collection_stats()['document_count'])

    def similarity_search(self, query: str, k: int = None, score_threshold: float | None = None, metadata_filter: dict | None = None):
        k = k or config.TOP_K
        threshold = config.SIMILARITY_THRESHOLD if score_threshold is None else score_threshold
        db = self._get_db()
        kwargs = {'k': k}
        if metadata_filter:
            kwargs['filter'] = metadata_filter
        # Chroma emits the entire retrieved document payload in this warning
        # when its distance conversion falls outside 0..1. Those scores are
        # filtered below; avoid flooding server logs with scraped page text.
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Relevance scores must be between 0 and 1.*', category=UserWarning)
            results = db.similarity_search_with_relevance_scores(query, **kwargs)
        return [(doc, float(score)) for doc, score in results if float(score) >= threshold]

    def all_documents(self, limit: int = 5000):
        db = self._get_db()
        if config.VECTOR_BACKEND == 'pgvector':
            return []
        raw = db._collection.get(limit=limit, include=['documents', 'metadatas'])
        try:
            from langchain.schema import Document
            return [Document(page_content=text, metadata=meta or {}) for text, meta in zip(raw.get('documents', []), raw.get('metadatas', []))]
        except Exception:
            return []

    def get_collection_stats(self):
        db = self._get_db()
        count = db._collection.count() if config.VECTOR_BACKEND == 'chroma' else self.manifest().get('document_count', 0)
        compatible, reason = self.compatibility()
        return {
            'document_count': count,
            'persist_directory': self.persist_dir,
            'compatible': compatible,
            'compatibility_reason': reason,
        }
