# CampusMind Secure Network-Resilient Mode

CampusMind is **offline-first**: student questions are answered from the local vector/knowledge store. Internet access is used to synchronize trusted institute sources, not for every chat request.

## Supported environments

- Home Wi-Fi / mobile hotspot / normal public internet
- College LAN/Wi-Fi
- Explicitly configured authorized HTTP/HTTPS proxies
- Networks using an institutional/custom CA certificate
- Temporary outages or fully offline operation (existing local knowledge remains available)

## Safety and access model

The sync client keeps TLS verification enabled and does not bypass firewalls, authentication, WAFs, or certificate validation. If a protected source requires access, configure the authorized proxy, CA certificate, or credentials supplied by the institution.

## Main settings

```env
NETWORK_MODE=auto
NETWORK_CONNECT_TIMEOUT=10
NETWORK_READ_TIMEOUT=30
NETWORK_MAX_RETRIES=4
NETWORK_CIRCUIT_FAILURES=5
NETWORK_CIRCUIT_RESET_SECONDS=60
NETWORK_HTTP_PROXY=
NETWORK_HTTPS_PROXY=
NETWORK_CA_BUNDLE=
NETWORK_BASIC_AUTH_USER=
NETWORK_BASIC_AUTH_PASSWORD=
NETWORK_ALLOWED_DOMAINS=egspec.org,coe.egspec.org,egspgroup.in,admissions.egspgroup.in
```

Use `NETWORK_MODE=offline` when the machine must not access the internet. The chatbot continues using the last successfully indexed knowledge base.

## Flow

1. Direct/authorized proxy HTTPS sync of allowlisted sources.
2. Retry with exponential backoff for transient failures.
3. Circuit breaker pauses repeated failing network calls.
4. Previously downloaded source files are preserved.
5. Combined knowledge index is rebuilt only when source content changed.
6. Chat responses use the local RAG/KAG/CAG pipeline even if the network is unavailable.
