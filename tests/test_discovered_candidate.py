from src.services.discovery.models import DiscoveredCandidate


def test_candidate_minimum():
    c = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket", source="reddit", source_url="https://reddit.com/r/x/post")
    assert c.text.startswith("Apollo")
    assert c.source == "reddit"


def test_candidate_dedupe_key_normalises_text():
    a = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket.", source="reddit", source_url="x")
    b = DiscoveredCandidate(text="apollo 11 carried a fallback rocket", source="wikipedia_dyk", source_url="y")
    assert a.dedupe_key == b.dedupe_key
