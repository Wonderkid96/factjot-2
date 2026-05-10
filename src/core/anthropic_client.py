import json
import re
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings


_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def extract_json(text: str) -> str:
    """Pull the first JSON document out of an LLM response.

    Handles common LLM wrapping styles:
    - plain JSON
    - markdown ```json ... ``` fence
    - prose preamble then JSON
    - JSON then trailing prose / extra content (raw_decode stops cleanly)

    Uses json.JSONDecoder.raw_decode which parses one balanced JSON value and
    reports where parsing stopped — robust to trailing garbage that would
    otherwise trip a naive find-first-/find-last brace approach.
    """
    if not text:
        return text

    # Strip markdown code fence if present
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1)

    text = text.strip()

    # Walk from each candidate start char; first parse-success wins
    decoder = json.JSONDecoder()
    for i, c in enumerate(text):
        if c not in "{[":
            continue
        try:
            _obj, end = decoder.raw_decode(text[i:])
            return text[i : i + end]
        except json.JSONDecodeError:
            continue

    # No parseable JSON found; return as-is so caller's json.loads raises a clear error
    return text


class AnthropicClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model_default = "claude-sonnet-4-6"
        self.model_judge = "claude-opus-4-7"
        self.model_vision = "claude-haiku-4-5-20251001"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def text(
        self,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int = 4096,
        cache_system: bool = True,
    ) -> str:
        """Single-turn text call. System block can be marked for caching."""
        sys_block: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if cache_system:
            sys_block[0]["cache_control"] = {"type": "ephemeral"}
        msg = self.client.messages.create(
            model=model or self.model_default,
            max_tokens=max_tokens,
            system=sys_block,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text  # type: ignore[union-attr]
