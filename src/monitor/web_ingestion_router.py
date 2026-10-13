from __future__ import annotations

import asyncio
import os
import re
import threading
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import config


BLOCK_MARKERS = (
    'captcha', 'verify you are human', 'access denied', 'forbidden',
    'authentication required', 'login required', 'sign in to continue',
)


@dataclass
class ExtractionResult:
    ok: bool
    text: str = ''
    links: list[str] = field(default_factory=list)
    extractor: str = ''
    reason: str = ''
    blocked: bool = False


class SafeAccessPolicy:
    """Stops the fallback chain at deliberate access controls.

    The advanced crawler is for rendering/extraction reliability only. It does not
    solve CAPTCHAs, evade authentication, rotate identities, or bypass 401/403 gates.
    """

    @staticmethod
    def is_blocked(status_code: int | None = None, body: str = '') -> bool:
        if status_code in {401, 403, 429}:
            return True
        sample = (body or '')[:12000].lower()
        return any(marker in sample for marker in BLOCK_MARKERS)


class Crawl4AIAdapter:
    name = 'crawl4ai'

    def available(self) -> bool:
        if not getattr(config, 'CRAWL4AI_ENABLED', True):
            return False
        try:
            import crawl4ai  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def _run(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        box = {}
        err = {}
        def runner():
            try:
                box['value'] = asyncio.run(coro)
            except Exception as exc:  # pragma: no cover - defensive
                err['value'] = exc
        t = threading.Thread(target=runner, daemon=True)
        t.start(); t.join()
        if 'value' in err:
            raise err['value']
        return box.get('value')

    async def _extract_async(self, url: str):
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    def extract(self, url: str) -> ExtractionResult:
        if not self.available():
            return ExtractionResult(False, extractor=self.name, reason='crawl4ai not installed')
        try:
            result = self._run(self._extract_async(url))
            markdown = getattr(result, 'markdown', '') or ''
            if hasattr(markdown, 'raw_markdown'):
                markdown = markdown.raw_markdown
            markdown = str(markdown or '').strip()
            if SafeAccessPolicy.is_blocked(body=markdown):
                return ExtractionResult(False, extractor=self.name, reason='access-control page detected', blocked=True)

            links = []
            raw_links = getattr(result, 'links', None)
            if isinstance(raw_links, dict):
                for group in raw_links.values():
                    if isinstance(group, list):
                        for item in group:
                            if isinstance(item, dict) and item.get('href'):
                                links.append(item['href'])
                            elif isinstance(item, str):
                                links.append(item)
            if len(markdown) < config.MONITOR_MIN_TEXT_LENGTH:
                return ExtractionResult(False, extractor=self.name, reason='insufficient extracted text')
            return ExtractionResult(True, markdown, links, self.name)
        except Exception as exc:
            return ExtractionResult(False, extractor=self.name, reason=str(exc))


class AnakinAdapter:
    """Optional adapter for a self-hosted AnakinScraper OSS instance.

    Safe mode deliberately requests normal HTTP extraction (`useBrowser=false`).
    No hosted proxy rotation, anti-detect configuration, or access-control evasion is used.
    """

    name = 'anakin'

    def __init__(self):
        self.enabled = bool(getattr(config, 'ANAKIN_ENABLED', False))
        self.base_url = str(getattr(config, 'ANAKIN_BASE_URL', 'http://127.0.0.1:8080')).rstrip('/')
        self.allow_remote = bool(getattr(config, 'ANAKIN_ALLOW_REMOTE', False))

    def _allowed_endpoint(self) -> bool:
        host = (urlparse(self.base_url).hostname or '').lower()
        return self.allow_remote or host in {'127.0.0.1', 'localhost', '::1'}

    def extract(self, url: str) -> ExtractionResult:
        if not self.enabled:
            return ExtractionResult(False, extractor=self.name, reason='Anakin adapter disabled')
        if not self._allowed_endpoint():
            return ExtractionResult(False, extractor=self.name, reason='remote Anakin endpoint not allowed by safe mode')
        try:
            r = requests.post(
                f'{self.base_url}/v1/scrape',
                json={'url': url, 'useBrowser': False, 'generateJson': False, 'timeout': 60},
                timeout=(5, 75),
            )
            if r.status_code in {401, 403}:
                return ExtractionResult(False, extractor=self.name, reason=f'Anakin service denied request ({r.status_code})', blocked=True)
            r.raise_for_status()
            payload = r.json() if 'json' in r.headers.get('content-type', '').lower() else {}
            markdown = str(payload.get('markdown') or payload.get('content') or '').strip()
            if SafeAccessPolicy.is_blocked(body=markdown):
                return ExtractionResult(False, extractor=self.name, reason='access-control page detected', blocked=True)
            if len(markdown) < config.MONITOR_MIN_TEXT_LENGTH:
                return ExtractionResult(False, extractor=self.name, reason='insufficient extracted text')
            return ExtractionResult(True, markdown, [], self.name)
        except Exception as exc:
            return ExtractionResult(False, extractor=self.name, reason=str(exc))


class PlaywrightAdapter:
    name = 'playwright'

    def available(self) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def _run(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        box, err = {}, {}
        def runner():
            try:
                box['value'] = asyncio.run(coro)
            except Exception as exc:  # pragma: no cover
                err['value'] = exc
        t = threading.Thread(target=runner, daemon=True)
        t.start(); t.join()
        if 'value' in err:
            raise err['value']
        return box.get('value')

    async def _extract_async(self, url: str):
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=False)
            page = await context.new_page()

            async def route_handler(route):
                if route.request.resource_type in {'image', 'media', 'font'}:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route('**/*', route_handler)
            response = await page.goto(url, wait_until='domcontentloaded', timeout=int(config.PLAYWRIGHT_TIMEOUT_MS))
            status = response.status if response else None
            if status in {401, 403}:
                await browser.close()
                return status, '', []
            await page.wait_for_timeout(int(config.PLAYWRIGHT_SETTLE_MS))
            text = await page.locator('body').inner_text(timeout=int(config.PLAYWRIGHT_TIMEOUT_MS))
            hrefs = await page.locator('a[href]').evaluate_all("els => els.map(e => e.href)")
            await browser.close()
            return status, text, hrefs

    def extract(self, url: str) -> ExtractionResult:
        if not getattr(config, 'PLAYWRIGHT_FALLBACK_ENABLED', True):
            return ExtractionResult(False, extractor=self.name, reason='Playwright fallback disabled')
        if not self.available():
            return ExtractionResult(False, extractor=self.name, reason='playwright not installed')
        try:
            status, text, links = self._run(self._extract_async(url))
            if SafeAccessPolicy.is_blocked(status, text):
                return ExtractionResult(False, extractor=self.name, reason='access-control page detected', blocked=True)
            clean = '\n'.join(line.strip() for line in str(text).splitlines() if line.strip())
            if len(clean) < config.MONITOR_MIN_TEXT_LENGTH:
                return ExtractionResult(False, extractor=self.name, reason='insufficient rendered text')
            return ExtractionResult(True, clean, list(dict.fromkeys(links)), self.name)
        except Exception as exc:
            return ExtractionResult(False, extractor=self.name, reason=str(exc))


class WebIngestionRouter:
    """Three-stage safe extraction fallback: Crawl4AI → Anakin → Playwright."""

    def __init__(self):
        self.adapters = [Crawl4AIAdapter(), AnakinAdapter(), PlaywrightAdapter()]

    @staticmethod
    def _same_trusted_domain(url: str, base_url: str) -> bool:
        host = (urlparse(url).hostname or '').lower()
        base = (urlparse(base_url).hostname or '').lower()
        return bool(host and base and (host == base or host.endswith('.' + base) or base.endswith('.' + host)))

    def extract(self, url: str) -> ExtractionResult:
        attempts = []
        for adapter in self.adapters:
            result = adapter.extract(url)
            attempts.append(f'{result.extractor}:{result.reason or "ok"}')
            if result.blocked:
                result.reason = result.reason or 'blocked by access policy'
                return result
            if result.ok:
                result.links = [u for u in result.links if self._same_trusted_domain(u, url)]
                return result
        return ExtractionResult(False, extractor='router', reason=' | '.join(attempts))
