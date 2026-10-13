# CampusMind Safe Multi-Stage Web Ingestion

CampusMind now keeps the existing lightweight Requests/BeautifulSoup crawler as the first path and adds three optional extraction layers for pages that are too thin or JavaScript-heavy:

1. **Crawl4AI** — primary AI-friendly Markdown extraction.
2. **AnakinScraper OSS adapter** — optional local structured scraper service. Disabled by default and restricted to localhost unless explicitly approved.
3. **Playwright fallback** — renders difficult JavaScript pages in Chromium without stealth/evasion logic.

## Safety behavior

The fallback chain is for rendering reliability, not security circumvention. HTTP 401/403, CAPTCHA/human-verification pages, and explicit login/access-control gates are treated as blocked states and are not bypassed. TLS verification remains enabled. Domain restrictions from CampusMind's network layer remain in place for the normal crawler.

## Install advanced crawlers

```powershell
python scripts\setup_advanced_web_ingestion.py
```

Or:

```powershell
pip install -r requirements-web-ingestion.txt
python -m playwright install chromium
crawl4ai-setup
```

## Optional AnakinScraper OSS

Run your own authorized local Anakin service separately, then set:

```env
ANAKIN_ENABLED=true
ANAKIN_BASE_URL=http://127.0.0.1:8080
```

CampusMind calls `/v1/scrape` in safe mode with browser forcing disabled. If that local service is absent, CampusMind simply continues to Playwright.

## Run

```powershell
python scripts\sync_website_once.py
python scripts\ingest_documents.py
python main.py
```

Stored page text includes an `EXTRACTOR:` provenance line so you can see whether Requests, Crawl4AI, Anakin, or Playwright produced the content.
