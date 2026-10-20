from src.monitor.website_monitor import WebsiteMonitor


class Response:
    def __init__(self, url, content, content_type='text/html', status=200):
        self.url, self.content, self.status_code = url, content, status
        self.headers = {'content-type': content_type}
        self.text = content.decode('utf-8', errors='replace')
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(str(self.status_code))


def test_recursive_crawl_and_incremental_second_run(tmp_path, monkeypatch):
    monitor = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    monkeypatch.setattr(monitor, '_sitemap_urls', lambda: set())
    pages = {
        'https://example.com/': Response('https://example.com/', b'<main>Home official information</main><a href="/about/">About</a><a href="/x.pdf">PDF</a>'),
        'https://example.com/about/': Response('https://example.com/about/', b'<main>Detailed admissions and department information</main>'),
        'https://example.com/x.pdf': Response('https://example.com/x.pdf', b'%PDF-1.4 test', 'application/pdf'),
    }
    monkeypatch.setattr(monitor, '_fetch_response', lambda url, stream=False: pages[url])
    first = monitor.scan()
    second = monitor.scan()
    assert first['visited_count'] == 3 and len(first['new_documents']) == 1
    assert second['changed_pages'] == [] and second['new_documents'] == []


def test_duplicate_page_content_is_saved_once(tmp_path):
    monitor = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    body = b'Same normalized institutional content'
    monitor._store('https://example.com/a', b'URL: a\n'+body, 'page', 'text/plain', body)
    monitor._store('https://example.com/b', b'URL: b\n'+body, 'page', 'text/plain', body)
    assert len(list((tmp_path/'data'/'pages').glob('*.txt'))) == 1


def test_expiring_signed_downloads_are_not_crawled(tmp_path, monkeypatch):
    monitor = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    monkeypatch.setattr(monitor, '_sitemap_urls', lambda: set())
    root = Response('https://example.com/', b'<main>Official college information</main><a href="/files/view/doc?expires=123&signature=abc">Expired PDF</a>')
    monkeypatch.setattr(monitor, '_fetch_response', lambda url, stream=False: root if url == monitor.base_url else (_ for _ in ()).throw(AssertionError(url)))
    result = monitor.scan()
    assert result['visited_count'] == 1
    assert result['skipped_volatile_count'] == 1
    assert result['failed_count'] == 0


def test_malformed_sitemap_display_names_are_counted_separately(tmp_path, monkeypatch):
    monitor = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    monkeypatch.setattr(monitor, '_sitemap_urls', lambda: {'https://example.com/academics/departments/artificial intelligence'})
    root = Response('https://example.com/', b'<main>Official college information</main>')
    monkeypatch.setattr(monitor, '_fetch_response', lambda url, stream=False: root if url == monitor.base_url else (_ for _ in ()).throw(AssertionError(url)))
    result = monitor.scan()
    assert result['visited_count'] == 1
    assert result['skipped_malformed_count'] == 1
    assert result['failed_count'] == 0


def test_known_broken_admissions_link_is_not_fetched(tmp_path, monkeypatch):
    monitor = WebsiteMonitor('https://admissions.egspgroup.in/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    monkeypatch.setattr(monitor, '_sitemap_urls', lambda: {'https://admissions.egspgroup.in/engineering'})
    root = Response(monitor.base_url, b'<main>Official admissions information</main>')
    monkeypatch.setattr(monitor, '_fetch_response', lambda url, stream=False: root if url == monitor.base_url else (_ for _ in ()).throw(AssertionError(url)))
    result = monitor.scan()
    assert result['visited_count'] == 1
    assert result['skipped_known_broken_count'] == 1
    assert result['failed_count'] == 0


def test_egspec_legacy_index_alias_is_canonicalized():
    canonical = WebsiteMonitor._canonical_url('https://egspec.org/academics/departments/undergraduate/mechanical-engineering/index.html')
    assert canonical == 'https://egspec.org/academics/departments/undergraduate/mechanical-engineering'


def test_egspec_log_viewer_template_is_not_fetched(tmp_path, monkeypatch):
    monitor = WebsiteMonitor('https://egspec.org/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    monkeypatch.setattr(monitor, '_sitemap_urls', lambda: {'https://egspec.org/log-viewer/{view?}='})
    root = Response(monitor.base_url, b'<main>Official college information</main>')
    monkeypatch.setattr(monitor, '_fetch_response', lambda url, stream=False: root if url == monitor.base_url else (_ for _ in ()).throw(AssertionError(url)))
    result = monitor.scan()
    assert result['visited_count'] == 1
    assert result['skipped_malformed_count'] == 1
    assert result['failed_count'] == 0
