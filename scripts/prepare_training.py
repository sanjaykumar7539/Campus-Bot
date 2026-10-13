"""Audit local stores and export public source text for GPU domain adaptation."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import config


def main():
    import chromadb
    output = ROOT / 'training'
    output.mkdir(exist_ok=True)
    report = {'sqlite': {}, 'collections': [], 'excluded_chunks': 0}
    db = ROOT / 'college_chatbot.db'
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
        report['sqlite']['integrity'] = connection.execute('PRAGMA integrity_check').fetchone()[0]
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        report['sqlite']['row_counts'] = {
            name: connection.execute('SELECT COUNT(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]
            for (name,) in tables
        }
    client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
    examples = []
    seen = set()
    for collection in client.list_collections():
        report['collections'].append({'name': collection.name, 'count': collection.count()})
        rows = collection.get(include=['documents', 'metadatas'])
        for text, meta in zip(rows['documents'], rows['metadatas']):
            meta = meta or {}
            url = meta.get('source_url', '')
            host = (urlparse(url).hostname or '').lower()
            trusted = any(host == domain or host.endswith('.' + domain) for domain in config.NETWORK_ALLOWED_DOMAINS)
            if not trusted or not text or len(text.strip()) < 80:
                report['excluded_chunks'] += 1
                continue
            # Remove the generated contextual prefix, preserving original source text.
            text = text.split('\n', 1)[1] if text.startswith('[Institute:') and '\n' in text else text
            digest = hashlib.sha256(text.strip().encode()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            examples.append({'text': text.strip(), 'source_url': url, 'sha256': digest})
    sources = sorted({row['source_url'] for row in examples}, key=lambda url: hashlib.sha256(url.encode()).hexdigest())
    if len(sources) < 2:
        raise RuntimeError('At least two public sources are required for separate training and validation sets.')
    held_out = set(sources[:max(1, len(sources) // 10)])
    splits = {'train': [], 'validation': []}
    for row in examples:
        splits['validation' if row['source_url'] in held_out else 'train'].append(row)
    for name, rows in splits.items():
        (output / f'{name}.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    report.update({'examples': {name: len(rows) for name, rows in splits.items()},
                   'public_sources': len(sources), 'source_overlap': 0,
                   'training_type': 'continued language modeling on public source text; not validated question-answer tuning',
                   'private_chat_logs_exported': False})
    (output / 'audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
