from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


class KnowledgeGraph:
    """Lightweight local KAG index built only from already-ingested institute text.

    This deliberately avoids inventing relations. It stores sentence-level facts and
    searchable entities/categories with source provenance.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.data = {"version": 1, "facts": [], "entities": {}}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and raw.get("version") == 1:
                    self.data = raw
            except Exception:
                pass
        return self

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def _sentences(text: str):
        # Remove contextual prefix from fact extraction.
        text = re.sub(r"^\[[^\n]+\]\s*", "", text or "")
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if 35 <= len(s.strip()) <= 700]

    @staticmethod
    def _tokens(text: str):
        return re.findall(r"[a-z0-9&]+", (text or "").lower())

    @staticmethod
    def _entities(sentence: str):
        # Conservative entity-like phrases; these are labels, not inferred claims.
        found = re.findall(r"\b(?:[A-Z][A-Za-z&.-]*)(?:\s+[A-Z][A-Za-z&.-]*){0,4}\b", sentence)
        return [x.strip() for x in found if len(x.strip()) >= 3][:12]

    def build(self, documents):
        facts = []
        entities = {}
        seen = set()

        for doc in documents:
            meta = getattr(doc, "metadata", {}) or {}
            source = str(meta.get("doc_name") or meta.get("source") or "Unknown")
            url = str(meta.get("source_url") or "")
            category = str(meta.get("category") or "general")
            for sentence in self._sentences(getattr(doc, "page_content", "")):
                key = re.sub(r"\W+", " ", sentence.lower()).strip()
                if key in seen:
                    continue
                seen.add(key)
                fact_id = len(facts)
                ent = self._entities(sentence)
                facts.append({
                    "id": fact_id,
                    "text": sentence,
                    "source": source,
                    "source_url": url,
                    "category": category,
                    "entities": ent,
                })
                for name in ent:
                    entities.setdefault(name.lower(), {"name": name, "fact_ids": []})["fact_ids"].append(fact_id)

        self.data = {"version": 1, "facts": facts, "entities": entities}
        self.save()
        return {"facts": len(facts), "entities": len(entities)}

    def search(self, query: str, k: int = 5):
        q = self._tokens(query)
        if not q:
            return []
        qset = set(q)
        ranked = []
        for fact in self.data.get("facts", []):
            tokens = self._tokens(fact.get("text", ""))
            if not tokens:
                continue
            counts = Counter(tokens)
            overlap = sum(1 + min(counts[t], 2) * 0.25 for t in qset if t in counts)
            category_bonus = 0.4 if fact.get("category") in qset else 0.0
            score = (overlap + category_bonus) / max(len(qset), 1)
            if score > 0:
                ranked.append((score, fact))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [{**fact, "score": float(score)} for score, fact in ranked[:max(1, int(k))]]
