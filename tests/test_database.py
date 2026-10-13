from src.database.db_manager import DatabaseManager
from src.database.chat_logs import ChatLogger
from src.database.feedback import FeedbackLogger

def test_chat_logging_creates_session_and_feedback(tmp_path):
    db = DatabaseManager(str(tmp_path / 'test.db'))
    log = ChatLogger(db)
    mid = log.log('s1', 'u1', 'hello', 'answer', [], 0.8)
    assert mid > 0
    assert len(log.get_session_logs('s1')) == 2
    fb = FeedbackLogger(db)
    fb.save(mid, 1, 'good')
    assert fb.get_stats()['positive'] == 1
