from __future__ import annotations

import hashlib
import os
from pathlib import Path

from src.network.network_manager import NetworkManager

class DownloadManager:
    def __init__(self):
        self.net = NetworkManager()
        self.chunk_size = int(os.getenv("DOWNLOAD_CHUNK_SIZE", str(1024 * 1024)))

    @staticmethod
    def sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def download(
        self,
        url: str,
        destination: str | Path,
        expected_sha256: str | None = None,
        resume: bool = True,
    ) -> Path:
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_suffix(dest.suffix + ".part")

        if dest.exists():
            if expected_sha256:
                if self.sha256(dest).lower() == expected_sha256.lower():
                    return dest
            else:
                return dest

        headers = {}
        mode = "wb"
        downloaded = 0

        if resume and partial.exists():
            downloaded = partial.stat().st_size
            if downloaded > 0:
                headers["Range"] = f"bytes={downloaded}-"
                mode = "ab"

        response = self.net.get(url, headers=headers, stream=True)
        if response.status_code == 416 and partial.exists():
            partial.replace(dest)
            return dest

        response.raise_for_status()

        # If server ignored Range, restart cleanly.
        if downloaded and response.status_code == 200:
            downloaded = 0
            mode = "wb"

        total_header = response.headers.get("content-length")
        remaining = int(total_header) if total_header and total_header.isdigit() else None
        total = (downloaded + remaining) if remaining is not None else None

        with partial.open(mode) as f:
            current = downloaded
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                current += len(chunk)
                if total:
                    pct = current * 100 / total
                    print(f"\rDownloading {dest.name}: {pct:6.2f}% ", end="", flush=True)
                else:
                    print(f"\rDownloading {dest.name}: {current / 1024 / 1024:.1f} MB ", end="", flush=True)

        print()
        partial.replace(dest)

        if expected_sha256:
            actual = self.sha256(dest)
            if actual.lower() != expected_sha256.lower():
                dest.unlink(missing_ok=True)
                raise ValueError(
                    f"SHA256 mismatch for {dest.name}\n"
                    f"Expected: {expected_sha256}\nActual:   {actual}"
                )

        return dest
