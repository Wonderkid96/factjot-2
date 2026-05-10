from unittest.mock import patch
from src.services.verification.fact_checker import verify_claim


def test_verify_passes_when_two_sources_agree():
    with patch("src.services.verification.fact_checker._llm_judge") as judge:
        judge.return_value = {"supported": True, "confidence": 0.85}
        result = verify_claim(claim="Apollo 11 landed in 1969", sources=["nasa.gov/apollo", "wikipedia/Apollo_11"])
    assert result.verified


def test_verify_fails_below_confidence():
    with patch("src.services.verification.fact_checker._llm_judge") as judge:
        judge.return_value = {"supported": False, "confidence": 0.4}
        result = verify_claim(claim="x", sources=["a", "b"])
    assert not result.verified
