from types import SimpleNamespace
from src.core.hybrid_retriever import HybridRetriever

class FakeStore:
    def similarity_search(self, *a, **k): return []
    def all_documents(self): return []

def doc(text): return SimpleNamespace(page_content=text, metadata={})

def test_keyword_score_prefers_exact_term():
    h = HybridRetriever(FakeStore())
    scores = h._keyword_scores('CS101 regulation', [doc('CS101 regulation syllabus'), doc('hostel food menu')])
    assert scores[0] > scores[1]

def test_tokenizer_keeps_ampersand_codes():
    assert 'ai&ds' in HybridRetriever._tokens('AI&DS fees')


def test_cached_corpus_statistics_keep_new_queries_and_new_corpora_correct():
    hybrid = HybridRetriever(FakeStore())
    corpus = [doc('admission eligibility'), doc('library books')]
    assert hybrid._keyword_scores('admission', corpus)[0] == 1.0
    assert hybrid._keyword_scores('library', corpus)[1] == 1.0
    replacement = [doc('library books'), doc('admission eligibility')]
    assert hybrid._keyword_scores('admission', replacement)[1] == 1.0
