import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests
from elevenlabs.client import ElevenLabs

from src.core.config import Settings


@dataclass
class NarrationResult:
    audio_path: Path
    alignment: list[dict]


class ElevenLabsNarrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.voice_id = self.settings.elevenlabs_voice
        self.client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        self.model_id = "eleven_v3"

    def _call_tts_api(self, text: str) -> bytes:
        chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format="mp3_44100_128",
        )
        return b"".join(chunks)

    def _resample_to_48khz(self, src: Path, dst: Path) -> None:
        """Meta rejects 44.1kHz audio. Resample before muxing."""
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-ar", "48000", "-c:a", "libmp3lame", str(dst)],
            check=True,
            capture_output=True,
        )

    def _fetch_alignment(self, text: str, audio_bytes: bytes) -> list[dict]:
        """Call the alignment endpoint to get word timestamps."""
        resp = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/" + self.voice_id + "/with-timestamps",
            headers={"xi-api-key": self.settings.elevenlabs_api_key},
            json={"text": text, "model_id": self.model_id},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # Extract simple word-level alignment from char-level response
        return data.get("alignment", {}).get("characters", [])

    def synthesize(self, text: str, out_path: Path) -> NarrationResult:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path = out_path.with_suffix(".44k.mp3")
        raw_path.write_bytes(self._call_tts_api(text))
        self._resample_to_48khz(raw_path, out_path)
        raw_path.unlink(missing_ok=True)
        alignment = self._fetch_alignment(text, b"")
        return NarrationResult(audio_path=out_path, alignment=alignment)
