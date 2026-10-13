# EGSPEC Institutional AI Assistant

Local-first institutional assistant that answers only exact questions in its source-linked, verified college Q&A dataset. Unknown questions receive the admissions contact fallback; chat answers are not generated from general model knowledge.

## Product Roadmap

A full multi-phase product roadmap is available in [`ROADMAP.md`](ROADMAP.md).  
It covers Admin Dashboard, Role-based Knowledge Access, Proactive Notifications, LMS integration, multi-tenant support, and more.

## One command runtime

Run:

```bash
python main.py
```

The same FastAPI process serves both frontend and backend:
- UI: `http://127.0.0.1:8000/`
- Chat API: `/api/v1/chat`
- Health: `/api/v1/health`
- Readiness: `/api/v1/ready`
- API docs: `/docs`

## First setup

```bash
pip install -r requirements.txt
python main.py
```

The reviewed Q&A dataset is in `training/online-college-qa/`. Text chat checks
those answers first, then uses the locally indexed institute websites and
documents when a question needs broader detail. This retrieval path does not
require the local language model or model-weight training. On Windows you can
first run `scripts\setup.ps1`.

## Answer verification

Broader answers are organized into readable sections such as institutions,
courses and departments, rankings and accreditations, and admissions and fees.
Only configured trusted institute domains are used; unsupported claims are not
inferred. If current fees are not present in the indexed records, the assistant
says it could not verify the amount and directs the user to admissions.

Source records remain available for backend verification and chat logs; source
links are not displayed in text or voice responses. Website synchronization and document ingestion update the retrieval index;
they do not, by themselves, fine-tune model weights or turn crawled content
into reviewed Q&A entries. The optional `scripts/prepare_training.py` and
`scripts/train_model.py` workflow exports trusted public-source text and trains
a separate LoRA adapter for continued language modeling. It does not perform
question-answer tuning, and the adapter is not automatically loaded by the
verified chat path. The retrieval index remains the source of live, grounded
answers.

## Tests

```bash
pytest -q
```

The suite covers verified answer matching and fallback behavior, configuration, database/feedback, website monitor, validators, API single-server behavior, and readiness checks.

## Knowledge update

One-time official website sync (updates the scraped knowledge store; review facts before adding them to the verified Q&A dataset):

```bash
python scripts/auto_monitor.py
```

Rebuild the normalized local index and knowledge graph after the crawl:

```bash
python scripts/ingest_documents.py
```

Optional model adaptation (requires the local base model and sufficient
system memory or a supported CUDA GPU):

```bash
python scripts/prepare_training.py
python scripts/train_model.py --device auto
```

This creates a separate adapter; it does not replace the base model or change
the verified chat runtime automatically.

Continuous hourly monitor:

```bash
python scripts/run_scheduler.py
```
# Production protection configuration

Set the following values in `.env` before deployment:

- `CHAT_RATE_LIMIT=20` and `CHAT_RATE_WINDOW_SECONDS=60`
- `RESPONSE_CACHE_TTL_SECONDS=900` and `RESPONSE_CACHE_MAX_ENTRIES=500`
- `ESCALATION_EMAIL` and `ESCALATION_PHONE` using verified official details only

The FAQ cache stores only grounded, standalone answers. Conversational
follow-ups and low-confidence fallbacks are deliberately excluded.

### LettuceDetect grounding verification
Final grounded RAG answers are optionally checked with LettuceDetect before being returned. If unsupported spans are detected above the configured confidence threshold, CampusMind blocks the answer and uses its safe fallback. Disable with `LETTUCEDETECT_ENABLED=false` if the detector model is intentionally unavailable.

## React UI (optional)

A modern React + Vite frontend lives in `frontend-react/`.

```bash
# Terminal 1 — API
python main.py

# Terminal 2 — React dev server
cd frontend-react && npm install && npm run dev
```

Production build (`npm run build`) outputs to `frontend-react/dist/`.  
If that folder exists, `python main.py` serves the React UI automatically.
