from __future__ import annotations

import hashlib
import re


class ChunkDeduplicator:
    """Exact + normalized near-duplicate protection for repeated website content."""

    @staticmethod
    def _canonical(text: str) -> str:
        text = (text or "").lower()
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def deduplicate(self, documents):
        seen = set()
        kept = []
        removed = 0

        for doc in documents:
            canonical = self._canonical(getattr(doc, "page_content", ""))
            if not canonical:
                removed += 1
                continue
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if digest in seen:
                removed += 1
                continue
            seen.add(digest)
            meta = getattr(doc, "metadata", {}) or {}
            meta["dedup_hash"] = digest
            doc.metadata = meta
            kept.append(doc)

        return kept, removed
