from config import config

def test_hybrid_weights_valid():
    assert abs(config.VECTOR_WEIGHT + config.KEYWORD_WEIGHT - 1.0) < 0.001

def test_chunk_settings_valid():
    assert config.CHUNK_SIZE > config.CHUNK_OVERLAP >= 0

def test_multilingual_embedding_default_active():
    assert 'multilingual' in config.EMBEDDING_MODEL.lower()

def test_monitor_configuration():
    from config import config
    assert isinstance(config.MONITOR_ENABLED, bool)
    assert config.MONITOR_INTERVAL_SECONDS >= 60
    assert config.MONITOR_BASE_URL.startswith(('http://', 'https://'))
    assert isinstance(config.MONITOR_PAGES, list) and len(config.MONITOR_PAGES) > 0
