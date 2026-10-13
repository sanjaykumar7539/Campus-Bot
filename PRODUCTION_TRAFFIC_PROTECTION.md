# CampusMind Production Traffic Protection

This release adds overload protection for deployment inside the college website.

## Request path

1. Per-IP and per-session sliding-window rate limit.
2. Existing grounded FAQ cache is checked first. Cache hits bypass local LLM inference.
3. Cache misses enter a bounded inference queue.
4. Only `LLM_MAX_CONCURRENT` expensive RAG/SLM jobs may run simultaneously.
5. At most `LLM_MAX_QUEUE` requests may wait. Further requests receive HTTP 503 + `Retry-After` instead of consuming unbounded RAM.
6. Queue wait and inference both have timeouts.
7. `/api/v1/system/traffic` exposes active and queued counts for monitoring.

## Safe starting values for the current CPU/local-model deployment

`LLM_MAX_CONCURRENT=2`, `LLM_MAX_QUEUE=64`, queue timeout 12 seconds. These are protection defaults, not a capacity guarantee. Tune them using load tests on the actual college server.

## Scaling beyond one process/server

The in-process queue/cache/rate limiter protects one CampusMind process. For multiple FastAPI replicas, use a shared Redis-backed cache/rate limiter and a load balancer/reverse proxy. PostgreSQL/pgvector is preferable to local Chroma for multi-replica production. Do not increase Uvicorn workers blindly when every worker loads its own local SLM; that can multiply RAM usage.
