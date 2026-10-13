from src.core.slm_model import SLMModel

def test_prompt_contains_context_and_query():
    s = SLMModel()
    p = s.format_prompt('system', 'official fee is 10', 'fee?')
    assert 'official fee is 10' in p and 'fee?' in p
