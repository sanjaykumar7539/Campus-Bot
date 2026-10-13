from src.core import question_phrase_memory, rag_chain
from src.core.rag_chain import RAGChain
from src.core.question_phrase_memory import (
    QuestionPhraseMemory,
    normalize_learnable_phrase,
)
from src.database.db_manager import DatabaseManager


class FakeRetriever:
    def __init__(self, evidence):
        self.evidence = evidence

    def retrieve_bundle(self, query, k=None):
        return {
            'context': '\n'.join(item['text'] for item in self.evidence),
            'evidence': self.evidence,
            'sources': [
                {
                    'document': item['source'],
                    'source_url': item['source_url'],
                    'page': item['page'],
                    'relevance_score': item['score'],
                }
                for item in self.evidence
            ],
            'scores': [item['score'] for item in self.evidence],
        }


def test_rag_returns_only_exact_verified_institute_answer():
    result = RAGChain().invoke('What is EGSPEC?')
    assert result['is_grounded']
    assert result['answer'] == 'EGSPEC is E. G. S. Pillay Engineering College.'
    assert result['sources'][0]['document'] == 'https://egspec.org/about/history'


def test_rag_rejects_questions_not_in_verified_dataset():
    result = RAGChain().invoke('What is the weather tomorrow?')
    assert not result['is_grounded']
    assert result['sources'] == []


def test_confident_new_phrasing_is_remembered_for_later_queries(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'phrases.db')
    memory = QuestionPhraseMemory(DatabaseManager(db_path))
    monkeypatch.setattr(question_phrase_memory, 'get_question_phrase_memory', lambda: memory)
    monkeypatch.setattr(rag_chain, 'get_question_phrase_memory', lambda: memory)

    first = RAGChain().invoke('College-la eppo start aachu?')

    persisted_memory = QuestionPhraseMemory(DatabaseManager(db_path))
    monkeypatch.setattr(
        question_phrase_memory,
        'get_question_phrase_memory',
        lambda: persisted_memory,
    )
    monkeypatch.setattr(rag_chain, 'get_question_phrase_memory', lambda: persisted_memory)
    second = RAGChain().invoke('College-la eppo start aachu?')
    unknown_question = 'What is the weather tomorrow?'
    unknown = RAGChain().invoke(unknown_question)
    unknown_phrase = normalize_learnable_phrase(unknown_question)

    assert first['is_grounded']
    assert first['fact_id'] == 'established'
    assert second['is_grounded']
    assert second['fact_id'] == 'established'
    assert unknown['is_grounded'] is False
    assert unknown_phrase is not None
    assert persisted_memory.get_fact_id(unknown_phrase) is None


def test_rag_builds_structured_answer_from_trusted_group_records():
    evidence = [
        {
            'text': (
                'EGS Pillay College of Pharmacy offers Diploma (D.Pharm), '
                'Undergraduate (B.Pharm), Doctorate (Pharm.D), and '
                'Postgraduate (M.Pharm) programs.'
            ),
            'source': 'admissions.txt',
            'source_url': 'https://admissions.egspgroup.in/admissions',
            'page': '0',
            'category': 'admissions',
            'score': 0.9,
        },
    ]

    result = RAGChain(FakeRetriever(evidence)).invoke(
        'Tell me the Pharmacy college programs and fees'
    )

    assert result['is_grounded']
    assert 'Institutions' in result['answer']
    assert 'Courses & Departments' in result['answer']
    assert 'Admissions & Fees' in result['answer']
    assert 'B.Pharm' in result['answer']
    assert 'could not verify a current fee amount' in result['answer']
    assert 'admissions.egspgroup.in/admissions' not in result['answer']


def test_fee_query_does_not_mistake_admissions_phone_for_fee_amount():
    evidence = [
        {
            'text': (
                'EGS Pillay College of Pharmacy: admissions phone +91 99887 76655. '
                'Programs include B.Pharm and D.Pharm.'
            ),
            'source': 'admissions.txt',
            'source_url': 'https://admissions.egspgroup.in/admissions',
            'page': '0',
            'category': 'admissions',
            'score': 0.9,
        },
    ]

    result = RAGChain(FakeRetriever(evidence)).invoke(
        'What is the fee for the EGS Pillay College of Pharmacy?'
    )

    assert result['is_grounded']
    assert 'could not verify a current fee amount' in result['answer']
    assert '+91 99887 76655' not in result['answer']


def test_rag_does_not_transfer_group_ranking_to_pharmacy():
    evidence = [
        {
            'text': 'EGS Pillay College of Pharmacy offers D.Pharm and B.Pharm programs.',
            'source': 'admissions.txt',
            'source_url': 'https://admissions.egspgroup.in/admissions',
            'page': '0',
            'category': 'admissions',
            'score': 0.9,
        },
        {
            'text': 'The EGS Pillay Group reports an NBA Tier-1 accreditation.',
            'source': 'home.txt',
            'source_url': 'https://admissions.egspgroup.in/',
            'page': '0',
            'category': 'accreditation',
            'score': 0.8,
        },
    ]

    result = RAGChain(FakeRetriever(evidence)).invoke(
        'What is the NBA accreditation of the Pharmacy college?'
    )

    assert result['is_grounded'] is False
    assert result['sources'] == []


def test_ranking_evidence_is_not_categorized_as_course_information():
    sections = RAGChain._sections_for(
        'NBA accreditation and NIRF ranking for Engineering departments.'
    )

    assert sections == ['Rankings & Accreditations']
