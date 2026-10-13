# Release Checklist

- [ ] `pytest -q` passes.
- [ ] `.env` contains the correct institute, monitor URL and deployment values.
- [ ] Production uses HTTPS behind a reverse proxy.
- [ ] `AUTO_OPEN_BROWSER=false` in production.
- [ ] `CORS_ORIGINS` contains only trusted origins.
- [ ] `ADMIN_API_KEY` is blank (feature disabled) or a long random secret.
- [ ] Model files are present and licensed for the intended deployment.
- [ ] Knowledge sources are institution-authorized and current.
- [ ] Backup/restore is tested for DB, data and vector index.
- [ ] Privacy policy and institution data-retention policy are approved before real student rollout.
- [ ] Load/latency testing is completed on target hardware.
