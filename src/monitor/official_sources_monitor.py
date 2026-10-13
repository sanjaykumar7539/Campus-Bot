from __future__ import annotations

import re
import threading
from pathlib import Path
from urllib.parse import urlparse

from config import config
from src.monitor.website_monitor import WebsiteMonitor


class OfficialSourcesMonitor:
    """Crawl all trusted CampusMind institute sources and rebuild the index once.

    Each source receives its own crawl directory and state file, so EGSPEC main,
    COE and admissions data can be synchronized independently without collisions.
    """

    def __init__(self, sources=None):
        self.sources = sources or config.OFFICIAL_SOURCE_ROOTS
        self._stop_event = threading.Event()

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
                    f"failed={result.get('failed_count', 0)}"
                )
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

        return {
            'sources': results,
            'changed': changed_any,
            'reingested': reingested,
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
