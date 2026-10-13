# Product Architecture

```text
Browser / Mobile Web
        |
        v
Advanced Product UI
        |
        v
FastAPI Product Gateway
  |       |        |
  |       |        +--> Product Status / Optional Admin Analytics
  |       +-----------> Feedback + Session Logging
  +-------------------> Multilingual Grounded RAG
                           |
                Query Processing / Hybrid Retrieval
                           |
                    Vector Knowledge Base
                           ^
                           |
             Automatic Knowledge Sync Manager
                           ^
                           |
         Website Monitor + PDF Change/Hash Detection
                           ^
                           |
                   Institution Website
```

## Separation of concerns
- **Product layer:** product name/version/edition, status, analytics, release configuration.
- **Tenant layer:** institute name, website, monitored sections and support identity.
- **AI layer:** language resolution, query analysis, hybrid retrieval, SLM grounding.
- **Knowledge layer:** local documents, website snapshots, PDFs, vector index and compatibility manifest.
- **Operations layer:** one-process startup, health/readiness, logging, Docker and release checklist.
