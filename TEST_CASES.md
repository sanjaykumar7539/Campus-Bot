# Test Case Coverage

Run all tests with:

```bash
pytest -q
```

## Coverage map

- Configuration: hybrid weights, chunk constraints, multilingual embedding configuration.
- Language: Tamil script, Thanglish, explicit language selection, offline-safe fallback.
- Query Processor: intent, AI&DS department, regulation, semester, year, whitespace normalization.
- Session/Context: bounded history and context message limits.
- Quick Replies: intent-specific suggestions.
- Response Formatting: HTML escaping.
- Guardrails: no-context rejection, retrieval-score grounding, generation-error fallback.
- Hybrid Retrieval: lexical exact-term preference and `AI&DS` token handling.
- Vector Store: manifest compatibility and missing-manifest rebuild warning.
- SLM: prompt structure without loading the model.
- RAG Chain: grounded answer/source flow using fakes.
- Database: session creation, two-message logging, feedback and feedback stats.
- Website Monitor: meaningful-text extraction and hash change state.
- Validators: empty query, script injection, normal query.
- Text Processor: null/whitespace cleanup.
- Readiness: expected readiness fields.
- API: frontend + chat API served from one app, message ID response, lightweight health endpoint.
