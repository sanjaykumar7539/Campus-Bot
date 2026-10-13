"""Run one sync for all trusted EGSPEC/college official sources, then exit."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.monitor.official_sources_monitor import OfficialSourcesMonitor

if __name__ == '__main__':
    print('Checking all trusted institute websites for new or changed content...')
    result = OfficialSourcesMonitor().sync_once(reingest=True)
    print('Sync completed.')
    print(result)
