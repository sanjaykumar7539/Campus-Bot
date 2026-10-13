import re
from typing import Dict, List
from config import config


class Guardrails:
    def __init__(self):
        self.fallback = config.FALLBACK_MESSAGE
        self.hallucination_patterns = [
            r'according to (general knowledge|my training)', r'based on (public|common) knowledge',
            r'typically, universities', r'in general, colleges', r'\bi believe\b', r'\bi think\b',
        ]

    def check_grounding(self, context: str, query: str, scores: List[float] | None = None) -> Dict:
        if not context or not context.strip():
            return {'is_grounded': False, 'score': 0.0, 'reason': 'No relevant institute documents found'}
        if len(context.strip()) < 50:
            return {'is_grounded': False, 'score': 0.0, 'reason': 'Retrieved context insufficient'}
        retrieval_score = max(scores or [0.0])
        active_threshold = config.HYBRID_THRESHOLD if config.ENABLE_HYBRID_SEARCH else config.SIMILARITY_THRESHOLD
        query_words = set(re.findall(r'[a-z0-9&]+', (query or '').lower()))
        context_words = set(re.findall(r'[a-z0-9&]+', context.lower()))
        lexical = len(query_words & context_words) / max(len(query_words), 1)
        score = max(retrieval_score, lexical)
        if config.STRICT_MODE and retrieval_score and retrieval_score < active_threshold:
            return {'is_grounded': False, 'score': score, 'reason': 'Retrieval confidence below threshold'}
        if config.STRICT_MODE and not retrieval_score and lexical < 0.1:
            return {'is_grounded': False, 'score': score, 'reason': 'Query not sufficiently covered'}
        return {'is_grounded': True, 'score': min(1.0, score), 'reason': 'Institute context retrieved'}

    def sanitize_output(self, text: str) -> str:
        if not text or text.startswith('Error generating response:'):
            return self.fallback
        if self.fallback in text and len(text) < len(self.fallback) + 80:
            return self.fallback
        lower = text.lower()
        if any(re.search(p, lower) for p in self.hallucination_patterns):
            return self.fallback
        seen, unique = set(), []
        for line in text.splitlines():
            key = line.strip()
            if key and key not in seen:
                seen.add(key); unique.append(line)
        return '\n'.join(unique).strip()
