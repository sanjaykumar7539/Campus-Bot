from src.core.guardrails import Guardrails
from config import config

def test_rejects_empty_context():
    r = Guardrails().check_grounding('', 'fees', [])
    assert not r['is_grounded']

def test_accepts_scored_context():
    r = Guardrails().check_grounding('fees ' * 30, 'fees', [0.8])
    assert r['is_grounded']

def test_sanitizes_generation_error():
    assert Guardrails().sanitize_output('Error generating response: boom') == config.FALLBACK_MESSAGE
