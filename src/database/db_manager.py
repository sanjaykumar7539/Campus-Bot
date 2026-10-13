import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import config


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.url = db_path or config.DATABASE_URL
        self.is_postgres = self.url.startswith(('postgresql://', 'postgres://'))
        if self.is_postgres:
            self.db_path = None
            self._init_db()
            return
        raw = self.url.replace('sqlite:///', '')
        p = Path(raw)
        if not p.is_absolute():
            p = Path(config.BASE_DIR) / p
        self.db_path = str(p.resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        if self.is_postgres:
            import psycopg
            conn = psycopg.connect(self.url)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback(); raise
            finally:
                conn.close()
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        schema_name = 'schema_postgres.sql' if self.is_postgres else 'schema.sql'
        schema = Path(config.BASE_DIR) / 'src' / 'database' / schema_name
        with self.get_connection() as conn:
            if self.is_postgres:
                for statement in schema.read_text(encoding='utf-8').split(';'):
                    if statement.strip(): conn.execute(statement)
            else:
                conn.executescript(schema.read_text(encoding='utf-8'))
