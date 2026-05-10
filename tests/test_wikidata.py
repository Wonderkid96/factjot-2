from unittest.mock import patch
from src.services.resolution.wikidata import resolve_entity, WikidataEntity


def test_resolve_known_event_returns_entity():
    fake_response = {
        "results": {"bindings": [{
            "item": {"value": "http://www.wikidata.org/entity/Q261221"},
            "itemLabel": {"value": "Johnstown Flood"},
            "date": {"value": "1889-05-31T00:00:00Z"},
            "coords": {"value": "Point(-78.92 40.32)"},
            "category": {"value": "Johnstown Flood"},
        }]}
    }
    with patch("src.services.resolution.wikidata._sparql", return_value=fake_response):
        e = resolve_entity("Johnstown Flood")
    assert e.entity_id == "Q261221"
    assert e.label == "Johnstown Flood"
    assert e.wikimedia_category == "Category:Johnstown Flood"


def test_resolve_unknown_returns_none():
    with patch("src.services.resolution.wikidata._sparql", return_value={"results": {"bindings": []}}):
        e = resolve_entity("zzzznotathing")
    assert e is None
