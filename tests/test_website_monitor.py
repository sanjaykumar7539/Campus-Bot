from pathlib import Path

from src.monitor.website_monitor import WebsiteMonitor


def test_meaningful_text_ignores_nav_and_script():
    html = '<html><nav>menu</nav><main><h1>Fees</h1><p>Official fee details</p></main><script>x=1</script></html>'
    text = WebsiteMonitor._meaningful_text(html)
    assert 'Official fee details' in text and 'menu' not in text and 'x=1' not in text


def test_discover_pdf_links_same_domain_only(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    html = '''
    <a href="/docs/new-circular.pdf">Circular</a>
    <a href="https://example.com/files/timetable.PDF">Timetable</a>
    <a href="https://other.com/evil.pdf">Other</a>
    '''
    links = m._discover_pdf_links(html, 'https://example.com/news/')
    assert 'https://example.com/docs/new-circular.pdf' in links
    assert 'https://example.com/files/timetable.PDF' in links
    assert all('other.com' not in x for x in links)


def test_scan_does_not_duplicate_unchanged_pdf(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    m.pages_to_monitor = ['']
    html = '<main>News update</main><a href="/docs/circular.pdf">PDF</a>'
    m._fetch = lambda url: html

    pdf_bytes = b'%PDF-1.4 same-content'
    class Resp:
        content = pdf_bytes
        headers = {'content-type': 'application/pdf'}
    m._fetch_response = lambda url, stream=False: Resp()

    first = m.scan()
    second = m.scan()
    assert len(first['new_pdfs']) == 1
    assert first['changed_pdfs'] == []
    assert second['new_pdfs'] == []
    assert second['changed_pdfs'] == []
    assert second['changed_pages'] == []


def test_scan_detects_changed_pdf_content(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    m.pages_to_monitor = ['']
    m._fetch = lambda url: '<main>News</main><a href="/docs/circular.pdf">PDF</a>'
    contents = [b'%PDF-1.4 version-one', b'%PDF-1.4 version-two']

    class Resp:
        headers = {'content-type': 'application/pdf'}
        def __init__(self, content): self.content = content

    m._fetch_response = lambda url, stream=False: Resp(contents.pop(0))
    first = m.scan()
    second = m.scan()
    assert len(first['new_pdfs']) == 1
    assert len(second['changed_pdfs']) == 1


def test_page_failure_keeps_existing_pdf_state(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    m.pages_to_monitor = ['']
    m.state['pdfs']['https://example.com/old.pdf'] = {'hash': 'abc', 'path': 'old.pdf'}
    def fail(url):
        raise RuntimeError('temporary outage')
    m._fetch = fail
    result = m.scan()
    assert result['reachable_pages'] == 0
    assert 'https://example.com/old.pdf' in m.state['pdfs']


def test_monitor_cycle_reingests_only_on_change(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    calls = {'count': 0}
    m.scan = lambda: {'changed_pages': [], 'new_pdfs': [], 'changed_pdfs': [], 'discovered_pdf_count': 0, 'reachable_pages': 1}
    m.reingest_documents = lambda: calls.__setitem__('count', calls['count'] + 1) or True
    result = m.run_monitor_cycle()
    assert result['reingested'] is False
    assert calls['count'] == 0


def test_safe_pdf_filename_is_stable(tmp_path):
    m = WebsiteMonitor('https://example.com/', str(tmp_path/'data'), str(tmp_path/'state.json'))
    one = m._pdf_local_path('https://example.com/docs/Exam%20Circular.pdf')
    two = m._pdf_local_path('https://example.com/docs/Exam%20Circular.pdf')
    assert one == two
    assert one.suffix.lower() == '.pdf'
