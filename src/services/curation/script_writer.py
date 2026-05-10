import json
from src.core.anthropic_client import AnthropicClient
from src.core.paths import REPO_ROOT
from src.pipelines.models import Script

STYLE_GUIDE_PATH = REPO_ROOT / "style" / "style-guide.md"


SYSTEM_PROMPT = """You are a script writer for Fact Jot, a faceless Instagram reels brand.

Style guide (always honour):
{style_guide}

You write a structured script as a JSON object with keys:
- title: <=70 chars
- hook: first 1.5s, <=12 words, must follow the hook formula
- beats: 4-7 items each {{ "text": str, "visual_brief": {{ "subject": str, "queries": [str, ...], "preferred_source": "video"|"image" }} }}
- cta: one sentence, follows CTA convention
- citations: list of {{ "claim": str, "source_url": str, "source_quote": str }}

Return ONLY the JSON. No prose around it.
"""


def _load_style_guide() -> str:
    return STYLE_GUIDE_PATH.read_text()


def _call_writer(system: str, user: str) -> str:
    return AnthropicClient().text(system=system, user=user)


def generate_script(topic: str, angle: str) -> Script:
    sys = SYSTEM_PROMPT.format(style_guide=_load_style_guide())
    user = f"Write a Fact Jot reel script about: {topic}\nAngle: {angle}\n\nReturn JSON only."
    raw = _call_writer(sys, user)
    data = json.loads(raw)
    return Script.model_validate(data)
