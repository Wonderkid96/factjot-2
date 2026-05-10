import json
from dataclasses import dataclass
from src.core.anthropic_client import AnthropicClient, extract_json
from src.core.logger import get_logger
from src.services.state import ledgers


log = get_logger("curation.topic_curator")


@dataclass
class CandidateTopic:
    topic: str
    hook_potential: int
    counterintuitiveness: int
    share_trigger: int
    specificity: int
    verifiability: int
    risk_flags: list[str]

    @property
    def total(self) -> int:
        return self.hook_potential + self.counterintuitiveness + self.share_trigger + self.specificity + self.verifiability


SCORER_PROMPT = """You score real-world fact candidates for a faceless Instagram reels brand called Fact Jot.
Brand promise: facts that hook people in the first 1.5s, keep them to the end, and feel so shocking they NEED to share.

You receive a list of discovered candidates (each with text + source + upvote signal). For each one return JSON:
- topic: the candidate text (verbatim or lightly cleaned)
- hook_potential: 1-10
- counterintuitiveness: 1-10 (defies a held belief?)
- share_trigger: 1-10 (would the average viewer feel compelled to share?)
- specificity: 1-10 (resolves to a canonical entity? proper nouns help)
- verifiability: 1-10 (can be sourced from authoritative material?)
- risk_flags: list of strings (graphic, political, contested, etc.)

Avoid these recently used topics: {recent}

Candidates:
{candidates}

Return only a JSON array of objects, one per candidate, in the same order.
"""

CRITIQUE_PROMPT = """You are an editorial reviewer for a faceless reels brand.
Review these scored candidate topics. Reject any with score <7 on any axis OR with risk_flags present.
Pick the highest combined-score survivor. Tie-break on share_trigger.

Candidates:
{candidates}

Return JSON: {{"winner_index": int, "rejected": [{{"index": int, "reason": str}}]}}.
If all rejected, return {{"winner_index": null, "rejected": [...]}}.
"""


def _call_sonnet_scorer(prompt: str) -> str:
    return AnthropicClient().text(system="You are an editorial scorer for a faceless reels brand.", user=prompt)


def _call_opus(prompt: str) -> str:
    c = AnthropicClient()
    return c.text(system="You are an editorial reviewer.", user=prompt, model=c.model_judge)


def curate_topic(recent_topics: list[str], discovered) -> CandidateTopic:
    """Score discovered candidates from §11.5 and pick the winner.

    `discovered` is list[DiscoveredCandidate] from the discovery orchestrator.
    """
    candidates_summary = "\n".join(
        f"- text: {c.text}\n  source: {c.source}\n  url: {c.source_url}\n  upvotes: {c.upvotes}"
        for c in discovered
    )
    scoring_text = _call_sonnet_scorer(SCORER_PROMPT.format(
        recent=", ".join(recent_topics) or "(none)",
        candidates=candidates_summary,
    ))
    try:
        scored = [CandidateTopic(**c) for c in json.loads(extract_json(scoring_text))]
    except (json.JSONDecodeError, TypeError) as e:
        log.error("scorer_json_parse_failed", error=str(e), preview=scoring_text[:500])
        raise
    critique_text = _call_opus(CRITIQUE_PROMPT.format(candidates=json.dumps([c.__dict__ for c in scored], indent=2)))
    try:
        critique = json.loads(extract_json(critique_text))
    except json.JSONDecodeError as e:
        log.error("critique_json_parse_failed", error=str(e), preview=critique_text[:500])
        raise
    if critique.get("winner_index") is None:
        raise RuntimeError(f"All candidates rejected: {critique['rejected']}")
    winner = scored[critique["winner_index"]]

    # Log to ledger for post-hoc analysis (spec §10.7)
    ledgers.append("topic_curation.jsonl", {
        "discovered_count": len(discovered),
        "scored": [c.__dict__ for c in scored],
        "critique": critique,
        "winner": winner.__dict__,
    })
    return winner
