"""Create UI metadata from an administrator-maintained location registry.

Coordinates are never extracted from the LLM answer.  Only entries explicitly
marked ``verified`` can become embedded maps; address-only entries become a
safe map-search card instead.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

from .location_repository import CampusLocationRepository


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PROJECT_ROOT / 'data' / 'campus_locations.json'


class ResponseVisualizer:
    def __init__(self, registry_path: Path | str = DEFAULT_REGISTRY, repository: CampusLocationRepository | None = None):
        self.registry_path = Path(registry_path)
        self.repository = repository or CampusLocationRepository()

    def _locations(self) -> list[dict[str, Any]]:
        try:
            value = json.loads(self.registry_path.read_text(encoding='utf-8'))
            return value if isinstance(value, list) else []
        except (OSError, ValueError):
            return []

    @staticmethod
    def _safe_source_url(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        parsed = urlparse(value)
        return value if parsed.scheme == 'https' and parsed.netloc else None

    @staticmethod
    def _has_location_intent(query: str) -> bool:
        lowered = query.casefold()
        return any(word in lowered for word in (
            'where', 'location', 'located', 'address', 'map', 'route', 'direction',
            'enga', 'engae', 'irukku', 'iruku', 'block', 'hostel', 'எங்கு', 'இடம்',
        ))

    @classmethod
    def _matches(cls, query: str, item: dict[str, Any]) -> bool:
        lowered = query.casefold()
        location_intent = cls._has_location_intent(query)
        aliases = [str(value).casefold() for value in item.get('aliases', []) if value]
        title = str(item.get('title', '')).casefold()
        if title:
            aliases.append(title)
        return location_intent and any(alias in lowered for alias in aliases)

    def build(self, query: str) -> list[dict[str, Any]]:
        visuals: list[dict[str, Any]] = []
        locations = self._locations()
        try:
            self.repository.ensure_synced(locations)
            spatial_match = self.repository.find_best(query) if self._has_location_intent(query) else None
        except Exception as exc:
            # Database outage must not break chat; the signed-off JSON registry remains usable.
            spatial_match = None
        candidates = [spatial_match] if spatial_match else locations
        for item in candidates:
            if not item:
                continue
            if not self._matches(query, item):
                continue
            common = {
                'id': str(item.get('id', 'campus-location')),
                'title': str(item.get('title', 'Campus location')),
                'address': str(item.get('address', '')),
                'source_url': self._safe_source_url(item.get('source_url')),
            }
            lat, lng = item.get('latitude'), item.get('longitude')
            if item.get('verified') is True and isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    visuals.append({
                        'type': 'map', **common, 'latitude': lat, 'longitude': lng,
                        'zoom': max(1, min(20, int(item.get('zoom', 16)))),
                    })
                    continue
            search = quote_plus(common['address'] or common['title'])
            visuals.append({
                'type': 'map_link', **common,
                'map_url': f'https://www.openstreetmap.org/search?query={search}',
                'verification_note': 'Embedded pin is disabled until an administrator verifies the GPS coordinates.',
            })
        return visuals
