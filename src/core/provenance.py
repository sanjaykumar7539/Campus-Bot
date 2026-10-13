from __future__ import annotations


def enrich_source_record(doc, score: float, trust_score: float):
    meta = getattr(doc, "metadata", {}) or {}
    return {
        "document": meta.get("doc_name", "Unknown"),
        "page": str(meta.get("page", "N/A")),
        "relevance_score": float(score),
        "source_url": meta.get("source_url", ""),
        "category": meta.get("category", "general"),
        "source_trust": float(trust_score),
        "chunk_index": meta.get("chunk_index"),
    }
