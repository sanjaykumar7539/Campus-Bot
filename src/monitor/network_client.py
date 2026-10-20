from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import config


@dataclass
class NetworkStatus:
    mode: str
    consecutive_failures: int = 0
    circuit_open_until: float = 0.0
    last_error: str = ''


class ResilientNetworkClient:
    """Secure, network-resilient HTTP client for trusted institute sources.

    Supports direct internet, an explicitly configured proxy, a custom college CA,
    retry/backoff, connection pooling and a circuit breaker. It intentionally does
    not disable TLS verification or bypass access controls.
    """

    def __init__(self):
        self.status = NetworkStatus(mode=config.NETWORK_MODE)
        self._lock = threading.Lock()
        self.session = requests.Session()
        # A broken origin can redirect to itself forever (observed on the
        # group directory). Fail promptly and keep the error visible.
        self.session.max_redirects = 5

        retry = Retry(
            total=config.NETWORK_MAX_RETRIES,
            connect=config.NETWORK_MAX_RETRIES,
            read=config.NETWORK_MAX_RETRIES,
            status=config.NETWORK_MAX_RETRIES,
            backoff_factor=config.NETWORK_BACKOFF_FACTOR,
            status_forcelist=(408, 425, 429, 500, 502, 503, 504),
            allowed_methods=frozenset({'GET', 'HEAD'}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=config.NETWORK_POOL_CONNECTIONS,
            pool_maxsize=config.NETWORK_POOL_MAXSIZE,
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.session.headers.update({
            'User-Agent': config.NETWORK_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IN,en;q=0.9',
            'Connection': 'keep-alive',
        })

        proxies = {}
        if config.NETWORK_HTTP_PROXY:
            proxies['http'] = config.NETWORK_HTTP_PROXY
        if config.NETWORK_HTTPS_PROXY:
            proxies['https'] = config.NETWORK_HTTPS_PROXY
        if proxies:
            self.session.proxies.update(proxies)

        self.verify = True
        if config.NETWORK_CA_BUNDLE:
            ca = Path(config.NETWORK_CA_BUNDLE).expanduser()
            if not ca.exists():
                raise FileNotFoundError(f'NETWORK_CA_BUNDLE not found: {ca}')
            self.verify = str(ca)

        if config.NETWORK_BASIC_AUTH_USER:
            self.session.auth = (
                config.NETWORK_BASIC_AUTH_USER,
                config.NETWORK_BASIC_AUTH_PASSWORD,
            )

    @staticmethod
    def _hostname(url: str) -> str:
        return (urlparse(url).hostname or '').lower().strip('.')

    def _allowed(self, url: str) -> bool:
        host = self._hostname(url)
        if not host:
            return False
        for allowed in config.NETWORK_ALLOWED_DOMAINS:
            allowed = allowed.lower().strip().strip('.')
            if host == allowed or host.endswith('.' + allowed):
                return True
        return False

    def _circuit_ready(self):
        with self._lock:
            now = time.time()
            if self.status.circuit_open_until and now < self.status.circuit_open_until:
                wait = int(self.status.circuit_open_until - now)
                raise requests.ConnectionError(
                    f'Network circuit breaker active for another {wait}s after repeated failures'
                )
            if self.status.circuit_open_until and now >= self.status.circuit_open_until:
                self.status.circuit_open_until = 0.0
                self.status.consecutive_failures = 0

    def _success(self):
        with self._lock:
            self.status.consecutive_failures = 0
            self.status.circuit_open_until = 0.0
            self.status.last_error = ''

    def _failure(self, exc: Exception):
        with self._lock:
            self.status.consecutive_failures += 1
            self.status.last_error = str(exc)
            if self.status.consecutive_failures >= config.NETWORK_CIRCUIT_FAILURES:
                self.status.circuit_open_until = time.time() + config.NETWORK_CIRCUIT_RESET_SECONDS

    def get(self, url: str, *, stream: bool = False, allow_redirects: bool = True):
        if not self._allowed(url):
            raise PermissionError(f'Blocked non-allowlisted host: {self._hostname(url)}')

        self._circuit_ready()
        timeout = (config.NETWORK_CONNECT_TIMEOUT, config.NETWORK_READ_TIMEOUT)

        try:
            if config.NETWORK_JITTER_MS > 0:
                time.sleep(random.uniform(0, config.NETWORK_JITTER_MS / 1000.0))

            response = self.session.get(
                url,
                timeout=timeout,
                stream=stream,
                allow_redirects=allow_redirects,
                verify=self.verify,
            )

            # A redirect may leave the trusted source family. Do not follow/use it silently.
            final_url = getattr(response, 'url', url)
            if not self._allowed(final_url):
                response.close()
                raise PermissionError(
                    f'Redirected to non-allowlisted host: {self._hostname(final_url)}'
                )

            if response.status_code in (401, 403):
                raise requests.HTTPError(
                    f'{response.status_code} access denied. Configure authorized credentials/proxy if required.',
                    response=response,
                )
            if response.status_code == 404:
                raise requests.HTTPError(f'404 Not Found: {url}', response=response)

            response.raise_for_status()
            self._success()
            return response
        except Exception as exc:
            self._failure(exc)
            raise

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'mode': self.status.mode,
                'proxy_configured': bool(config.NETWORK_HTTP_PROXY or config.NETWORK_HTTPS_PROXY),
                'custom_ca': bool(config.NETWORK_CA_BUNDLE),
                'consecutive_failures': self.status.consecutive_failures,
                'circuit_open': self.status.circuit_open_until > time.time(),
                'last_error': self.status.last_error,
            }
