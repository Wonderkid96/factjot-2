from unittest.mock import patch
from src.services.curation.topic_curator import curate_topic
from src.services.discovery.models import DiscoveredCandidate


def test_curator_scores_discovered_candidates_and_picks_winner():
    discovered = [
        DiscoveredCandidate(text="Apollo 11 carried a fallback rocket on the lander", source="reddit", source_url="https://r/x", upvotes=50000),
        DiscoveredCandidate(text="It rained today in Manchester", source="reddit", source_url="https://r/y", upvotes=5),
    ]
    scoring_json = '''[
      {"topic": "Apollo 11 carried a fallback rocket on the lander", "hook_potential": 9, "counterintuitiveness": 8, "share_trigger": 9, "specificity": 9, "verifiability": 9, "risk_flags": []},
      {"topic": "It rained today in Manchester", "hook_potential": 2, "counterintuitiveness": 1, "share_trigger": 1, "specificity": 8, "verifiability": 9, "risk_flags": []}
    ]'''
    critique_json = '''{"winner_index": 0, "rejected": [{"index": 1, "reason": "low scores"}]}'''
    with patch("src.services.curation.topic_curator._call_sonnet_scorer", return_value=scoring_json):
        with patch("src.services.curation.topic_curator._call_opus", return_value=critique_json):
            with patch("src.services.curation.topic_curator.ledgers") as ledg:
                winner = curate_topic(recent_topics=[], discovered=discovered)
    assert "Apollo" in winner.topic
    assert winner.share_trigger == 9
    assert ledg.append.called  # Verify ledger logging happens
