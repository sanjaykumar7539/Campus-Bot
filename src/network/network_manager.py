from __future__ import annotations

import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.network.proxy_manager import ProxyManager

class NetworkManager:
    def __init__(self):
        self.mode = os.getenv("NETWORK_MODE", "auto").strip().lower()
        self.connect_timeout = float(os.getenv("NETWORK_CONNECT_TIMEOUT", "15"))
        self.read_timeout = float(os.getenv("NETWORK_READ_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("NETWORK_MAX_RETRIES", "5"))
        self.ca_bundle = os.getenv("NETWORK_CA_BUNDLE", "").strip()
        self.verify_tls = os.getenv("VERIFY_TLS", "true").lower() not in {"0", "false", "no"}

        if not self.verify_tls:
            raise RuntimeError(
                "VERIFY_TLS=false is not supported. Use NETWORK_CA_BUNDLE for trusted custom CAs."
            )

        self.session = requests.Session()

        retry = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            backoff_factor=1.5,
            status_forcelist=(408, 425, 429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        proxies = ProxyManager().requests_proxies()
        if proxies:
            self.session.proxies.update(proxies)

        token = os.getenv("HF_TOKEN", "").strip()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

        self.session.headers.setdefault(
            "User-Agent",
            "CampusMind/1.0 (official-data-sync; educational-project)"
        )

    @property
    def verify(self):
        return self.ca_bundle if self.ca_bundle else True

    def get(self, url: str, **kwargs):
        if self.mode == "offline":
            raise ConnectionError("NETWORK_MODE=offline")
        timeout = kwargs.pop("timeout", (self.connect_timeout, self.read_timeout))
        return self.session.get(
            url,
            timeout=timeout,
            verify=self.verify,
            **kwargs,
        )

    def head(self, url: str, **kwargs):
        if self.mode == "offline":
            raise ConnectionError("NETWORK_MODE=offline")
        timeout = kwargs.pop("timeout", (self.connect_timeout, self.read_timeout))
        return self.session.head(
            url,
            timeout=timeout,
            verify=self.verify,
            allow_redirects=True,
            **kwargs,
        )
