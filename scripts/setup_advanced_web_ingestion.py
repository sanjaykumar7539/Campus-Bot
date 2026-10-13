from __future__ import annotations

import subprocess
import sys


def run(cmd):
    print('>', ' '.join(cmd))
    subprocess.check_call(cmd)


def main():
    print('Installing optional CampusMind advanced web-ingestion dependencies...')
    run([sys.executable, '-m', 'pip', 'install', '-U', 'crawl4ai', 'playwright'])
    print('\nInstalling Crawl4AI browser dependencies...')
    try:
        run(['crawl4ai-setup'])
    except Exception:
        print('crawl4ai-setup was not available on PATH; Crawl4AI may install its browser on first use.')
    print('\nInstalling Playwright Chromium...')
    run([sys.executable, '-m', 'playwright', 'install', 'chromium'])
    print('\nDone. AnakinScraper is intentionally optional and self-hosted; enable it only if your local service is running.')


if __name__ == '__main__':
    main()
