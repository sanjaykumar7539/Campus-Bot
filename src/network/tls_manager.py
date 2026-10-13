import os
import ssl
from pathlib import Path

class TLSManager:
    def __init__(self):
        self.ca_bundle = os.getenv("NETWORK_CA_BUNDLE", "").strip()
        self.verify_tls = os.getenv("VERIFY_TLS", "true").lower() not in {"0", "false", "no"}

    def ssl_context(self):
        if not self.verify_tls:
            raise RuntimeError(
                "TLS verification cannot be disabled in this project. "
                "Provide NETWORK_CA_BUNDLE for a trusted college/custom CA."
            )

        if self.ca_bundle:
            ca = Path(self.ca_bundle)
            if not ca.exists():
                raise FileNotFoundError(f"CA bundle not found: {ca}")
            ctx = ssl.create_default_context(cafile=str(ca))
        else:
            ctx = ssl.create_default_context()

        # Require modern TLS.
        if hasattr(ssl, "TLSVersion"):
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        return ctx
