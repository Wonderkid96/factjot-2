from unittest.mock import patch
from src.services.discovery.wikidata_patterns import fetch_pattern_candidates


def test_fetch_pattern_returns_candidates():
    fake = {"results": {"bindings": [
        {"itemLabel": {"value": "S.S. Edmund Fitzgerald"}, "item": {"value": "http://wikidata.org/entity/Q123"}, "description": {"value": "American freighter that sank in Lake Superior"}}
    ]}}
    with patch("src.services.discovery.wikidata_patterns._sparql", return_value=fake):
        candidates = fetch_pattern_candidates(pattern_key="lost_ships")
    assert len(candidates) >= 1
    assert candidates[0].source == "wikidata"
