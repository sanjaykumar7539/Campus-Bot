# Advanced RAG Upgrade

This project now includes a CPU-friendly hybrid retrieval layer and a basic evaluation harness.

## Added

- Dense vector search + BM25-style keyword scoring (no new heavy dependency)
- Configurable vector/keyword weights and hybrid threshold
- Conversation context is now actually passed to generation for follow-up questions
- Conversation history is explicitly treated as non-authoritative; institute documents remain the factual source
- Retrieval evaluation script and starter question set
- Per-document retrieval metadata: vector score, keyword score, hybrid score

## Recommended next steps

1. Put official institute PDFs/pages in the ingestion source and rebuild ChromaDB.
2. Fill `evaluation/questions.json` with 100-200 real questions and expected source filenames.
3. Run `python scripts/evaluate_retrieval.py` and tune hybrid weights/threshold.
4. Add structured metadata (`department`, `regulation`, `semester`, `document_date`) during ingestion.
5. Add an optional cross-encoder reranker only after measuring baseline CPU latency.
6. Integrate authenticated student APIs only with institute approval; use synthetic data for demos.

## New environment options

```env
ENABLE_HYBRID_SEARCH=true
VECTOR_WEIGHT=0.70
KEYWORD_WEIGHT=0.30
HYBRID_CANDIDATE_K=12
HYBRID_THRESHOLD=0.45
```
# CampusMind Advanced Production RAG

The active query path is now:

`Query analysis -> Hybrid candidate retrieval -> BGE cross-encoder reranking -> grounding -> local SLM -> agentic verification`

- `ENABLE_RERANKER=true` enables lazy cross-encoder loading. If its model is
  unavailable, a deterministic lexical reranker keeps the application running.
- `ENABLE_LANGGRAPH=true` enables the plan/answer/verify graph. A built-in
  sequential implementation preserves identical safety behavior if LangGraph
  is unavailable.
- `/api/v1/chat/stream` provides SSE progress, answer chunks, sources, and final
  metadata. The browser UI uses this endpoint by default.
- `python scripts/evaluate_rag.py` creates
  `evaluation/rag_evaluation_report.json` with grounded rate, confidence,
  relevance, expected-answer overlap, and source recall.

For PostgreSQL + pgvector, copy values from
`deployment/.env.postgres.example`, use strong matching passwords, then run:

`docker compose --env-file deployment/.env.postgres.example -f deployment/docker-compose.yml --profile postgres up --build`

The default remains SQLite + Chroma, so normal `START_CAMPUSMIND.bat` usage is
unchanged.
