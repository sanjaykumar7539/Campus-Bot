# Automatic Website + PDF Knowledge Sync

Run only:

```bash
python main.py
```

The same process now:
1. starts the FastAPI backend and frontend,
2. bootstraps the vector database automatically if it is missing/incompatible and local documents exist,
3. starts the website monitor in a background daemon thread,
4. checks configured institute pages immediately and then every `MONITOR_INTERVAL_SECONDS`,
5. discovers PDF links automatically,
6. downloads new PDFs into `data/website_scraped/pdfs/`,
7. compares SHA-256 content hashes to avoid duplicate ingestion,
8. detects changed PDF content and replaces the local copy,
9. snapshots changed web-page text into `data/website_scraped/pages/`,
10. rebuilds the knowledge base only when real content changes are found.

## Safety behavior

- Temporary website/network failure does not delete the existing knowledge base.
- A missing PDF link on one scan does not auto-delete an older valid PDF.
- Unchanged PDFs are not re-injected.
- Changed PDFs trigger knowledge synchronization.
- Invalid/non-PDF responses are ignored.
- Monitor failures are isolated from the chatbot server; the app keeps running.

## Configuration

Edit `.env` if needed:

```env
MONITOR_ENABLED=true
MONITOR_BASE_URL=https://egspec.org/
MONITOR_INTERVAL_SECONDS=3600
MONITOR_PAGES=,about/,admissions/,academics/,departments/,examinations/,placement/,hostel/,fee-structure/,faculty/,news/,events/,contact/
```

`3600` means every hour. The monitor also runs once immediately at startup.
