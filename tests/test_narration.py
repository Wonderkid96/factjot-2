from unittest.mock import patch
from src.services.narration.elevenlabs import ElevenLabsNarrator


def test_narrator_initialises():
    n = ElevenLabsNarrator()
    assert n.voice_id, "voice_id should be loaded from ELEVENLABS_VOICE env"


def test_narrator_writes_to_path(tmp_path):
    n = ElevenLabsNarrator()
    out = tmp_path / "n.mp3"
    with patch.object(n, "_call_tts_api", return_value=b"FAKE_MP3_BYTES"):
        with patch.object(n, "_resample_to_48khz", side_effect=lambda src, dst: dst.write_bytes(b"FAKE_48K")):
            with patch.object(n, "_fetch_alignment", return_value=[{"word": "hi", "start": 0.0, "end": 0.3}]):
                result = n.synthesize("hi", out)
    assert out.exists()
    assert result.alignment[0]["word"] == "hi"
