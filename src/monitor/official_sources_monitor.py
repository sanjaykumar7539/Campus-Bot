from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from config import config
from src.monitor.website_monitor import WebsiteMonitor


class OfficialSourcesMonitor:
    """Crawl all trusted CampusMind institute sources and rebuild the index once.

    Each source receives its own crawl directory and state file, so EGSPEC main,
    COE and admissions data can be synchronized independently without collisions.
    """

    def __init__(self, sources=None, report_path=None):
        self.sources = sources or config.OFFICIAL_SOURCE_ROOTS
        self._stop_event = threading.Event()
        self.report_path = Path(report_path or Path(config.DATA_DIR) / 'website_scraped' / 'source_sync_verification.json')

    @staticmethod
    def _source_key(url: str) -> str:
        host = urlparse(url).netloc.lower() or 'source'
        return re.sub(r'[^a-z0-9._-]+', '_', host).strip('._') or 'source'

    def _monitor_for(self, url: str) -> WebsiteMonitor:
        key = self._source_key(url)
        data_dir = Path(config.DATA_DIR) / 'website_scraped' / key
        state_file = Path(config.BASE_DIR) / 'src' / 'monitor' / 'states' / f'{key}.json'
        return WebsiteMonitor(base_url=url, data_dir=data_dir, state_file=state_file)

    def sync_once(self, reingest: bool = True) -> dict:
        results = {}
        changed_any = False

        for source in self.sources:
            source = source.strip()
            if not source:
                continue
            key = self._source_key(source)
            print(f'\n[CampusMind] Syncing official source: {source}')
            try:
                result = self._monitor_for(source).scan()
                results[key] = result
                changed = bool(
                    result.get('changed_pages')
                    or result.get('new_documents')
                    or result.get('changed_documents')
                    or result.get('new_pdfs')
                    or result.get('changed_pdfs')
                )
                changed_any = changed_any or changed
                print(
                    f"[CampusMind] {key}: visited={result.get('visited_count', 0)}, "
                    f"changed_pages={len(result.get('changed_pages', []))}, "
                    f"new_docs={len(result.get('new_documents', []))}, "
                    f"failed={result.get('failed_count', 0)}, "
                    f"skipped_expiring={result.get('skipped_volatile_count', 0)}, "
                    f"skipped_malformed={result.get('skipped_malformed_count', 0)}, "
                    f"skipped_known_broken={result.get('skipped_known_broken_count', 0)}"
                )
                for failure in result.get('failures', [])[:3]:
                    print(f"[CampusMind] failed URL: {failure['url']} — {failure['error'][:180]}")
            except Exception as exc:
                results[key] = {'error': str(exc)}
                print(f'[CampusMind] Source sync failed safely for {source}: {exc}')

        reingested = False
        if reingest and changed_any:
            from src.core.knowledge_sync import KnowledgeSyncManager
            manager = KnowledgeSyncManager()
            if manager.has_source_documents():
                print('\n[CampusMind] Rebuilding combined knowledge index...')
                reingested = manager.rebuild()

        verification = {
            'checked_at_utc': datetime.now(timezone.utc).isoformat(),
            'sources': {
                key: {
                    'source_url': next((url for url in self.sources if self._source_key(url) == key), ''),
                    'visited_count': item.get('visited_count', 0),
                    'reachable_pages': item.get('reachable_pages', 0),
                    'failed_count': item.get('failed_count', 0),
                    'skipped_volatile_count': item.get('skipped_volatile_count', 0),
                    'skipped_malformed_count': item.get('skipped_malformed_count', 0),
                    'skipped_known_broken_count': item.get('skipped_known_broken_count', 0),
                    'crawl_limit_reached': item.get('crawl_limit_reached', False),
                    'failure_examples': item.get('failures', [])[:25],
                    'error': item.get('error', ''),
                    'complete_without_fetch_failures': (
                        not item.get('error') and item.get('failed_count', 0) == 0
                        and item.get('reachable_pages', 0) > 0
                        and not item.get('crawl_limit_reached', False)
                    ),
                }
                for key, item in results.items()
            },
        }
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.report_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.report_path)

        return {
            'sources': results,
            'changed': changed_any,
            'reingested': reingested,
            'verification_report': str(self.report_path),
        }

    def run_forever(self, interval_seconds=None, initial_scan=True):
        interval = max(60, int(interval_seconds or config.MONITOR_INTERVAL_SECONDS))
        if initial_scan:
            print('Initial multi-source institute sync started.')
            print(f'Official sources: {len(self.sources)}')
            print(f'Multi-source sync result: {self.sync_once(reingest=True)}')

        while not self._stop_event.wait(interval):
            try:
                print(f'Multi-source incremental sync result: {self.sync_once(reingest=True)}')
            except Exception as exc:
                print(f'Multi-source sync failed safely; existing knowledge retained: {exc}')

    def stop(self):
        self._stop_event.set()
