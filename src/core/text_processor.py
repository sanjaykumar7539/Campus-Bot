from typing import List, Any
from pathlib import Path
from config import config


class TextProcessor:
    def __init__(self):
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=['\n\n', '\n', '. ', ' ', ''],
        )

    def split_documents(self, documents: List[Any]) -> List[Any]:
        for doc in documents:
            doc.page_content = self.clean_text(doc.page_content)
            from .contextual_enricher import ContextualEnricher
            source_url = ContextualEnricher.source_url_from_text(doc.page_content)
            if source_url:
                doc.metadata['source_url'] = source_url

        chunks = self.splitter.split_documents(documents)
        per_source = {}

        for chunk in chunks:
            source = str(chunk.metadata.get('source', 'unknown'))
            idx = per_source.get(source, 0)
            per_source[source] = idx + 1
            chunk.metadata['chunk_index'] = idx
            chunk.metadata['doc_name'] = Path(source).name
            chunk.metadata['file_type'] = Path(source).suffix.lower().lstrip('.') or 'unknown'

        if getattr(config, 'CONTEXTUAL_RETRIEVAL_ENABLED', True):
            from .contextual_enricher import ContextualEnricher
            enricher = ContextualEnricher()
            chunks = [enricher.enrich(chunk, i) for i, chunk in enumerate(chunks)]

        if getattr(config, 'CHUNK_DEDUP_ENABLED', True):
            from .deduplicator import ChunkDeduplicator
            chunks, removed = ChunkDeduplicator().deduplicate(chunks)
            if removed:
                print(f'Deduplicated {removed} repeated/empty chunks')

        return chunks

    def clean_text(self, text: str) -> str:
        if not text:
            return ''
        text = text.replace('\x00', '')
        lines = [' '.join(line.split()) for line in text.splitlines()]
        lines = [line for line in lines if line]
        return '\n'.join(lines).strip()
