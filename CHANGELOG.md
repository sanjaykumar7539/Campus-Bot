# Changelog

## 2.2.0-planned — Roadmap & Future Capabilities
- Added comprehensive product **ROADMAP.md** covering all major planned features.
- Organized into 5 phases: Visibility & Control → Access Control & Trust → Continuous Improvement → Proactive & Connected → Scale & Intelligence.
- Key planned epics include:
  - Admin Dashboard
  - Role-based Knowledge Access
  - Chat Export & Report Generator
  - Continuous Evaluation Dashboard
  - Proactive Notifications
  - Document Change Timeline
  - Feedback → Review Loop
  - Automatic FAQ Generation
  - PWA / Installable App
  - LMS Integration (Moodle / Google Classroom)
  - Multi-campus / Multi-tenant mode
  - Fine-tuned institute SLM
  - Voice wake-word
  - Sentiment & early-warning analytics

- Added safe multi-stage web ingestion: Crawl4AI -> optional local AnakinScraper -> Playwright fallback, with explicit access-control stop conditions.

## 2.1.0 — Visual UI + Indian Multilingual Voice
- Integrated final Ask EGSPEC visual conversation UI.
- Added Indian multilingual voice input and speech output.
- Added English (India), Tamil, Hindi, Telugu, Malayalam and Kannada voice locales.
- Added sidebar voice/language controls while keeping the landing page clean.
- Added assistant answer replay voice control.
- Added `/api/v1/voice/languages` capability endpoint.
- Added voice assistant tests.

# Changelog

## 2.0.0 — Productization
- Separated product identity from institute/tenant configuration.
- Added product metadata and status APIs.
- Added privacy-conscious local analytics with optional admin-key protection.
- Restricted CORS defaults and added production security response headers.
- Added `.env.example` and product deployment guidance.
- Kept one-command startup, multilingual RAG, website monitoring and PDF auto-ingestion.
# Security, escalation, cache and CI update

# Structured visual responses update

- Added SSE `visual` events and response `visuals` metadata.
- Added locally vendored Leaflet 1.9.4 assets and responsive map/source cards.
- Added a trusted location registry; only administrator-verified coordinates can render embedded pins.
- Added a safe OpenStreetMap search fallback when an address has no verified GPS coordinates.
- Added PostGIS SRID 4326 campus storage, GiST indexing, verified registry synchronization,
  nearest-location lookup, and map visuals for both text SSE and real-time voice responses.

- Added thread-safe sliding-window limits for both client IP and session ID on `/api/v1/chat`.
- Added `Retry-After` on HTTP 429 responses.
- Added bounded TTL/LRU caching for grounded standalone FAQ answers only.
- Added `X-CampusMind-Cache: HIT|MISS` response diagnostics.
- Added verified-contact escalation using `ESCALATION_EMAIL` and `ESCALATION_PHONE`.
- Added GitHub Actions test workflow for pushes and pull requests.
- Kept API/core package imports lightweight for isolated testing and startup.
# Advanced RAG, streaming and PostgreSQL/pgvector

- Added BGE cross-encoder reranking with safe offline fallback.
- Added LangGraph plan/answer/verify orchestration with deterministic fallback.
- Added `/api/v1/chat/stream` SSE endpoint and streaming browser client.
- Added offline automated RAG quality evaluation report generation.
- Added optional PostgreSQL relational logging and pgvector vector storage.
- Added pgvector Docker profile and deployment environment template.
# Defense-in-depth security release

- Added JWT authentication, token revocation and role-based authorization.
- Added student/faculty/hostel-manager/admin roles and admin-only user creation.
- Added Argon2 password hashing, login attempt limiting and account lockout.
- Added Fernet encryption for stored chat content and feedback comments.
- Added persistent security audit tables for SQLite and PostgreSQL.
- Added prompt-injection detection before RAG processing.
- Added CSP, HSTS, COOP and expanded secure CORS headers.
- Added one-time secret generation and interactive first-admin creation.
# Real-time streaming voice release

- Added authenticated FastAPI WebSocket voice sessions.
- Added browser 16 kHz PCM16 microphone streaming with Web Speech fallback.
- Added Silero VAD with deterministic RMS fallback.
- Added lazy Faster-Whisper multilingual partial/final transcription.
- Connected final transcripts to the existing secured, grounded RAG pipeline.
- Added streamed answer events and Piper-local/Edge-TTS audio delivery.
- Added audio duration, energy, VAD and session-bound tests.
