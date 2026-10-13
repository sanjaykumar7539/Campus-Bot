import os

class ProxyManager:
    def __init__(self):
        self.http_proxy = os.getenv("NETWORK_HTTP_PROXY", "").strip()
        self.https_proxy = os.getenv("NETWORK_HTTPS_PROXY", "").strip()

    def requests_proxies(self):
        proxies = {}
        if self.http_proxy:
            proxies["http"] = self.http_proxy
        if self.https_proxy:
            proxies["https"] = self.https_proxy
        return proxies
