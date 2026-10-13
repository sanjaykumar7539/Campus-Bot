from __future__ import annotations

from urllib.parse import urlparse


class SourceTrustScorer:
    """Small deterministic provenance score; it never creates facts."""

    TRUSTED = {
        "coe.egspec.org": 1.00,
        "egspec.org": 0.98,
        "www.egspec.org": 0.98,
        "admissions.egspgroup.in": 0.96,
        "egspgroup.in": 0.94,
    }

    def score(self, metadata: dict) -> float:
        metadata = metadata or {}
        url = str(metadata.get("source_url", "") or "")
        host = urlparse(url).netloc.lower()
        if host in self.TRUSTED:
            return self.TRUSTED[host]
        source = str(metadata.get("source", "")).lower()
        if "website_scraped" in source:
            return 0.92
        if source.endswith((".pdf", ".docx", ".xlsx", ".pptx")):
            return 0.90
        return 0.85
