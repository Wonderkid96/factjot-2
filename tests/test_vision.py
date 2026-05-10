from unittest.mock import patch
from src.services.verification.vision import check_image_subject


def test_vision_passes_for_matching_image():
    with patch("src.services.verification.vision._fetch_bytes", return_value=b"FAKE_IMG"):
        with patch("src.services.verification.vision._call_vision") as v:
            v.return_value = {"matches": True, "confidence": 0.9}
            ok = check_image_subject(image_url="https://x.jpg", expected_subject="Apollo 11")
    assert ok


def test_vision_rejects_low_confidence():
    with patch("src.services.verification.vision._fetch_bytes", return_value=b"FAKE_IMG"):
        with patch("src.services.verification.vision._call_vision") as v:
            v.return_value = {"matches": False, "confidence": 0.3}
            ok = check_image_subject(image_url="https://x.jpg", expected_subject="Apollo 11")
    assert not ok
