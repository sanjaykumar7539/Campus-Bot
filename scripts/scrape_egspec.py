import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitor.official_sources_monitor import OfficialSourcesMonitor

if __name__ == "__main__":
    print("Scraping all trusted CampusMind institute sources...")
    result = OfficialSourcesMonitor().sync_once(reingest=False)
    print("\nScrape complete. Run ingest_documents.py next if reindexing manually.")
    print(result)
