# CampusMind Universal Network + Model/Data Download

This update adds a common network layer for:
- official EGSPEC/COE/admissions data sync
- resumable model-file downloads
- normal Wi-Fi, mobile hotspot, college LAN
- authorized HTTP/HTTPS proxies
- trusted custom CA certificates
- retries and exponential backoff
- offline reuse of already downloaded/indexed data

## 1) Test the current network
```powershell
python scripts\network_self_test.py
```

## 2) Download a model file
Use an official/direct URL you are authorized to access:
```powershell
python scripts\download_model.py --url "MODEL_FILE_URL" --name "model.gguf"
```

Optional integrity check:
```powershell
python scripts\download_model.py --url "MODEL_FILE_URL" --name "model.gguf" --sha256 "EXPECTED_HASH"
```

Interrupted downloads use `.part` files and resume automatically when the server supports HTTP Range.

## 3) College proxy
Set in `.env`:
```env
NETWORK_HTTP_PROXY=http://proxy.example:8080
NETWORK_HTTPS_PROXY=http://proxy.example:8080
```

## 4) College/private CA
```env
NETWORK_CA_BUNDLE=C:\certs\college-ca.pem
```

## 5) Offline use
```env
NETWORK_MODE=offline
```
CampusMind can then answer from its already indexed local RAG/KAG/CAG knowledge.

Security controls are not bypassed. For a network that requires login, proxy, VPN,
private CA, or access tokens, use the authorized credentials/configuration supplied
by the network or service owner.
