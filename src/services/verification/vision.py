import json
import base64
import requests
from anthropic import Anthropic
from src.core.anthropic_client import extract_json
from src.core.config import Settings


def _fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def _call_vision(image_b64: str, expected_subject: str) -> dict:
    settings = Settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": f'Does this image depict "{expected_subject}"? Respond JSON only: {{"matches": bool, "confidence": float}}.'},
            ],
        }],
    )
    return json.loads(extract_json(msg.content[0].text))  # type: ignore[union-attr]


CONFIDENCE_FLOOR = 0.7


def check_image_subject(image_url: str, expected_subject: str) -> bool:
    try:
        b = _fetch_bytes(image_url)
        b64 = base64.b64encode(b).decode("ascii")
        result = _call_vision(b64, expected_subject)
        return bool(result["matches"]) and float(result["confidence"]) >= CONFIDENCE_FLOOR
    except Exception:
        return False  # fail-safe: if we can't verify, reject
