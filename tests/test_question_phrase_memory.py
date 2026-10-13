from src.core.question_phrase_memory import QuestionPhraseMemory, normalize_learnable_phrase
from src.database.db_manager import DatabaseManager


def test_learned_phrase_persists_across_memory_instances(tmp_path):
    db = DatabaseManager(str(tmp_path / 'phrases.db'))
    first = QuestionPhraseMemory(db)
    assert first.remember('College-la eppo start aachu?', 'established')

    second = QuestionPhraseMemory(db)
    normalized = normalize_learnable_phrase('COLLEGE-la eppo start aachu')
    assert normalized is not None
    assert second.get_fact_id(normalized) == 'established'


def test_personal_contact_details_are_not_learned(tmp_path):
    db = DatabaseManager(str(tmp_path / 'phrases.db'))
    memory = QuestionPhraseMemory(db)
    assert not memory.remember('admission phone +91 98765 43210', 'admissions')
    assert not memory.remember('email me at student@example.com about admission', 'admissions')
