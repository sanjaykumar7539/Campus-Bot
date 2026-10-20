import json

from src.monitor.official_sources_monitor import OfficialSourcesMonitor


def test_source_sync_writes_honest_verification_report(tmp_path, monkeypatch):
    report = tmp_path / 'verification.json'
    monitor = OfficialSourcesMonitor(
        sources=['https://egspec.org/', 'https://egspgroup.in/'],
        report_path=report,
    )

    class FakeSite:
        def __init__(self, url):
            self.url = url

        def scan(self):
            if 'egspgroup' in self.url:
                return {
                    'visited_count': 1, 'reachable_pages': 0, 'failed_count': 1,
                    'failures': [{'url': self.url, 'error': 'redirect loop'}],
                }
            return {
                'visited_count': 40, 'reachable_pages': 40, 'failed_count': 0,
                'skipped_malformed_count': 17, 'skipped_known_broken_count': 1,
            }

    monkeypatch.setattr(monitor, '_monitor_for', lambda url: FakeSite(url))
    result = monitor.sync_once(reingest=False)
    saved = json.loads(report.read_text(encoding='utf-8'))
    assert result['verification_report'] == str(report)
    assert saved['sources']['egspec.org']['complete_without_fetch_failures'] is True
    assert saved['sources']['egspec.org']['skipped_malformed_count'] == 17
    assert saved['sources']['egspgroup.in']['complete_without_fetch_failures'] is False
    assert saved['sources']['egspgroup.in']['failure_examples'][0]['error'] == 'redirect loop'
