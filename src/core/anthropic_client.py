from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings


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
