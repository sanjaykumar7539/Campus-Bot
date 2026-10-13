"""PostGIS-backed trusted campus location lookup and registry synchronization."""
from __future__ import annotations

import json
import re
import threading
from typing import Any

from config import config
from src.database.db_manager import DatabaseManager
from src.utils.logger import get_logger


logger = get_logger('campus_locations')


class CampusLocationRepository:
    def __init__(self, db_manager: DatabaseManager | None = None):
        self._db = db_manager
        self._sync_lock = threading.Lock()
        self._synced = False

    @property
    def enabled(self) -> bool:
        return bool(self._db and self._db.is_postgres) or str(config.DATABASE_URL).startswith(('postgresql://', 'postgres://'))

    @property
    def db(self) -> DatabaseManager:
        if self._db is None:
            self._db = DatabaseManager()
        return self._db

    def sync_registry(self, locations: list[dict[str, Any]]) -> int:
        """Upsert only administrator-verified, valid coordinate records."""
        if not self.enabled:
            return 0
        valid = []
        for item in locations:
            lat, lng = item.get('latitude'), item.get('longitude')
            if item.get('verified') is not True or not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                continue
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                continue
            valid.append(item)
        with self.db.get_connection() as conn:
            for item in valid:
                conn.execute("""
                    INSERT INTO campus_locations
                    (external_id, location_name, category, description, address, aliases,
                     source_url, verified, zoom, geom)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,%s,
                            ST_SetSRID(ST_MakePoint(%s,%s),4326))
                    ON CONFLICT (external_id) DO UPDATE SET
                      location_name=EXCLUDED.location_name, category=EXCLUDED.category,
                      description=EXCLUDED.description, address=EXCLUDED.address,
                      aliases=EXCLUDED.aliases, source_url=EXCLUDED.source_url,
                      verified=EXCLUDED.verified, zoom=EXCLUDED.zoom, geom=EXCLUDED.geom,
                      updated_at=CURRENT_TIMESTAMP
                """, (
                    str(item.get('id')), str(item.get('title', 'Campus location')),
                    item.get('category'), item.get('description'), item.get('address'),
                    json.dumps(item.get('aliases', [])), item.get('source_url'),
                    max(1, min(20, int(item.get('zoom', 16)))), lng, lat,
                ))
        return len(valid)

    def ensure_synced(self, locations: list[dict[str, Any]]) -> None:
        if self._synced or not self.enabled:
            return
        with self._sync_lock:
            if self._synced:
                return
            self.sync_registry(locations)
            self._synced = True

    @staticmethod
    def _terms(query: str) -> set[str]:
        ignored = {'where', 'is', 'the', 'a', 'an', 'show', 'me', 'map', 'route', 'direction',
                   'location', 'located', 'enga', 'engae', 'irukku', 'iruku', 'please'}
        return {term for term in re.findall(r'[\w&.-]+', query.casefold()) if len(term) > 1 and term not in ignored}

    def find_best(self, query: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT external_id, location_name, category, description, address, aliases,
                       source_url, zoom, ST_Y(geom) AS latitude, ST_X(geom) AS longitude
                FROM campus_locations WHERE verified=TRUE
            """).fetchall()
        terms = self._terms(query)
        best, best_score = None, 0
        for row in rows:
            aliases = row[5] if isinstance(row[5], list) else json.loads(row[5] or '[]')
            labels = [str(row[1]), *map(str, aliases)]
            haystack = ' '.join(labels).casefold()
            score = sum(3 if term in str(row[1]).casefold() else 1 for term in terms if term in haystack)
            if score > best_score:
                best_score = score
                best = {
                    'id': row[0], 'title': row[1], 'category': row[2], 'description': row[3],
                    'address': row[4] or '', 'aliases': aliases, 'source_url': row[6],
                    'zoom': row[7], 'latitude': float(row[8]), 'longitude': float(row[9]),
                    'verified': True,
                }
        return best

    def find_nearest(self, latitude: float, longitude: float, limit: int = 5) -> list[dict[str, Any]]:
        """Return verified locations ordered by PostGIS geography distance."""
        if not self.enabled or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return []
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT external_id, location_name, ST_Y(geom), ST_X(geom),
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)
                FROM campus_locations WHERE verified=TRUE
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s,%s),4326) LIMIT %s
            """, (longitude, latitude, longitude, latitude, max(1, min(20, limit)))).fetchall()
        return [{'id': r[0], 'title': r[1], 'latitude': float(r[2]), 'longitude': float(r[3]),
                 'distance_meters': round(float(r[4]), 1)} for r in rows]
