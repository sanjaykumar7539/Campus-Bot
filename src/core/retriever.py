from typing import List, Tuple, Any
from config import config
from .vector_store import VectorStore
from .hybrid_retriever import HybridRetriever
from .query_processor import QueryProcessor, QueryAnalysis
from .reranker import CrossEncoderReranker
from .source_trust import SourceTrustScorer
from .provenance import enrich_source_record
from .cag_context import ContextCache
from .knowledge_graph import KnowledgeGraph


class Retriever:
    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self.hybrid = HybridRetriever(self.vector_store)
        self.query_processor = QueryProcessor()
        self.reranker = CrossEncoderReranker()
        self.trust = SourceTrustScorer()
        self.cache = ContextCache(
            ttl_seconds=getattr(config, 'CAG_CONTEXT_TTL_SECONDS', 1800),
            max_entries=getattr(config, 'CAG_CONTEXT_MAX_ENTRIES', 500),
        )
        self.kg = KnowledgeGraph(getattr(config, 'KAG_GRAPH_PATH', 'data/knowledge_graph.json'))

    def warmup(self) -> dict:
        document_count = self.hybrid.warmup()
        # Exercise both embedding and reranking paths while the server starts.
        docs, scores = self.retrieve('EGS Pillay Engineering College', k=4)
        if config.ENABLE_RERANKER and docs:
            self.reranker.rerank('EGS Pillay Engineering College', docs, scores, 4)
        return {'documents': document_count, 'models_ready': True}

    def retrieve(self, query: str, k: int = None) -> Tuple[List[Any], List[float]]:
        if config.ENABLE_HYBRID_SEARCH:
            return self.hybrid.retrieve(query, k)
        results = self.vector_store.similarity_search(query, k=k or config.TOP_K)
        return [d for d, _ in results], [s for _, s in results]

    def retrieve_bundle(self, query: str, k: int = None) -> dict:
        analysis = self.query_processor.analyze(query)

        cache_key = f'{analysis.normalized}|k={k or config.TOP_K}'
        if getattr(config, 'ENABLE_CAG', True):
            cached = self.cache.get(cache_key)
            if cached is not None:
                cached['analysis'] = analysis
                cached['retrieval_mode'] = 'cag_cache'
                return cached

        final_k = k or config.TOP_K
        candidate_k = max(config.RERANKER_CANDIDATE_K, final_k) if config.ENABLE_RERANKER else final_k
        docs, scores = self.retrieve(analysis.normalized, candidate_k)

        if config.ENABLE_RERANKER:
            docs, scores = self.reranker.rerank(analysis.normalized, docs, scores, final_k)

        # Provenance-aware tie-breaking. Trust only nudges equally relevant results;
        # it never allows a weak source to become evidence by itself.
        ranked = []
        for doc, score in zip(docs, scores):
            trust = self.trust.score(getattr(doc, 'metadata', {}) or {})
            combined = float(score) * (0.97 + 0.03 * trust)
            ranked.append((doc, combined, float(score), trust))
        ranked.sort(key=lambda x: x[1], reverse=True)

        context_parts, sources, final_scores, evidence = [], [], [], []
        for i, (doc, _, original_score, trust) in enumerate(ranked[:final_k], 1):
            source = doc.metadata.get('doc_name', 'Unknown')
            page = str(doc.metadata.get('page', 'N/A'))
            url = doc.metadata.get('source_url', '')
            category = doc.metadata.get('category', 'general')
            context_parts.append(
                f'[Document {i}] Source: {source} (Page: {page}, Score: {original_score:.3f}, '
                f'Category: {category})' + (f' URL: {url}' if url else '') + f'\n{doc.page_content}'
            )
            sources.append(enrich_source_record(doc, original_score, trust))
            final_scores.append(original_score)
            evidence.append({
                'text': doc.page_content,
                'source': str(source),
                'source_url': str(url),
                'page': page,
                'category': str(category),
                'score': float(original_score),
            })

        kag_used = []
        if getattr(config, 'ENABLE_KAG', True):
            kag_used = self.kg.search(analysis.normalized, getattr(config, 'KAG_TOP_K', 5))
            if kag_used:
                parts = []
                for idx, fact in enumerate(kag_used, 1):
                    label = fact.get('source', 'Unknown')
                    url = fact.get('source_url', '')
                    fact_text = str(fact.get('text', ''))
                    parts.append(
                        f'[KAG Fact {idx}] Source: {label}' + (f' URL: {url}' if url else '') +
                        f'\n{fact_text}'
                    )
                    sources.append({
                        'document': label,
                        'page': 'N/A',
                        'relevance_score': float(fact.get('score', 0.0)),
                        'source_url': url,
                        'category': fact.get('category', 'general'),
                        'source_trust': 0.95,
                        'retrieval_layer': 'KAG',
                    })
                    evidence.append({
                        'text': fact_text,
                        'source': str(label),
                        'source_url': str(url),
                        'page': 'N/A',
                        'category': str(fact.get('category', 'general')),
                        'score': float(fact.get('score', 0.0)),
                    })
                context_parts.append('[Knowledge-Augmented Evidence]\n' + '\n\n'.join(parts))

        bundle = {
            'context': '\n\n'.join(context_parts),
            'sources': sources,
            'evidence': evidence,
            'scores': final_scores,
            'analysis': analysis,
            'retrieval_mode': 'compound_rag_kag',
            'cag_cache_hit': False,
            'kag_facts_used': len(kag_used),
        }

        if getattr(config, 'ENABLE_CAG', True) and bundle['context']:
            self.cache.set(cache_key, bundle)

        return bundle

    def retrieve_with_context(self, query: str, k: int = None) -> str:
        return self.retrieve_bundle(query, k)['context']
