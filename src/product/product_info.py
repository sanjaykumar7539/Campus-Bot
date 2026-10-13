from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import secrets

from config import config
from src.core.readiness import check_readiness

_STATE_FILE = Path(config.DATA_DIR) / ".product_state.json"


def _install_id() -> str:
    try:
        if _STATE_FILE.exists():
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            if data.get("install_id"):
                return str(data["install_id"])
    except Exception:
        pass
    install_id = "inst_" + secrets.token_hex(8)
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps({
            "install_id": install_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2), encoding="utf-8")
    except Exception:
        pass
    return install_id


def get_product_info() -> dict:
    return {
        "product_name": config.PRODUCT_NAME,
        "product_version": config.PRODUCT_VERSION,
        "edition": config.PRODUCT_EDITION,
        "institute_name": config.INSTITUTE_NAME,
        "institute_short_name": config.INSTITUTE_SHORT_NAME,
        "support_email": config.SUPPORT_EMAIL,
        "official_website": config.MONITOR_BASE_URL,
        "features": [
            "verified_institute_qa", "official_answer_sources", "admissions_contact_fallback",
            "auto_website_sync", "auto_pdf_ingestion", "feedback", "voice_input"
        ],
    }


def get_product_status() -> dict:
    ready = check_readiness()
    return {
        **get_product_info(),
        "install_id": _install_id(),
        "environment": config.APP_ENV,
        "monitor_enabled": config.MONITOR_ENABLED,
        "monitor_interval_seconds": config.MONITOR_INTERVAL_SECONDS,
        "chat_ready": ready["ready_for_full_chat"],
        "components": ready,
    }
