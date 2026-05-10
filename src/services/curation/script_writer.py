import json
from src.core.anthropic_client import AnthropicClient, extract_json
from src.core.logger import get_logger
from src.core.paths import REPO_ROOT
from src.pipelines.models import Script


log = get_logger("curation.script_writer")

STYLE_GUIDE_PATH = REPO_ROOT / "style" / "style-guide.md"


SYSTEM_PROMPT = """You are a script writer for Fact Jot, a faceless Instagram reels brand.

Style guide (always honour):
{style_guide}

You write a structured script as a JSON object with keys:
- title: <=70 chars
- hook: first 1.5s, <=12 words, must follow the hook formula
- beats: 4-7 items, each `{{ "text": str, "visual_brief": {{ ... }} }}`
- cta: one sentence, follows CTA convention
- citations: list of `{{ "claim": str, "source_url": str, "source_quote": str }}`

The `visual_brief` for each beat is critical — visuals are sourced from search engines (Wikimedia Commons, Pexels, Pixabay) using the brief, so vague briefs produce vague visuals. Format:

```
{{
  "subject": "<canonical noun phrase, 1-4 words, suitable as a search-engine query for a real photographable thing>",
  "queries": ["<2-4 word search query>", "<alternative phrasing>", "<more general fallback>"],
  "preferred_source": "video" | "image"
}}
```

**Subject rules:**
- Use a clean noun phrase that names a real, photographable entity. NOT a scene description.
- Prefer proper nouns (people, places, events, organisations, named objects) when the topic supports them. They resolve to Wikidata entities and unlock Wikimedia category sourcing.
- Disambiguate single-word entities. "Venus" alone is ambiguous (planet vs. plant vs. goddess); write "Venus planet" or "Venus flytrap" or "Venus de Milo".
- BAD: "Blue whale close-up, healthy skin, slow glide through water" / "1980s gas station with high price signs" / "Animated graphic of statistics rising"
- GOOD: "Blue whale" / "1980s gas station" / "Stock market chart"

**Queries rules:**
- 3-5 short search-engine queries (2-4 words each).
- First query is most specific; later queries broaden out.
- Avoid descriptive language ("close-up of", "vintage 1980s footage of"). Search engines tag content; they don't understand prose.

**Preferred source:**
- "video" for kinetic / atmospheric beats (motion, change, action).
- "image" for archival / specific / historical beats (named events, people, photographs).

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
    try:
        data = json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        log.error("script_json_parse_failed", error=str(e), preview=raw[:500])
        raise
    return Script.model_validate(data)
