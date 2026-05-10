from unittest.mock import patch
from src.services.discovery.orchestrator import discover_candidates
from src.services.discovery.models import DiscoveredCandidate


def test_orchestrator_aggregates_and_dedupes():
    same_fact_a = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket.", source="reddit", source_url="x", upvotes=100)
    same_fact_b = DiscoveredCandidate(text="apollo 11 carried a fallback rocket", source="wikipedia_dyk", source_url="y")
    other = DiscoveredCandidate(text="The first photograph took 8 hours", source="reddit", source_url="z")
    with patch("src.services.discovery.orchestrator.fetch_reddit_candidates", return_value=[same_fact_a, other]):
        with patch("src.services.discovery.orchestrator.fetch_dyk_candidates", return_value=[same_fact_b]):
            with patch("src.services.discovery.orchestrator.fetch_atlas_obscura_candidates", return_value=[]):
                with patch("src.services.discovery.orchestrator.fetch_hn_candidates", return_value=[]):
                    with patch("src.services.discovery.orchestrator.fetch_pattern_candidates", return_value=[]):
                        result = discover_candidates(per_source_limit=10)
    # same_fact_a and same_fact_b are the same fact — should dedupe to ONE
    assert len(result) == 2
    # The deduped survivor should track both sources for cross-validation
    apollo = next(c for c in result if "apollo" in c.text.lower())
    assert "reddit" in apollo.raw_metadata.get("seen_in", []) or "wikipedia_dyk" in apollo.raw_metadata.get("seen_in", [])


def test_orchestrator_tolerates_source_failures():
    """A source raising an exception must not kill the others. Best-effort discovery."""
    good = DiscoveredCandidate(text="Wikipedia gave us this", source="wikipedia_dyk", source_url="x")
    with patch("src.services.discovery.orchestrator.fetch_reddit_candidates", side_effect=RuntimeError("boom")):
        with patch("src.services.discovery.orchestrator.fetch_dyk_candidates", return_value=[good]):
            with patch("src.services.discovery.orchestrator.fetch_atlas_obscura_candidates", side_effect=TimeoutError("slow")):
                with patch("src.services.discovery.orchestrator.fetch_hn_candidates", return_value=[]):
                    with patch("src.services.discovery.orchestrator.fetch_pattern_candidates", side_effect=Exception("sparql died")):
                        result = discover_candidates(per_source_limit=10)
    assert len(result) == 1
    assert result[0].source == "wikipedia_dyk"
