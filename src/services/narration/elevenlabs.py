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
        """Call the with-timestamps endpoint and return word-level alignment.

        ElevenLabs returns three parallel arrays under `alignment`:
          characters: list[str] (one char each)
          character_start_times_seconds: list[float]
          character_end_times_seconds: list[float]

        We group consecutive non-whitespace characters into words and return
        list[dict] with {"word": str, "start": float, "end": float} — the shape
        FactReel.tsx expects for narration-locked beat timing.
        """
        resp = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/" + self.voice_id + "/with-timestamps",
            headers={"xi-api-key": self.settings.elevenlabs_api_key},
            json={"text": text, "model_id": self.model_id},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        align = data.get("alignment") or data.get("normalized_alignment") or {}
        chars = align.get("characters", [])
        starts = align.get("character_start_times_seconds", [])
        ends = align.get("character_end_times_seconds", [])
        if not (len(chars) == len(starts) == len(ends)) or not chars:
            return []

        words: list[dict] = []
        cur_chars: list[str] = []
        cur_start: float | None = None
        prev_end: float = 0.0
        for ch, s, e in zip(chars, starts, ends):
            if ch.isspace():
                if cur_chars:
                    words.append({"word": "".join(cur_chars), "start": cur_start or 0.0, "end": prev_end})
                    cur_chars = []
                    cur_start = None
            else:
                if cur_start is None:
                    cur_start = float(s)
                cur_chars.append(ch)
                prev_end = float(e)
        if cur_chars:
            words.append({"word": "".join(cur_chars), "start": cur_start or 0.0, "end": prev_end})
        return words

    def synthesize(self, text: str, out_path: Path) -> NarrationResult:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path = out_path.with_suffix(".44k.mp3")
        raw_path.write_bytes(self._call_tts_api(text))
        self._resample_to_48khz(raw_path, out_path)
        raw_path.unlink(missing_ok=True)
        alignment = self._fetch_alignment(text, b"")
        return NarrationResult(audio_path=out_path, alignment=alignment)
