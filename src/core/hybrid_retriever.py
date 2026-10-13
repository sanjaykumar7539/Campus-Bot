import math
import re
from collections import Counter
from typing import Dict, List, Tuple, Any
from config import config
from .vector_store import VectorStore


class HybridRetriever:
    """True hybrid retrieval: dense candidates + lexical candidates from the local KB."""
    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self.vector_weight = config.VECTOR_WEIGHT
        self.keyword_weight = config.KEYWORD_WEIGHT
        self.candidate_k = config.HYBRID_CANDIDATE_K

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r'[a-z0-9&]+', (text or '').lower())

    def _keyword_scores(self, query: str, docs: List[Any]) -> Dict[int, float]:
        query_terms = self._tokens(query)
        if not query_terms or not docs:
            return {i: 0.0 for i in range(len(docs))}
        tokenized = [self._tokens(d.page_content) for d in docs]
        avgdl = sum(len(t) for t in tokenized) / max(len(tokenized), 1)
        n = len(docs)
        doc_freq = Counter()
        for tokens in tokenized:
            for term in set(tokens):
                doc_freq[term] += 1
        raw = {}
        k1, b = 1.5, 0.75
        for i, tokens in enumerate(tokenized):
            counts, dl, score = Counter(tokens), max(len(tokens), 1), 0.0
            for term in query_terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = doc_freq.get(term, 0)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1)))
            raw[i] = score
        max_score = max(raw.values(), default=0.0)
        return {i: (s / max_score if max_score else 0.0) for i, s in raw.items()}

    @staticmethod
    def _key(doc: Any) -> tuple:
        m = getattr(doc, 'metadata', {}) or {}
        return (m.get('source'), m.get('page'), m.get('chunk_index'), getattr(doc, 'page_content', '')[:80])

    def retrieve(self, query: str, k: int = None, metadata_filter: dict | None = None) -> Tuple[List[Any], List[float]]:
        k = k or config.TOP_K
        dense = self.vector_store.similarity_search(query, k=max(self.candidate_k, k), score_threshold=0.0, metadata_filter=metadata_filter)
        dense_map = {self._key(doc): max(0.0, min(1.0, score)) for doc, score in dense}
        candidates = {self._key(doc): doc for doc, _ in dense}

        # Lexical pass can rescue exact codes/names missed by dense search.
        try:
            lexical_docs = self.vector_store.all_documents()
            if metadata_filter:
                lexical_docs = [d for d in lexical_docs if all(str(d.metadata.get(a)) == str(b) for a, b in metadata_filter.items())]
            lexical_scores = self._keyword_scores(query, lexical_docs)
            top_lex = sorted(lexical_scores.items(), key=lambda x: x[1], reverse=True)[:self.candidate_k]
            lex_map = {}
            for idx, score in top_lex:
                doc = lexical_docs[idx]
                key = self._key(doc)
                candidates[key] = doc
                lex_map[key] = score
        except Exception:
            lex_map = {}

        ranked = []
        for key, doc in candidates.items():
            vector_score = dense_map.get(key, 0.0)
            keyword_score = lex_map.get(key, 0.0)
            hybrid = self.vector_weight * vector_score + self.keyword_weight * keyword_score
            doc.metadata['vector_score'] = round(vector_score, 4)
            doc.metadata['keyword_score'] = round(keyword_score, 4)
            doc.metadata['hybrid_score'] = round(hybrid, 4)
            ranked.append((doc, hybrid))
        ranked.sort(key=lambda x: x[1], reverse=True)
        ranked = [(d, s) for d, s in ranked if s >= config.HYBRID_THRESHOLD]
        return [d for d, _ in ranked[:k]], [s for _, s in ranked[:k]]
