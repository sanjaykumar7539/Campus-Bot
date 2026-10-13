from __future__ import annotations

import re
import math
from typing import Any
from config import config


class CrossEncoderReranker:
    """Lazy cross-encoder reranking with a deterministic lexical safety fallback."""
    _models = {}

    def _model(self):
        if config.RERANKER_MODEL not in self._models:
            from sentence_transformers import CrossEncoder
            self._models[config.RERANKER_MODEL] = CrossEncoder(config.RERANKER_MODEL, max_length=512)
        return self._models[config.RERANKER_MODEL]

    @staticmethod
    def _fallback_score(query: str, text: str) -> float:
        q=set(re.findall(r'[a-z0-9&]+',query.lower())); d=set(re.findall(r'[a-z0-9&]+',text.lower()))
        return len(q & d)/max(len(q),1)

    def rerank(self, query: str, docs: list[Any], base_scores: list[float], k: int):
        if not docs: return [], []
        try:
            raw=self._model().predict([[query,d.page_content] for d in docs],show_progress_bar=False)
            scores=[1.0/(1.0+math.exp(-max(-30.0,min(30.0,float(x))))) for x in raw]
        except Exception as exc:
            print(f'Cross-encoder unavailable; lexical rerank fallback used: {exc}')
            scores=[self._fallback_score(query,d.page_content) for d in docs]
        ranked=[]
        for doc,rerank,base in zip(docs,scores,base_scores):
            combined=config.RERANKER_WEIGHT*rerank+(1-config.RERANKER_WEIGHT)*float(base)
            doc.metadata['pre_rerank_score']=round(float(base),4)
            doc.metadata['reranker_score']=round(float(rerank),4)
            ranked.append((doc,combined))
        ranked.sort(key=lambda x:x[1],reverse=True)
        return [d for d,_ in ranked[:k]],[float(s) for _,s in ranked[:k]]
