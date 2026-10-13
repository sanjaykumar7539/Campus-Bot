# CampusMind AI — Productized Institutional Assistant

This build separates **product identity** from **college/tenant identity**, so the same codebase can be deployed for EGSPEC or another institution by changing environment variables rather than editing Python files.

## Product capabilities
- Source-linked, exact-match verified institute Q&A
- Admissions-contact fallback when no verified answer exists
- Official website monitoring and PDF ingestion for reviewed knowledge updates
- One-process startup (`python main.py`)
- Responsive advanced web UI, voice-ready input, feedback and source drawer
- Local operational analytics (no external telemetry)
- Public product/status APIs plus optional admin analytics protected by an admin key
- Production-oriented CORS and response security headers
- Docker deployment files and environment template
- Structured SSE visual events, locally vendored Leaflet campus maps, and source cards

## Verified campus locations

Edit `data/campus_locations.json` to add locations. An embedded map is rendered only when
`verified` is `true` and valid `latitude`/`longitude` values are present. Address-only records
use a safe map-search link, preventing an LLM-generated or unverified GPS pin from being shown.

For PostGIS mode, start the database with `docker compose --profile postgres up -d postgres`
from `deployment`, set `DATABASE_URL` to the PostgreSQL connection string, and start CampusMind.
Verified registry records are upserted with SRID 4326. Location questions query PostGIS first;
the JSON registry remains the outage-safe fallback. `find_nearest` uses PostGIS distance ordering.

## EGSPEC local run
1. `pip install -r requirements.txt`
2. Download/configure the local SLM if not already present.
3. `python main.py`

The server automatically serves the UI and starts website/PDF monitoring. Chat
answers come only from the reviewed `training/online-college-qa/` dataset;
monitoring does not add answers automatically. The language-model adapter is
not used by the strict verified-answer path.

## Rebrand for another institution
Copy `.env.example` to `.env` and change `PRODUCT_NAME`, `INSTITUTE_NAME`, `INSTITUTE_SHORT_NAME`, `MONITOR_BASE_URL`, `MONITOR_PAGES`, support contact and deployment settings. No source-code edits should be required for normal tenant branding/configuration.

## Production checklist
- Use a reverse proxy with HTTPS.
- Set `APP_ENV=production` and `AUTO_OPEN_BROWSER=false`.
- Restrict `CORS_ORIGINS` to the real deployed frontend origin.
- Set a strong `ADMIN_API_KEY` only if admin analytics is needed.
- Back up the SQLite DB and vector/data directories, or migrate persistence to managed infrastructure for multi-instance deployments.
- Run `pytest -q` before release.
- Do not expose model/vector/data directories through the web server.

## API surfaces
- `GET /api/v1/product` — product + tenant metadata
- `GET /api/v1/product/status` — readiness and sync configuration summary
- `GET /api/v1/ready` — lightweight readiness check
- `POST /api/v1/chat` — exact-match verified Q&A assistant with admissions fallback
- `POST /api/v1/feedback` — answer feedback
- `GET /api/v1/admin/analytics` — local usage summary; disabled unless `ADMIN_API_KEY` is configured

## Indian Multilingual Voice Assistant

The product now supports both text and voice conversations.

Supported Indian voice/text languages:
- English (India)
- Tamil
- Hindi
- Telugu
- Malayalam
- Kannada
- Thanglish text support

The microphone is integrated into the Ask EGSPEC composer. Voice/language preferences are kept inside the sidebar to preserve the clean landing page. Assistant replies can be spoken automatically and replayed. The browser selects the best available Indian-locale voice on the device.

Run the complete product with:

```bash
python main.py
```

Then open `http://127.0.0.1:8000`.
