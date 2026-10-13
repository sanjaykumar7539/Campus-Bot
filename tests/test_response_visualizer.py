import json

from src.visuals.response_visualizer import ResponseVisualizer


def test_unverified_location_uses_search_link(tmp_path):
    registry = tmp_path / 'locations.json'
    registry.write_text(json.dumps([{
        'id': 'main', 'title': 'Main campus', 'aliases': ['campus'],
        'address': 'Verified address', 'verified': False,
        'source_url': 'https://example.edu/contact',
    }]), encoding='utf-8')
    visual = ResponseVisualizer(registry).build('Where is the campus?')[0]
    assert visual['type'] == 'map_link'
    assert visual['map_url'].startswith('https://www.openstreetmap.org/search?')


def test_only_verified_coordinates_create_embedded_map(tmp_path):
    registry = tmp_path / 'locations.json'
    registry.write_text(json.dumps([{
        'id': 'library', 'title': 'Library', 'aliases': ['library'],
        'address': 'Campus', 'latitude': 10.5, 'longitude': 79.8,
        'zoom': 17, 'verified': True,
    }]), encoding='utf-8')
    visual = ResponseVisualizer(registry).build('Show library location on map')[0]
    assert visual == {
        'type': 'map', 'id': 'library', 'title': 'Library', 'address': 'Campus',
        'source_url': None, 'latitude': 10.5, 'longitude': 79.8, 'zoom': 17,
    }


def test_non_location_query_has_no_visual(tmp_path):
    registry = tmp_path / 'locations.json'
    registry.write_text('[{"aliases":["campus"],"verified":false}]', encoding='utf-8')
    assert ResponseVisualizer(registry).build('Tell me the campus fees') == []


def test_postgis_result_is_preferred_for_location_query(tmp_path):
    class FakeRepository:
        def ensure_synced(self, locations): self.locations = locations
        def find_best(self, query):
            return {'id': 'cse', 'title': 'CSE Block', 'aliases': ['cse'], 'address': 'North campus',
                    'latitude': 10.76, 'longitude': 79.84, 'zoom': 18, 'verified': True,
                    'source_url': 'https://example.edu/cse'}

    registry = tmp_path / 'locations.json'
    registry.write_text('[]', encoding='utf-8')
    visual = ResponseVisualizer(registry, FakeRepository()).build('CSE block enga irukku?')[0]
    assert visual['type'] == 'map'
    assert visual['title'] == 'CSE Block'
    assert visual['latitude'] == 10.76
