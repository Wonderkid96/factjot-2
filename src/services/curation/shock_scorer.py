"""LLM-based "shock value" scoring for discovery candidates.

Why: Reddit upvotes proxy for *popular* facts, not *shocking* ones. The math
of mass-appeal subreddits means top-of-month posts are typically facts that
many users already half-knew ("octopus has 3 hearts"). We want the opposite:
specific, visceral, causally-charged claims most people have NEVER heard.

This service takes the top-N discovery candidates and asks Claude Haiku to
score each on a 1-10 axis. Cheap (~$0.001 per call) and runs once per reel.
The pipeline picks the highest-scoring candidate that survives fact-check.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from src.core.anthropic_client import AnthropicClient, extract_json
from src.core.logger import get_logger
from src.services.discovery.models import DiscoveredCandidate


log = get_logger("curation.shock_scorer")


SHOCK_RUBRIC_SYSTEM = """You are a viral-content editor for a faceless Instagram facts brand.

You evaluate candidate facts on a 1-10 SHOCK VALUE scale. Shock value means:
- Counterintuitive (most people would guess wrong)
- Specific (named places/people/dates/numbers, not vague)
- Visceral or causally charged (death, betrayal, hidden, escape, survival)
- NOT a TIL cliché (octopuses, blue whales, Bohemian Rhapsody, Mars rovers)
- NOT a soft generosity / inspirational story
- NOT a celebrity drama / political claim

Scoring guide:
- 9-10: stops your thumb instantly. "A man stood inside both atomic bombs and lived."
- 7-8: strong, specific, unfamiliar. "A Bulgarian dissident was assassinated by a poisoned umbrella in 1978."
- 5-6: interesting but well-known or soft. "The Wright brothers' first flight lasted 12 seconds."
- 3-4: nice but mild. "Cows have best friends and get stressed when separated."
- 1-2: boring, vague, or familiar to the point of meme. "Bananas are berries."

Be strict. If a fact has been widely shared on Instagram/TikTok for years, it's not shocking any more.
"""


SHOCK_RUBRIC_USER = """Score these candidates on shock value (1-10).

Return JSON: {{"scores": [{{"i": int, "score": int, "reason": str}}, ...]}}

One entry per candidate, in input order. Keep `reason` to 8 words max.

Candidates:
{candidates}
"""


@dataclass
class ScoredCandidate:
    candidate: DiscoveredCandidate
    shock_score: int     # 1-10
    reason: str


def _format_candidates(cands: list[DiscoveredCandidate]) -> str:
    lines = []
    for i, c in enumerate(cands):
        # Trim to 160 chars so the prompt stays bounded even with 30 candidates
        snippet = (c.text or "")[:160].replace("\n", " ").strip()
        lines.append(f"[{i}] {snippet}")
    return "\n".join(lines)


def score_candidates(
    candidates: list[DiscoveredCandidate],
    max_to_score: int = 25,
) -> list[ScoredCandidate]:
    """Rate the top-N candidates on shock value. Returns the full list sorted
    by shock_score descending. Falls back to upvote-sort if the LLM call fails.
    """
    if not candidates:
        return []
    head = candidates[:max_to_score]
    user = SHOCK_RUBRIC_USER.format(candidates=_format_candidates(head))
    try:
        raw = AnthropicClient().text(system=SHOCK_RUBRIC_SYSTEM, user=user)
        data = json.loads(extract_json(raw))
        score_by_index = {int(row["i"]): row for row in data.get("scores", [])}
    except Exception as e:
        log.warning("shock_score_failed", error=str(e)[:200])
        # Fall back to upvote-sort (already the input order in most callers)
        return [
            ScoredCandidate(candidate=c, shock_score=5, reason="scorer-error fallback")
            for c in head
        ]

    out: list[ScoredCandidate] = []
    for i, c in enumerate(head):
        row = score_by_index.get(i)
        if row is None:
            out.append(ScoredCandidate(candidate=c, shock_score=5, reason="no-score fallback"))
            continue
        try:
            score = max(1, min(10, int(row["score"])))
        except (KeyError, TypeError, ValueError):
            score = 5
        out.append(ScoredCandidate(
            candidate=c,
            shock_score=score,
            reason=str(row.get("reason", ""))[:100],
        ))
    out.sort(key=lambda s: (s.shock_score, s.candidate.upvotes), reverse=True)
    return out
