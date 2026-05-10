import json
import os
import re
import subprocess
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import Settings
from src.core.logger import get_logger


log = get_logger("core.anthropic_client")


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


def _use_local_agent() -> bool:
    """Toby's iteration mode: shell out to `claude -p` instead of hitting the API.

    Set USE_LOCAL_AGENT=true (or 1/yes) for free testing via the local Claude
    subscription. Default off — production runs hit the API directly.
    """
    return os.environ.get("USE_LOCAL_AGENT", "").lower() in ("true", "1", "yes")


def _call_local_agent(system: str, user: str, max_tokens: int = 4096) -> str:
    """Run a prompt via the local `claude -p` CLI. Uses Toby's subscription auth.

    System and user prompts are joined with a separator. `--max-turns 1`
    prevents the agent from iterating with tools — we only want one answer.
    """
    full_prompt = f"{system}\n\n---\n\n{user}" if system else user
    cmd = [
        "claude",
        "-p",
        "--max-turns", "1",
        "--allow-dangerously-skip-permissions",
        full_prompt,
    ]
    log.info("local_agent_call", prompt_chars=len(full_prompt))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed (code {result.returncode}): {result.stderr[:500]}")
    return result.stdout.strip()


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
        """Single-turn text call. System block can be marked for caching.

        When USE_LOCAL_AGENT=true, routes to `claude -p` (Toby's subscription).
        Otherwise hits the Anthropic API directly. Local-agent mode bypasses
        prompt caching (no equivalent on the CLI).
        """
        if _use_local_agent():
            return _call_local_agent(system, user, max_tokens=max_tokens)

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
