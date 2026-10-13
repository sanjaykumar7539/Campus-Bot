# CampusMind Ultimate Advanced Update

This build keeps the safe 3-stage web ingestion pipeline and adds an accuracy-focused
Compound AI knowledge layer.

## Added
- Crawl4AI + optional Anakin + Playwright fallback (existing safe router)
- Contextual Retrieval: adds source/category context before embedding
- Exact/normalized chunk deduplication
- Hybrid dense + BM25-style lexical retrieval
- Cross-encoder reranking with lexical fallback
- KAG: provenance-preserving local fact/entity graph generated from the verified corpus
- CAG: TTL/LRU cache for repeated grounded retrieval contexts
- Source trust/provenance metadata in returned sources
- Agentic RAG retry workflow already present
- LettuceDetect hallucination verification already present
- Safe Chroma batching already present
- Network resilience, TLS verification, proxy/custom-CA support already present
- Offline-first local knowledge answering remains intact

## Recommended run order
1. `python scripts\setup_advanced_web_ingestion.py`
2. `python scripts\sync_website_once.py`
3. `python scripts\ingest_documents.py`
4. `python scripts\diagnose_knowledge.py`
5. `python main.py`

## Important
Accuracy still depends on having complete, current, verified institute documents.
The system does not invent missing college facts and does not bypass access controls.
