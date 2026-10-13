from config import config
from src.monitor.network_client import ResilientNetworkClient


def test_trusted_domains_are_allowed():
    client = ResilientNetworkClient()
    assert client._allowed('https://egspec.org/')
    assert client._allowed('https://coe.egspec.org/regulations')
    assert client._allowed('https://admissions.egspgroup.in/')


def test_untrusted_domain_is_blocked():
    client = ResilientNetworkClient()
    assert not client._allowed('https://example.com/')


def test_network_snapshot_has_resilience_fields():
    client = ResilientNetworkClient()
    status = client.snapshot()
    assert 'circuit_open' in status
    assert 'consecutive_failures' in status
    assert 'proxy_configured' in status
