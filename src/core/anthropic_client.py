import re
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings


_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def extract_json(text: str) -> str:
    """Pull JSON out of an LLM response that may include markdown fences or prose.

    LLMs frequently wrap structured output in ```json ... ``` or add a
    "Here is the JSON:" preamble. Strict json.loads() on the raw response
    fails. This helper strips fences, then locates the outer-most JSON
    array/object and returns just that span.
    """
    if not text:
        return text

    # Strip markdown code fence if present
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1)

    text = text.strip()

    # Already starts with JSON? Done.
    if text.startswith("{") or text.startswith("["):
        return text

    # Find an outer-most array or object
    for start_char, end_char in (("[", "]"), ("{", "}")):
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end > start:
            return text[start : end + 1]

    # No JSON-looking content; return as-is so json.loads raises a clear error
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
