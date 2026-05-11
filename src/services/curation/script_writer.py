import json
import os
from src.core.anthropic_client import AnthropicClient, extract_json
from src.core.logger import get_logger
from src.core.paths import REPO_ROOT
from src.pipelines.models import Script


log = get_logger("curation.script_writer")


class FrozenModeViolation(RuntimeError):
    """Raised when the script writer would be called while FACTJOT_FROZEN=1.

    Frozen mode means render-only against a fixture. Hitting Anthropic for a
    new script breaks that contract and burns credits.
    """

STYLE_GUIDE_PATH = REPO_ROOT / "style" / "style-guide.md"


SYSTEM_PROMPT = """You are a script writer for Fact Jot, a faceless Instagram reels brand.

Style guide (always honour):
{style_guide}

# HARD CONSTRAINTS — non-negotiable

**Length: target 30-40 seconds when narrated.**
ElevenLabs reads at ~150 words per minute, so the TOTAL script across hook + all beats + CTA must be **80-100 words**. Going over 110 makes the reel drag. Going under 70 leaves it feeling thin.

**Banned punctuation in shipping copy:** em dashes (—), en dashes (–), and ellipses (...). Use commas, full stops, or rewrite the sentence. This rule is from Toby's brand voice. If you find yourself reaching for an em dash, the sentence is structurally weak — rewrite it.

# JSON SCHEMA

Return a JSON object with these keys:
- `title`: <=60 chars, declarative, image-able. NOT a question.
- `hook`: 6-10 words. The first 1.5 seconds. Must STOP the thumb. See hook formula below.
- `topic_entity`: 1-3 word canonical proper noun for the WHOLE reel, OR null if abstract.
- `beats`: EXACTLY 4 items. Each item: `{{ "text": str, "visual_brief": {{ ... }}, "scene_treatment": str }}`. Beat text: 12-18 words.
- `cta`: 8-12 words. The closing line that lands the consequence or pattern. **Do NOT include "follow for more" or "follow fact jot" — that's appended automatically by the brand outro after your CTA.**
- `citations`: list of `{{ "claim": str, "source_url": str, "source_quote": str }}`.

# HOOK FORMULA

The hook is everything. If they don't stop scrolling in 1.5s, nothing else matters.

**Form:** a counterintuitive declarative claim, present tense, active voice. Image-able subject in the first 5 words. No question marks. No "Did you know". No setup.

**GOOD hooks (study these):**
- "Every horse runs on its middle finger."
- "The first photograph took 8 hours to expose."
- "Your blood is hotter than the desert."
- "JFK's Pulitzer wasn't even his to win."
- "Roman ruins live under a Belgrade glass floor."

**BAD hooks (rewrite if you produce these):**
- "Horses walk on a single fingertip, not a foot." (passive, descriptive)
- "Did you know horses walk on their fingers?" (question, banned phrase)
- "It's surprising what horses actually walk on." (no concrete subject, vague)

# topic_entity RULES

- The proper noun the entire reel revolves around. Used to pull archive footage of that subject across every beat.
- Examples:
  - "John F. Kennedy was the only US president to win a Pulitzer..." → "John F. Kennedy"
  - "The Johnstown Flood killed 2,209 people in 14 minutes..." → "Johnstown Flood"
  - "Blue whales rarely get cancer..." → "Blue whale"
  - "Quantum entanglement breaks classical intuition..." → null (abstract)
- Single proper noun preferred. "Apollo 11", not "Apollo 11 mission to the moon".

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

**Queries rules — progressively widening, search-engine-tag style:**
- Exactly 3 queries per beat: SPECIFIC → GENERAL → BROAD.
- Each query: 1-3 words, no prose, no descriptive adjectives, no time-of-day, no shot-type words.
- Stock and archive search engines tag images by keyword; "horse hoof" matches; "vintage close-up of a horse hoof in slow motion" matches nothing.
- BAD: ["Close-up of a horse's lower leg and hoof from the side", "Horse foot anatomy", "Horse"]
- GOOD: ["horse hoof", "horse leg", "horse"]
- BAD: ["Stunning vintage 1980s footage of a gas station with rising prices"]
- GOOD: ["1980s gas station", "gas station", "petrol pump"]

**Preferred source:**
- "video" for kinetic / atmospheric beats (motion, change, action).
- "image" for archival / specific / historical beats (named events, people, photographs).

# SCENE TREATMENT — DIRECT THE SHOT

Each beat carries a `scene_treatment` from a CLOSED set. You are the art director: pick HOW the beat plays cinematically, not just what asset to fetch.

**The brand aesthetic is "Netflix documentary"**: pure black backgrounds, full-bleed footage, subtle Ken Burns, cinematic colour grading, bold typography on black. No paper, no desks, no stamps slamming down — clean, gripping, restrained. Think *Wild Wild Country*, *The Vow*, *Don't F**k With Cats*.

**Treatments (use these EXACT strings):**

- `polaroid` — full-bleed colour footage of a person, place, or specific object. Slow Ken Burns + vignette. Default for any beat naming a specific person. (Name kept for back-compat; there is no actual polaroid border any more.)

- `evidence_slide` — full-bleed asset with WARM SEPIA grade. Use for archival material (letters, paintings, scans, manuscripts) where you want a "this is old" feel.

- `redacted_doc` — bold typed paragraph on pure black. Selected words get inverter-matte redaction blocks that sweep in left-to-right (the words flip to black, the block reads as a redaction stamp). Use for secrecy, cover-up, hidden info, declassified material, things-that-should-not-be-known beats.

- `stamp_reveal` — full-bleed asset with a big bold text plate that rises up from the bottom and holds. ONLY use this when the beat contains a 4-digit year (e.g. "2009", "1968") or a punchy number — the renderer extracts a year/number for the plate. If your beat has no extractable year/number, DO NOT pick stamp_reveal.

- `index_card` — bold Archivo Black title text on pure black. The text IS the visual. Use when the beat is a tight standalone fact, a quote, or a number that should land without competing imagery.

- `newsprint_clip` — full-bleed asset with B&W halftone-dot grade. Reads as "press archival". Use for historical events covered in press, crimes, scandals, public disasters.

- `archive_film` — full-bleed asset, B&W with heavier grain. Use for pre-1970s context, retro/vintage atmosphere, or when the source footage is genuinely old.

- `map_pin` — full-bleed asset with a bottom-left LOCATION label slid in (eyebrow + place name). Use the FIRST time a specific place is named in the reel.

- `red_thread` — full-bleed colour, no special treatment. Use this for connection/callback beats where you want a clean visual that lets the narration carry the link.

- `ken_burns` — full-bleed colour with slow zoom. Identical to `polaroid` in current rendering; pick whichever name feels right for the beat.

**Picking rules:**
- Variety matters. Don't pick the same treatment for all four beats; mix at least 3 different treatments per script.
- Match the EMOTIONAL beat to the treatment, not the literal noun.
- Beat 0 introduces the subject — usually `polaroid` (person), `map_pin` (place), or `index_card` (a sharp number).
- Use `stamp_reveal` ONLY if you put a year or number in the beat text. Otherwise it falls back to a generic plate and reads as random.

Return ONLY the JSON. No prose around it.
"""


VALID_TREATMENTS = {
    "polaroid", "evidence_slide", "redacted_doc", "stamp_reveal",
    "index_card", "newsprint_clip", "archive_film", "map_pin",
    "red_thread", "ken_burns",
}


def _load_style_guide() -> str:
    return STYLE_GUIDE_PATH.read_text()


def _call_writer(system: str, user: str) -> str:
    return AnthropicClient().text(system=system, user=user)


def _strip_banned_punctuation(text: str) -> str:
    """Sonnet sometimes leaks em dashes / en dashes / ellipses despite the prompt.
    Final defence: replace them post-generation. Em/en dash → comma. Ellipsis → full stop.
    """
    return (
        text.replace("—", ",")
            .replace("–", ",")
            .replace("…", ".")
            .replace("...", ".")
    )


def _scrub_script(data: dict) -> dict:
    """Walk every voice-facing string and strip banned punctuation.

    Also validates `scene_treatment` per beat. If the writer omitted one or
    picked a treatment the renderer doesn't know, fall back to ken_burns so
    the renderer never has to handle a missing-or-unknown enum.
    """
    for key in ("hook", "cta", "title"):
        if key in data and isinstance(data[key], str):
            data[key] = _strip_banned_punctuation(data[key])
    for idx, beat in enumerate(data.get("beats", [])):
        if isinstance(beat.get("text"), str):
            beat["text"] = _strip_banned_punctuation(beat["text"])
        treatment = beat.get("scene_treatment")
        if treatment not in VALID_TREATMENTS:
            log.info("scene_treatment_fallback", beat_index=idx, got=treatment)
            beat["scene_treatment"] = "ken_burns"
        # red_thread on beat 0 has nothing to connect to — push to polaroid.
        if idx == 0 and beat["scene_treatment"] == "red_thread":
            beat["scene_treatment"] = "polaroid"
    return data


def generate_script(topic: str, angle: str) -> Script:
    if os.getenv("FACTJOT_FROZEN") == "1":
        raise FrozenModeViolation(
            "generate_script() called while FACTJOT_FROZEN=1. Use the fixture's "
            "spec.json instead of regenerating, or drop --frozen if you really "
            "want to hit Anthropic."
        )
    sys = SYSTEM_PROMPT.format(style_guide=_load_style_guide())
    user = f"Write a Fact Jot reel script about: {topic}\nAngle: {angle}\n\nReturn JSON only."
    raw = _call_writer(sys, user)
    try:
        data = json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        log.error("script_json_parse_failed", error=str(e), preview=raw[:500])
        raise
    data = _scrub_script(data)
    return Script.model_validate(data)
