from src.monitor.web_ingestion_router import ExtractionResult, SafeAccessPolicy, WebIngestionRouter


def test_access_policy_blocks_explicit_gates():
    assert SafeAccessPolicy.is_blocked(403, '')
    assert SafeAccessPolicy.is_blocked(200, 'Please verify you are human')
    assert not SafeAccessPolicy.is_blocked(200, 'Admissions and department information')


def test_router_stops_on_first_success(monkeypatch):
    router = WebIngestionRouter()
    calls = []

    class A:
        def __init__(self, name, result): self.name, self.result = name, result
        def extract(self, url): calls.append(self.name); return self.result

    router.adapters = [
        A('crawl4ai', ExtractionResult(False, extractor='crawl4ai', reason='thin')),
        A('anakin', ExtractionResult(True, text='x' * 200, extractor='anakin')),
        A('playwright', ExtractionResult(True, text='y' * 200, extractor='playwright')),
    ]
    result = router.extract('https://egspec.org/test')
    assert result.ok and result.extractor == 'anakin'
    assert calls == ['crawl4ai', 'anakin']


def test_router_does_not_continue_after_blocked():
    router = WebIngestionRouter()
    calls = []

    class A:
        def __init__(self, name, result): self.name, self.result = name, result
        def extract(self, url): calls.append(self.name); return self.result

    router.adapters = [
        A('crawl4ai', ExtractionResult(False, extractor='crawl4ai', blocked=True, reason='gate')),
        A('anakin', ExtractionResult(True, text='x' * 200, extractor='anakin')),
    ]
    result = router.extract('https://egspec.org/test')
    assert result.blocked
    assert calls == ['crawl4ai']
