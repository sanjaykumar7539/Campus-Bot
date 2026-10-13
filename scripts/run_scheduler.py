import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.monitor.website_monitor import WebsiteMonitor


def continuous_monitor(interval_minutes: int = 60):
    monitor = WebsiteMonitor()
    print(f'Website monitor active; checking every {interval_minutes} minutes. Ctrl+C to stop.')
    while True:
        try:
            monitor.run_monitor_cycle()
        except KeyboardInterrupt:
            print('Monitor stopped.')
            break
        except Exception as exc:
            print(f'Monitor cycle failed: {exc}')
        time.sleep(interval_minutes * 60)


if __name__ == '__main__':
    continuous_monitor(60)
