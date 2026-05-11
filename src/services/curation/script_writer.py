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

Each beat carries a `scene_treatment` from a CLOSED set. This is YOU acting as art director: choosing how the asset enters the frame, not just what asset to fetch. The renderer wraps the sourced asset in the chosen treatment, so a mediocre stock image reads as deliberate when framed as evidence on a desk.

**The brand aesthetic is "case file"**: documents slide across the desk, polaroids drop in, stamps slam down, evidence accumulates. Be cinematic. Use Ken Burns sparingly — only when the asset is genuinely too good to dress up.

**Treatments (use these exact strings):**

- `polaroid` — for INTRODUCING a person, place, or specific object (someone's face, a landmark, a named thing). Photo wraps in a white border with tape, slides onto the desk with a settling rotation. Default for any beat that names a specific person.

- `evidence_slide` — for DOCUMENT-LIKE archival material (letters, charters, blueprints, scans, paintings, manuscripts). The asset slides in from off-canvas and stops in frame. Use for "official" or "documented" beats.

- `redacted_doc` — for SECRECY, COVER-UP, or HIDDEN INFORMATION beats. The beat text appears as a typewritten paragraph and black redaction bars sweep across key words. Pair with stories about classified info, government secrets, suppressed history.

- `stamp_reveal` — for VERDICTS, DEADLINES, OUTCOMES, or DATES that need to land hard ("CLASSIFIED", "1968", "DECLASSIFIED", "RESOLVED"). Asset shows underneath; the stamp rotates in with overshoot. Best on beat 3 or 4 where the punchline lives.

- `index_card` — for QUOTES, NUMBERS, or TIGHT FACTS. Typed monospaced text on a manila card. Use when the beat is the fact itself and the asset is decorative.

- `newsprint_clip` — for HISTORICAL EVENTS that were COVERED IN PRESS. Halftone-filtered image with a yellowed border, like a newspaper clipping pinned to the board. Use for crimes, scandals, disasters, public events.

- `archive_film` — for OLD FOOTAGE or VINTAGE atmosphere. Black-and-white film-strip frame around the asset. Use for pre-1970s context, retro feel.

- `map_pin` — for LOCATIONS. Asset displays alongside a map fragment with a push-pin drop. Use the FIRST time a place is named.

- `red_thread` — for CONNECTIONS BETWEEN BEATS. NEVER on beat 0 (nothing to connect to). Use when this beat ties back to the previous beat's subject (same person, same place, same date).

- `ken_burns` — the v1 fallback. Full-bleed asset with slow zoom. Reserve for when the asset is so striking it deserves the full frame.

**Picking rules:**
- Variety matters. Don't pick the same treatment for all four beats; mix at least 3 different treatments per script.
- Match the EMOTIONAL beat to the treatment, not the literal noun.
- Beat 0 introduces the subject — usually `polaroid` (person), `evidence_slide` (document), `map_pin` (place), or `newsprint_clip` (event).
- Beat 3 lands the consequence — often `stamp_reveal` or `redacted_doc`.

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
