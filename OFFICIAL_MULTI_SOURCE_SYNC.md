# CampusMind Official Multi-Source Knowledge Sync

CampusMind no longer depends only on the main EGSPEC website.
A normal sync combines these trusted public institute sources by default:

1. `https://egspec.org/` — main college website, departments, facilities, placements, PDFs, notices and linked documents.
2. `https://coe.egspec.org/` — Controller of Examinations, regulations, syllabus/exam related pages and linked documents.
3. `https://admissions.egspgroup.in/` — official admissions portal and linked admissions information.

## One-time / manual sync

```powershell
python scripts\sync_website_once.py
```

The script crawls all configured official sources, stores them separately under:

```text
data/
└── website_scraped/
    ├── egspec.org/
    ├── coe.egspec.org/
    └── admissions.egspgroup.in/
```

When any source changes, CampusMind rebuilds one combined vector index from all local institute data.

## Initial scrape without automatic re-index

```powershell
python scripts\scrape_egspec.py
python scripts\ingest_documents.py
```

## Automatic mode

When `MONITOR_ENABLED=true`, `python main.py` starts the same multi-source synchronizer in the background. It checks all configured sources at `MONITOR_INTERVAL_SECONDS`.

## Add another trusted official source

In `.env`:

```env
OFFICIAL_SOURCE_ROOTS=https://egspec.org/,https://coe.egspec.org/,https://admissions.egspgroup.in/,https://another-official-domain.example/
```

Only add sources that the college treats as authoritative. Public third-party blogs or unofficial pages should not be mixed into the verified institute knowledge base.

## Chroma large-batch fix

Vector ingestion is batched at 5000 chunks. This prevents the observed Chroma error where 8092 chunks exceeded a maximum batch size of 5461.
