"""Single entry point: advanced EGSPEC UI + API + automatic website/PDF knowledge sync.

Run only: python main.py
The same FastAPI process serves the integrated responsive chatbot UI at /.
"""
from __future__ import annotations
import threading
import webbrowser
import uvicorn
from config import config
from src.api.main import app


def _open_browser():
    try:
        webbrowser.open(f'http://127.0.0.1:{config.PORT}')
    except Exception:
        pass


def _start_monitor():
    from src.monitor.official_sources_monitor import OfficialSourcesMonitor
    monitor = OfficialSourcesMonitor()
    monitor.run_forever(config.MONITOR_INTERVAL_SECONDS)


if __name__ == '__main__':
    if config.MONITOR_ENABLED:
        threading.Thread(target=_start_monitor, name='website-monitor', daemon=True).start()
    else:
        from src.core.knowledge_sync import KnowledgeSyncManager
        KnowledgeSyncManager().bootstrap_if_needed()
    if config.AUTO_OPEN_BROWSER:
        threading.Timer(1.2, _open_browser).start()
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level='info')
