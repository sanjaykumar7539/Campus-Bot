from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.network.network_manager import NetworkManager

URLS = [
    "https://egspec.org/",
    "https://coe.egspec.org/",
    "https://admissions.egspgroup.in/",
    "https://huggingface.co/",
]

net = NetworkManager()

for url in URLS:
    try:
        r = net.get(url, stream=True)
        print(f"[OK] {r.status_code} {url}")
        r.close()
    except Exception as e:
        print(f"[FAIL] {url} -> {e}")
