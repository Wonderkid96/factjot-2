import json
from dataclasses import dataclass
from src.core.anthropic_client import AnthropicClient, extract_json


@dataclass
class VerificationResult:
    verified: bool
    confidence: float
    reason: str = ""


CONFIDENCE_FLOOR = 0.65


JUDGE_PROMPT = """Claim: {claim}
Sources to consider: {sources}

Decide: do these sources support the claim?
Return JSON: {{"supported": bool, "confidence": float (0-1), "reason": str}}.
"""


def _llm_judge(claim: str, sources: list[str]) -> dict:
    raw = AnthropicClient().text(
        system="You are a strict fact-checker. Be conservative. Carry-over from v1 §verification floor.",
        user=JUDGE_PROMPT.format(claim=claim, sources=", ".join(sources)),
    )
    return json.loads(extract_json(raw))


def verify_claim(claim: str, sources: list[str]) -> VerificationResult:
    if len(sources) < 2:
        return VerificationResult(verified=False, confidence=0.0, reason="<2 sources")
    judgment = _llm_judge(claim, sources)
    return VerificationResult(
        verified=bool(judgment["supported"]) and judgment["confidence"] >= CONFIDENCE_FLOOR,
        confidence=float(judgment["confidence"]),
        reason=judgment.get("reason", ""),
    )
