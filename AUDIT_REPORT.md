# Full Project Audit and Upgrade Report

## Critical issues fixed

1. `.env` was overriding the multilingual embedding model with `all-MiniLM-L6-v2`; this caused the language upgrade to be ineffective at runtime.
2. Frontend/backend documentation and PowerShell setup still instructed separate startup. All runtime instructions now use `python main.py`.
3. PowerShell setup contained malformed escaped path characters; rewritten safely.
4. `UnstructuredHTMLLoader` was used without its required dependency. HTML ingestion now uses BeautifulSoup directly.
5. Model/embedding components loaded too early. They are now lazy so the web server can start and health checks stay lightweight.
6. `/health` previously attempted to load the full SLM. It now checks presence only; `/ready` reports setup readiness.
7. SLM generation errors could be returned as grounded answers. Generation errors now fail safely.
8. Grounding confidence used only word overlap. It now incorporates retrieval score.
9. Hybrid retrieval previously calculated lexical scores only on dense candidates. It now can rescue exact lexical matches from the local KB.
10. Vector DB had no record of the embedding/chunk configuration used to build it. A manifest now detects incompatible/legacy DBs.
11. Database message rows referenced sessions that were never created. Chat logging now creates sessions first and enables SQLite foreign keys.
12. Feedback API had no usable bot message ID in chat responses. Chat responses now return `message_id`; feedback validates the bot message exists.
13. Session context had no actual token budget enforcement. ContextWindow now respects message/token bounds.
14. HTML formatter could emit unescaped user/model HTML. It now escapes before applying a tiny safe markdown subset.
15. Website hashes used raw HTML, causing false changes from scripts/navigation. Monitoring now hashes meaningful page text with SHA-256.
16. Re-ingestion paths were relative/hard-coded. Configured absolute project paths are used consistently.
17. CORS used wildcard origins with credentials. Credentials are disabled for the same-origin one-server design.

## Higher-level modules added

- `QueryProcessor`: intent + department/regulation/semester/year hints.
- `VectorStore manifest`: embedding/chunk compatibility detection.
- `Readiness`: cheap startup/setup checks without loading AI models.
- True hybrid retrieval: dense + lexical candidate union.
- Safer DB/feedback lifecycle and returned message IDs.

## Test result

`32 passed` using `pytest -q` in the audit environment.

Heavy external model inference and real Chroma embedding quality still require the project dependencies, model files, vector DB, and institute documents on the target machine. Those are integration/runtime tests, not faked as completed here.
