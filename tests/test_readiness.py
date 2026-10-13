from src.core import readiness

def test_readiness_returns_expected_keys():
    state = readiness.check_readiness()
    assert {'model_present','vector_db_present','manifest_present','ready_for_full_chat'} <= set(state)
    assert state['verified_answers_present']
    assert state['ready_for_full_chat']


def test_verified_chat_does_not_require_local_model(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness.config, 'MODEL_PATH', str(tmp_path / 'missing-model'))
    state = readiness.check_readiness()
    assert not state['model_present']
    assert state['ready_for_full_chat']


def test_partial_model_is_not_ready(tmp_path):
    (tmp_path / 'config.json').write_text('{}')
    (tmp_path / 'model.safetensors.index.json').write_text(
        '{"weight_map":{"a":"first.safetensors","b":"second.safetensors"}}'
    )
    (tmp_path / 'first.safetensors').write_bytes(b'weights')
    assert not readiness.model_files_present(tmp_path)
    (tmp_path / 'second.safetensors').write_bytes(b'weights')
    assert readiness.model_files_present(tmp_path)
