import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.document_loader import DocumentLoader
from src.core.text_processor import TextProcessor
from src.core.vector_store import VectorStore
from src.core.knowledge_graph import KnowledgeGraph
from config import config


def main():
    print("Starting document ingestion...")
    loader = DocumentLoader()
    processor = TextProcessor()
    store = VectorStore()

    print(f"Loading documents from {config.DATA_DIR}...")
    documents = loader.load_directory(config.DATA_DIR)
    print(f"Loaded {len(documents)} raw documents")
    if not documents:
        print("No documents found. Place files in the data/ folder or run the website sync first.")
        return

    print("Cleaning, contextualizing and chunking documents...")
    chunks = processor.split_documents(documents)
    print(f"Created {len(chunks)} unique chunks")

    print("Creating vector store in safe batches...")
    store.rebuild_from_documents(chunks)
    print(f"Vector store created at {config.VECTOR_DB_PATH}")
    print(f"Documents: {store.get_collection_stats()['document_count']}")

    if getattr(config, 'ENABLE_KAG', True):
        print("Building provenance-preserving KAG fact graph...")
        kg = KnowledgeGraph(getattr(config, 'KAG_GRAPH_PATH', 'data/knowledge_graph.json'))
        stats = kg.build(chunks)
        print(f"KAG graph: {stats['entities']} entities, {stats['facts']} facts")

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
