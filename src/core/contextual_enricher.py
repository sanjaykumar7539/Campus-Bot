from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse


class ContextualEnricher:
    """Adds compact source context before embedding without changing factual content."""

    CATEGORY_HINTS = {
        "admission": "admissions",
        "admissions": "admissions",
        "placement": "placements",
        "placements": "placements",
        "hostel": "hostel",
        "transport": "transport",
        "syllabus": "academics",
        "regulation": "academics",
        "exam": "examinations",
        "department": "departments",
        "faculty": "departments",
        "scholarship": "scholarships",
        "fee": "fees",
        "library": "facilities",
        "laboratory": "facilities",
        "lab": "facilities",
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def category_for(self, source: str, text: str) -> str:
        hay = f"{source} {text[:800]}".lower()
        for key, category in self.CATEGORY_HINTS.items():
            if key in hay:
                return category
        return "general"

    @staticmethod
    def source_url_from_text(text: str) -> str:
        m = re.search(r"(?im)^URL:\s*(https?://\S+)", text or "")
        return m.group(1).rstrip(".,)") if m else ""

    def enrich(self, doc, chunk_index: int = 0):
        source = str((getattr(doc, "metadata", {}) or {}).get("source", "unknown"))
        text = self._normalize(getattr(doc, "page_content", ""))
        url = (getattr(doc, 'metadata', {}) or {}).get('source_url') or self.source_url_from_text(text)
        category = self.category_for(source, text)

        filename = Path(source).name if source else "unknown"
        host = urlparse(url).netloc.lower() if url else ""
        prefix_parts = [
            f"Institute: EGSPEC",
            f"Category: {category}",
            f"Source: {filename}",
        ]
        if host:
            prefix_parts.append(f"Host: {host}")
        prefix = " | ".join(prefix_parts)

        # Context prefix helps embeddings disambiguate short/ambiguous chunks.
        doc.page_content = f"[{prefix}]\n{text}"
        meta = getattr(doc, "metadata", {}) or {}
        meta["category"] = category
        meta["source_url"] = url
        meta["contextualized"] = True
        meta["content_sha256"] = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
        meta["chunk_index"] = int(meta.get("chunk_index", chunk_index))
        doc.metadata = meta
        return doc
