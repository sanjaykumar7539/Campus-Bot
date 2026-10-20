from __future__ import annotations

import hashlib, json, re, threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from config import config
from src.monitor.network_client import ResilientNetworkClient
from src.monitor.web_ingestion_router import WebIngestionRouter, SafeAccessPolicy


class WebsiteMonitor:
    """Full same-domain crawler with retries, deduplication and incremental updates."""
    DOCUMENT_EXTENSIONS = {'.pdf','.txt','.md','.csv','.json','.xml','.doc','.docx','.xls','.xlsx','.ppt','.pptx'}
    IGNORED_EXTENSIONS = {'.jpg','.jpeg','.png','.gif','.webp','.svg','.ico','.css','.js','.map','.woff','.woff2','.ttf','.mp3','.mp4','.avi','.mov','.zip','.rar','.7z','.exe','.apk'}

    def __init__(self, base_url=None, data_dir=None, state_file=None):
        self.base_url = self._canonical_url(base_url or config.MONITOR_BASE_URL)
        self.domain = urlparse(self.base_url).netloc.lower()
        self.data_dir = Path(data_dir or Path(config.DATA_DIR)/'website_scraped')
        self.document_dir, self.page_dir = self.data_dir/'documents', self.data_dir/'pages'
        self.document_dir.mkdir(parents=True, exist_ok=True); self.page_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir = self.document_dir  # backwards-compatible public attribute
        self.state_file = Path(state_file or Path(config.BASE_DIR)/'src/monitor/monitor_state.json')
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.network = ResilientNetworkClient()
        self.web_router = WebIngestionRouter()
        self.session = self.network.session  # compatibility for existing callers/tests
        self._stop_event = threading.Event(); self.load_state()

    @staticmethod
    def _canonical_url(url):
        p=urlparse(str(url).strip()); path=re.sub(r'/+','/',p.path or '/')
        # EGSPEC publishes both legacy /index.html links and clean department
        # routes. The legacy aliases frequently serve only a JavaScript shell.
        if (p.hostname or '').casefold() in {'egspec.org', 'www.egspec.org'} and path.lower().endswith('/index.html'):
            path=path[:-len('/index.html')] or '/'
        query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query,keep_blank_values=True)
                               if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid'}))
        return urlunparse((p.scheme.lower() or 'https',p.netloc.lower(),path,'',query,''))

    def load_state(self):
        try: raw=json.loads(self.state_file.read_text('utf-8')) if self.state_file.exists() else {}
        except Exception: raw={}
        if raw.get('version') != 3: raw={}
        self.state={'version':3,'last_check':raw.get('last_check'),'resources':raw.get('resources',{}),'content_hashes':raw.get('content_hashes',{})}
        # Compatibility view for callers written against the older PDF-only monitor.
        self.state['pdfs'] = raw.get('pdfs', {})

    def save_state(self):
        self.state['last_check']=datetime.now(timezone.utc).isoformat(); tmp=self.state_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state,indent=2,sort_keys=True),encoding='utf-8'); tmp.replace(self.state_file)

    def _fetch_response(self,url,stream=False):
        if config.NETWORK_MODE == 'offline':
            raise requests.ConnectionError('NETWORK_MODE=offline; using existing local knowledge only')
        return self.network.get(url, stream=stream, allow_redirects=True)

    def _fetch(self,url): return self._fetch_response(url).text

    @staticmethod
    def _meaningful_text(html):
        soup=BeautifulSoup(html,'html.parser')
        for tag in soup(['script','style','nav','footer','header','aside','noscript','form']): tag.decompose()
        main=soup.find('main') or soup.find('article') or soup.body or soup
        lines=(re.sub(r'\s+',' ',x).strip() for x in main.get_text('\n',strip=True).splitlines())
        return '\n'.join(dict.fromkeys(x for x in lines if x))

    @staticmethod
    def _sha256_bytes(data): return hashlib.sha256(data).hexdigest()
    @staticmethod
    def _safe_name(value,fallback='resource'):
        value=re.sub(r'[^A-Za-z0-9._-]+','_',value).strip('._'); return value[:140] or fallback

    def _is_same_domain(self,url):
        host=urlparse(url).netloc.lower().split(':')[0]; base=self.domain.split(':')[0]
        return host==base or host.endswith('.'+base) or base.endswith('.'+host)

    def _classify(self,url):
        suffix=Path(urlparse(url).path).suffix.lower()
        return 'document' if suffix in self.DOCUMENT_EXTENSIONS else 'ignore' if suffix in self.IGNORED_EXTENSIONS else 'page'

    @staticmethod
    def _is_volatile_url(url):
        """Signed, expiring downloads are not durable crawl documents."""
        parsed = urlparse(url)
        keys = {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        return (bool(keys & {'signature', 'expires', 'token', 'x-amz-signature'})
                and '/files/view/' in parsed.path.casefold())

    @staticmethod
    def _is_malformed_page_url(url):
        # The institute sitemap publishes department display names as URL
        # paths (for example "/academics/departments/artificial intelligence ...").
        # Those paths consistently return 404; real department slugs are
        # hyphenated and usually under /undergraduate/ or /postgraduate/.
        parsed = urlparse(url)
        return (Path(parsed.path).suffix.lower() not in WebsiteMonitor.DOCUMENT_EXTENSIONS
                and (bool(re.search(r'\s|%20|[{}]', parsed.path, re.I))
                     or bool(re.search(r'[{}]', parsed.query))))

    @staticmethod
    def _is_known_broken_url(url):
        parsed = urlparse(url)
        host = (parsed.hostname or '').casefold()
        path = parsed.path.casefold().rstrip('/')
        return ((host in {'egspec.org', 'www.egspec.org'}
                 and path in {'/academics/departments/academics', '/log-viewer'})
                or (host == 'admissions.egspgroup.in' and path == '/engineering'))

    def _links(self,html,page_url):
        soup=BeautifulSoup(html,'html.parser'); found=set()
        for tag,attr in [('a','href'),('iframe','src'),('embed','src'),('object','data')]:
            for node in soup.find_all(tag):
                href=(node.get(attr) or '').strip()
                if not href or href.startswith(('#','mailto:','tel:','javascript:','data:')): continue
                absolute=self._canonical_url(urljoin(page_url,href))
                if urlparse(absolute).scheme in {'http','https'} and self._is_same_domain(absolute): found.add(absolute)
        return found

    def _discover_pdf_links(self,html,page_url):
        return {u for u in self._links(html,page_url) if Path(urlparse(u).path).suffix.lower()=='.pdf'}

    def _resource_path(self,url,kind,content_type=''):
        p=urlparse(url); stem=self._safe_name(Path(p.path).stem or 'home'); suffix=Path(p.path).suffix.lower()
        if kind=='page': suffix='.txt'
        elif not suffix or suffix not in self.DOCUMENT_EXTENSIONS: suffix='.pdf' if 'pdf' in content_type else '.txt'
        key=hashlib.sha1(url.encode()).hexdigest()[:12]
        return (self.page_dir if kind=='page' else self.document_dir)/f'{key}_{stem}{suffix}'

    def _pdf_local_path(self,url): return self._resource_path(url,'document','application/pdf')

    def _store(self,url,data,kind,content_type,digest_data=None):
        digest=self._sha256_bytes(digest_data if digest_data is not None else data)
        previous=self.state['resources'].get(url); duplicate=self.state['content_hashes'].get(digest)
        changed=previous is None or previous.get('hash')!=digest; path=self._resource_path(url,kind,content_type)
        if changed and previous and not previous.get('duplicate_of'):
            old_path=Path(previous.get('path',''))
            if old_path.exists() and old_path != path:
                old_path.unlink()
            if self.state['content_hashes'].get(previous.get('hash')) == url:
                self.state['content_hashes'].pop(previous.get('hash'),None)
        if duplicate and duplicate!=url:
            record_path=self.state['resources'].get(duplicate,{}).get('path') or str(path)
        else:
            tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_bytes(data); tmp.replace(path)
            record_path=str(path); self.state['content_hashes'][digest]=url
        self.state['resources'][url]={'hash':digest,'path':record_path,'kind':kind,'content_type':content_type,
            'duplicate_of':duplicate if duplicate!=url else None,'last_seen':datetime.now(timezone.utc).isoformat()}
        return ('new' if previous is None else 'changed' if changed else 'unchanged'),changed,Path(record_path)

    def _download_pdf(self,url):
        try:
            r=self._fetch_response(url); data=r.content; ctype=r.headers.get('content-type','').split(';')[0].lower()
            if not data.startswith(b'%PDF'):
                print(f'Skipping invalid PDF link (server returned {ctype or "unknown content"}): {url}'); return None
            _,_,path=self._store(url,data,'document','application/pdf'); return path,self._sha256_bytes(data)
        except Exception as exc: print(f'Document fetch failed {url}: {exc}'); return None

    def _sitemap_urls(self):
        pending=deque([urljoin(self.base_url,'sitemap.xml'),urljoin(self.base_url,'sitemap_index.xml')]); seen=set(); urls=set()
        while pending and len(seen)<100:
            site=self._canonical_url(pending.popleft())
            if site in seen: continue
            seen.add(site)
            try:
                soup=BeautifulSoup(self._fetch_response(site).content,'xml')
                for loc in soup.find_all('loc'):
                    u=self._canonical_url(loc.get_text(strip=True))
                    if not self._is_same_domain(u): continue
                    if urlparse(u).path.lower().endswith('.xml'):
                        pending.append(u)
                    else:
                        urls.add(u)
            except Exception: continue
        return urls

    def scan(self):
        if hasattr(self, 'pages_to_monitor'):
            return self._scan_legacy_pages()
        queue=deque([self.base_url,*sorted(self._sitemap_urls())]); visited=set(); failures=[]; skipped_volatile=0; skipped_malformed=0; skipped_broken=0
        changed_pages=[]; new_docs=[]; changed_docs=[]
        while queue and len(visited)<config.MONITOR_MAX_PAGES:
            url=self._canonical_url(queue.popleft())
            if url in visited or not self._is_same_domain(url) or self._classify(url)=='ignore': continue
            if self._is_volatile_url(url):
                skipped_volatile += 1
                continue
            if self._is_malformed_page_url(url):
                skipped_malformed += 1
                continue
            if self._is_known_broken_url(url):
                skipped_broken += 1
                continue
            visited.add(url)
            try:
                r=self._fetch_response(url); final=self._canonical_url(getattr(r,'url',url)); ctype=r.headers.get('content-type','').split(';')[0].lower(); data=r.content
                htmlish='html' in ctype or data.lstrip()[:20].lower().startswith((b'<!doctype html',b'<html'))
                if htmlish:
                    text=self._meaningful_text(r.text)
                    extractor='requests+bs4'
                    extra_links=[]
                    # Existing lightweight extraction stays first. Advanced extractors are
                    # invoked only when the page looks thin/JS-rendered. Explicit access
                    # controls terminate the chain rather than being bypassed.
                    if (config.ADVANCED_WEB_INGESTION and len(text) < config.ADVANCED_WEB_MIN_TEXT
                            and not SafeAccessPolicy.is_blocked(getattr(r, 'status_code', None), r.text)):
                        enhanced=self.web_router.extract(final)
                        if enhanced.blocked:
                            raise PermissionError(f'access-control gate detected by {enhanced.extractor}')
                        if enhanced.ok and len(enhanced.text) > len(text):
                            text=enhanced.text
                            extractor=enhanced.extractor
                            extra_links=enhanced.links
                    if len(text)>=config.MONITOR_MIN_TEXT_LENGTH:
                        body=f'URL: {final}\nEXTRACTOR: {extractor}\n\n{text}'
                        status,changed,_=self._store(final,body.encode(),'page','text/plain',text.encode())
                        if changed: changed_pages.append(final)
                    discovered=set(self._links(r.text,final))
                    discovered.update(u for u in extra_links if self._is_same_domain(u))
                    queue.extend(u for u in discovered if u not in visited)
                elif data.startswith(b'%PDF') or self._classify(final)=='document':
                    if Path(urlparse(final).path).suffix.lower()=='.pdf' and not data.startswith(b'%PDF'):
                        raise ValueError(f'invalid PDF response ({ctype or "unknown content"})')
                    status,changed,_=self._store(final,data,'document',ctype)
                    if status=='new': new_docs.append(final)
                    elif changed: changed_docs.append(final)
            except Exception as exc:
                recovered=False
                response_status = getattr(getattr(exc, 'response', None), 'status_code', None)
                explicit_gate = isinstance(exc, PermissionError) or response_status in {401, 403, 404, 429}
                if config.ADVANCED_WEB_INGESTION and self._classify(url)=='page' and not explicit_gate:
                    enhanced=self.web_router.extract(url)
                    if enhanced.blocked:
                        failures.append({'url':url,'error':f'blocked: {enhanced.reason}'})
                        continue
                    if enhanced.ok:
                        final=url
                        text=enhanced.text
                        body=f'URL: {final}\nEXTRACTOR: {enhanced.extractor}\n\n{text}'
                        _,changed,_=self._store(final,body.encode(),'page','text/plain',text.encode())
                        if changed: changed_pages.append(final)
                        queue.extend(u for u in enhanced.links if u not in visited and self._is_same_domain(u))
                        recovered=True
                if not recovered:
                    failures.append({'url':url,'error':str(exc)})
        self.save_state()
        return {'changed_pages':changed_pages,'new_documents':new_docs,'changed_documents':changed_docs,
                'new_pdfs':new_docs,'changed_pdfs':changed_docs,'discovered_pdf_count':len(new_docs)+len(changed_docs),
                'visited_count':len(visited),'reachable_pages':len(visited)-len(failures),'failed_count':len(failures),
                'failures':failures[:25],'skipped_volatile_count':skipped_volatile,
                'skipped_malformed_count':skipped_malformed,
                'skipped_known_broken_count':skipped_broken,
                'crawl_limit_reached':bool(queue),
                'network':self.network.snapshot()}

    def _scan_legacy_pages(self):
        """Preserve the original public test/API while using the v3 store."""
        changed_pages=[]; new_docs=[]; changed_docs=[]; failures=[]; reachable=0
        for relative in self.pages_to_monitor:
            page_url=self._canonical_url(urljoin(self.base_url, relative))
            try:
                html=self._fetch(page_url); reachable += 1
                text=self._meaningful_text(html)
                if len(text)>=config.MONITOR_MIN_TEXT_LENGTH:
                    _,changed,_=self._store(page_url,f'URL: {page_url}\n\n{text}'.encode(),'page','text/plain',text.encode())
                    if changed: changed_pages.append(page_url)
                for url in sorted(self._discover_pdf_links(html,page_url)):
                    r=self._fetch_response(url); data=r.content
                    if not data.startswith(b'%PDF'): continue
                    status,changed,path=self._store(url,data,'document','application/pdf')
                    record={'hash':self._sha256_bytes(data),'path':str(path)}; self.state['pdfs'][url]=record
                    if status=='new': new_docs.append(url)
                    elif changed: changed_docs.append(url)
            except Exception as exc:
                failures.append({'url':page_url,'error':str(exc)})
        self.save_state()
        return {'changed_pages':changed_pages,'new_documents':new_docs,'changed_documents':changed_docs,
                'new_pdfs':new_docs,'changed_pdfs':changed_docs,'discovered_pdf_count':len(new_docs)+len(changed_docs),
                'visited_count':len(self.pages_to_monitor),'reachable_pages':reachable,'failed_count':len(failures),
                'failures':failures,'crawl_limit_reached':False,
                'network':self.network.snapshot()}

    def run_monitor_cycle(self):
        result=self.scan(); changed=(result.get('changed_pages') or result.get('new_documents') or
                                    result.get('new_pdfs') or result.get('changed_documents') or result.get('changed_pdfs'))
        result['reingested']=self.reingest_documents() if changed else False; return result

    def reingest_documents(self):
        from src.core.knowledge_sync import KnowledgeSyncManager
        manager=KnowledgeSyncManager(); return manager.rebuild() if manager.has_source_documents() else False

    def run_forever(self,interval_seconds=None,initial_scan=True):
        interval=max(60,int(interval_seconds or config.MONITOR_INTERVAL_SECONDS))
        if initial_scan:
            print(f'Initial website sync started: {self.base_url}'); print(f'Website sync result: {self.run_monitor_cycle()}')
        while not self._stop_event.wait(interval):
            try: print(f'Website incremental sync result: {self.run_monitor_cycle()}')
            except Exception as exc: print(f'Website sync failed safely; existing knowledge retained: {exc}')

    def stop(self): self._stop_event.set()

def main(): WebsiteMonitor().run_forever()
if __name__=='__main__': main()
