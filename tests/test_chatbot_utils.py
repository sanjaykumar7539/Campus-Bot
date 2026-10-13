from src.chatbot.session_manager import SessionManager
from src.chatbot.context_window import ContextWindow
from src.chatbot.quick_replies import QuickReplies
from src.chatbot.response_formatter import ResponseFormatter


def test_session_history_is_bounded():
    s = SessionManager(max_history=4)
    for i in range(7): s.add_message('x', 'user', str(i))
    assert len(s.get_messages('x')) == 4

def test_context_window_respects_message_limit():
    c = ContextWindow(max_tokens=100, max_messages=2)
    out = c.build_context([{'role':'user','content':'a'}, {'role':'bot','content':'b'}, {'role':'user','content':'c'}])
    assert out.splitlines() == ['Assistant: b', 'User: c']

def test_quick_reply_intent():
    assert 'Exam Schedule' in QuickReplies().get_replies('exam timetable')

def test_formatter_escapes_html():
    out = ResponseFormatter().to_html('<script>alert(1)</script> **ok**')
    assert '<script>' not in out and '<strong>ok</strong>' in out
