import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests
from elevenlabs.client import ElevenLabs

from src.core.config import Settings


# Speed multiplier applied via ffmpeg atempo (preserves pitch). 1.0 = no
# change, matches V1's behaviour (V1 doesn't post-process speed at all).
# The 1.1 we tried earlier made the same voice sound rushed + dramatic; V1's
# natural pace reads as Netflix-doc-narrator measured.
NARRATION_SPEED = 1.0


class FrozenModeViolation(RuntimeError):
    """Raised when ElevenLabs would be called while FACTJOT_FROZEN=1.

    The frozen runner contract is: no paid APIs. If this fires, the pipeline
    is leaking through frozen mode somewhere and would otherwise burn credits.
    """


@dataclass
class NarrationResult:
    audio_path: Path
    alignment: list[dict]


class ElevenLabsNarrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.voice_id = self.settings.elevenlabs_voice
        self.client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        # V1's "curious" defaults — measured, Netflix-doc-narrator pace.
        # V1 routes by tone (shocking / sober / wholesome / curious=default).
        # Bot-2 used "shocking" (style 0.42, stab 0.38) which read as rushed
        # and emotionally over-pitched even though the prompt was identical;
        # V1's default tone is "curious" and it sounds more like a real
        # documentary narrator. See Insta-bot/src/render/tts_engine.py:638-641.
        self.model_id = "eleven_turbo_v2_5"
        self.voice_settings = {
            "stability": 0.52,           # curious tone — V1 fallback
            "similarity_boost": 0.82,
            "style": 0.22,               # curious tone — V1 fallback
            "use_speaker_boost": True,
        }
        self.speed = NARRATION_SPEED

    def _call_tts_api(self, text: str) -> bytes:
        chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format="mp3_44100_128",
            voice_settings=self.voice_settings,
        )
        return b"".join(chunks)

    def _resample_to_48khz(self, src: Path, dst: Path) -> None:
        """Resample to 48kHz AND apply atempo for narration speed.

        Meta rejects 44.1kHz audio. atempo preserves pitch when speeding up,
        which is what we want; -filter:a runs both stages in one ffmpeg pass.
        """
        filters = [f"atempo={self.speed}"] if self.speed != 1.0 else []
        cmd = ["ffmpeg", "-y", "-i", str(src), "-ar", "48000"]
        if filters:
            cmd += ["-filter:a", ",".join(filters)]
        cmd += ["-c:a", "libmp3lame", str(dst)]
        subprocess.run(cmd, check=True, capture_output=True)

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
            json={
                "text": text,
                "model_id": self.model_id,
                "voice_settings": self.voice_settings,
            },
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

        # The MP3 we hand to the renderer was atempo'd by self.speed, so the
        # alignment seconds need to be divided by the same factor to stay
        # aligned with the actual playback.
        if self.speed != 1.0:
            words = [
                {"word": w["word"],
                 "start": w["start"] / self.speed,
                 "end": w["end"] / self.speed}
                for w in words
            ]
        return words

    def synthesize(self, text: str, out_path: Path) -> NarrationResult:
        if os.getenv("FACTJOT_FROZEN") == "1":
            raise FrozenModeViolation(
                "ElevenLabsNarrator.synthesize() called while FACTJOT_FROZEN=1. "
                "Frozen mode is the contract that says 'no paid APIs tonight'. "
                "Either drop --frozen, or fix the call site to reuse the fixture audio."
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path = out_path.with_suffix(".44k.mp3")
        raw_path.write_bytes(self._call_tts_api(text))
        self._resample_to_48khz(raw_path, out_path)
        raw_path.unlink(missing_ok=True)
        alignment = self._fetch_alignment(text, b"")
        return NarrationResult(audio_path=out_path, alignment=alignment)
