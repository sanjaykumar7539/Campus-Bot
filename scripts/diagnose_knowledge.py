from pathlib import Path
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from src.core.vector_store import VectorStore
from src.core.knowledge_graph import KnowledgeGraph


def main():
    print("=== CampusMind Knowledge Diagnostic ===")
    print("Data dir:", config.DATA_DIR)
    data_dir = Path(config.DATA_DIR)
    files = [p for p in data_dir.rglob("*") if p.is_file()] if data_dir.exists() else []
    print("Source files:", len(files))

    store = VectorStore()
    try:
        stats = store.get_collection_stats()
        print("Vector chunks:", stats.get("document_count"))
        print("Vector compatible:", stats.get("compatible"))
        print("Vector status:", stats.get("compatibility_reason"))
    except Exception as exc:
        print("Vector DB error:", exc)

    kg = KnowledgeGraph(config.KAG_GRAPH_PATH)
    print("KAG entities:", len(kg.data.get("entities", {})))
    print("KAG facts:", len(kg.data.get("facts", [])))

    print("Contextual retrieval:", config.CONTEXTUAL_RETRIEVAL_ENABLED)
    print("KAG enabled:", config.ENABLE_KAG)
    print("CAG enabled:", config.ENABLE_CAG)
    print("Hybrid retrieval:", config.ENABLE_HYBRID_SEARCH)
    print("Reranker:", config.ENABLE_RERANKER)


if __name__ == "__main__":
    main()
