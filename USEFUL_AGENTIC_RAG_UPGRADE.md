# CampusMind Useful Agentic RAG Upgrade

This build intentionally adds only the agentic behavior that improves an institutional RAG assistant without adding unnecessary infrastructure.

## Added
- Bounded LangGraph retry loop for weak/ungrounded retrieval.
- Query focusing/rewrite that removes conversational filler while preserving names, IDs, years and numbers.
- Wider retrieval on the single retry, followed by the existing hybrid retrieval + cross-encoder reranking + grounding pipeline.
- Final verification that grounded answers must contain source evidence.
- Explicit retry-exhausted metadata while preserving the existing safe fallback behavior.

## Kept
- Hybrid dense + BM25-style retrieval.
- Cross-encoder reranking.
- Grounding guardrails and source citations.
- Session conversation context.
- PostGIS location intelligence and verified map registry.
- Local SLM, website auto-sync, STT/TTS and existing security controls.

## Deliberately not added
- MCP: no current requirement for a general external tool protocol in the core college Q&A path.
- GraphRAG: current institutional documents do not justify the operational complexity yet.
- Multi-agent system: separate planner/retriever/verifier agents would add latency and CPU cost without enough benefit for this use case.
- Autonomous web browsing: CampusMind remains grounded to approved institute sources.
- Unbounded agent loops: retry is capped at one to control latency and avoid runaway CPU usage.

## Validation
Full project test suite: 70 passed.
