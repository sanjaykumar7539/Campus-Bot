import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.monitor.website_monitor import WebsiteMonitor

if __name__ == '__main__':
    WebsiteMonitor().run_monitor_cycle()
