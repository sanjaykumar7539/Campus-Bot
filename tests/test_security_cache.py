from src.api.rate_limiter import SlidingWindowRateLimiter
from src.core.response_cache import ResponseCache


def test_rate_limiter_blocks_and_recovers():
    limiter = SlidingWindowRateLimiter(2, 10)
    assert limiter.check('ip:session', now=0)[0]
    assert limiter.check('ip:session', now=1)[0]
    allowed, retry = limiter.check('ip:session', now=2)
    assert not allowed and retry > 0
    assert limiter.check('ip:session', now=11)[0]


def test_response_cache_normalizes_copies_and_expires():
    cache = ResponseCache(10, 2)
    key = cache.key('  What   IS the Fee? ', 'EN')
    assert key == 'en:what is the fee?'
    value = {'answer': 'official', 'is_grounded': True}
    cache.set(key, value, now=0)
    received = cache.get(key, now=1)
    received['answer'] = 'mutated'
    assert cache.get(key, now=2)['answer'] == 'official'
    assert cache.get(key, now=10) is None
