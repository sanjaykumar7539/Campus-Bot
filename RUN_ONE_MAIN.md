# One-command run

The frontend and backend are now served by the same FastAPI process.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Then open `http://127.0.0.1:8000` if the browser does not open automatically.

- Frontend: `/`
- Chat API: `/api/v1/chat`
- API docs: `/docs`
- Health check: `/api/v1/health`

## Language

The chat UI supports Auto, English, Tamil and Thanglish reply modes.
The default embedding model is now multilingual. If an older Chroma vector DB was created with the previous English embedding model, delete/rebuild `vector_db` and run document ingestion again before testing multilingual retrieval.
# One-click automatic website sync

Double-click `START_CAMPUSMIND.bat`. It creates the virtual environment when
needed, installs requirements, runs `main.py`, starts the website crawl, cleans
and deduplicates content, rebuilds the RAG index when content changes, and opens
the application.

The first run crawls the complete same-domain website using sitemap discovery
and recursive links. Later checks download only new or changed resources.
Temporary network failures and 404 links are reported without deleting the
working knowledge base.

To check for updates once without starting the application, double-click
`UPDATE_WEBSITE_DATA.bat`.
