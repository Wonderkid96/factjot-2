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

- `redacted_doc` — bold typed paragraph on pure black. Selected words get inverter-matte redaction blocks that sweep in left-to-right (the words flip to black, the block reads as a redaction stamp). Use ONLY when the beat is about active CONCEALMENT — censorship, classified documents, sealed records, deliberately hidden information, cover-ups.

  **CRITICAL: unsolved ≠ secret.** A scientific mystery, an unexplained phenomenon, or an open historical question is NOT a redaction beat. Use `ken_burns` or `index_card` for those.

  - GOOD: "The CIA destroyed every copy of the report in 1973." (active destruction)
  - GOOD: "The pope's letter has been sealed in the Vatican archives for 200 years." (literal concealment)
  - GOOD: "Three witnesses signed NDAs and never spoke publicly again." (enforced silence)
  - BAD: "Scientists still can't explain why birds flee women." (mystery, NOT concealment — use `ken_burns`)
  - BAD: "The murder remains unsolved decades later." (open case, NOT cover-up — use `newsprint_clip`)
  - BAD: "Nobody knows what really started the fire." (unknown ≠ hidden — use `ken_burns`)

- `stamp_reveal` — full-bleed asset with a big bold text plate that rises up from the bottom and holds. ONLY use this when the beat contains a 4-digit year (e.g. "2009", "1968") or a punchy number — the renderer extracts a year/number for the plate. If your beat has no extractable year/number, DO NOT pick stamp_reveal.

- `index_card` — bold Archivo Black title text on pure black. The text IS the visual. Use when the beat is a tight standalone fact, a quote, or a number that should land without competing imagery.

- `newsprint_clip` — full-bleed asset with B&W halftone-dot grade. Reads as "press archival". Use for historical events covered in press, crimes, scandals, public disasters.

- `archive_film` — full-bleed asset, B&W with heavier grain. Use for pre-1970s context, retro/vintage atmosphere, or when the source footage is genuinely old.

- `map_pin` — full-bleed asset with a bottom-left LOCATION label slid in (eyebrow + place name). Use the FIRST time a specific place is named in the reel.

- `red_thread` — full-bleed colour, no special treatment. Use this for connection/callback beats where you want a clean visual that lets the narration carry the link.

- `ken_burns` — full-bleed colour with slow zoom. Identical to `polaroid` in current rendering; pick whichever name feels right for the beat.

**Picking rules — strict:**
- Variety matters. Don't pick the same treatment for all four beats; mix at least 3 different treatments per script.
- Match the EMOTIONAL beat to the treatment, not the literal noun.
- **`ken_burns` is the safe default.** If a beat doesn't unambiguously fit one of the specific treatments below, USE `ken_burns`. Don't pick a richer treatment just for variety — every pick should have a reason you can name in one sentence.
- `redacted_doc` ONLY when the beat is genuinely about secrecy, cover-up, classified info, suppression, or hidden facts. NOT for emphasis. NOT just because the previous beats were image-heavy.
- `stamp_reveal` ONLY when the beat contains a 4-digit year or a 3+ digit number you want to land. If no year/number, do not pick.
- `red_thread` ONLY for callback beats that explicitly tie back to an earlier beat's subject. NOT for "this is a connection in general".
- `archive_film` ONLY for pre-1970s content. Modern footage shouldn't be B&W-graded just for vibes.
- `index_card` ONLY when the beat is a tight quote, number, or fact that's stronger AS text than with an image. Use sparingly — defaults to text-on-black, which feels static if overused.
- Beat 0 introduces the subject — usually `polaroid` (person/place/object), `map_pin` (specific location), `newsprint_clip` (press-covered event), or `ken_burns` (default).
- Beat 3 lands the consequence. STOP picking `stamp_reveal` or `redacted_doc` here by default — pick whatever fits the actual content. `ken_burns` over a strong final asset is often the right call.

# RICH ANIMATIONS — OPTIONAL OVERLAY

Each beat can OPTIONALLY include an `animation` field that adds a rich
motion-graphic overlay on top of the base scene_treatment. ONLY emit this
field when the beat content unambiguously fits one of the named primitives.
If nothing clearly fits, OMIT the field entirely — the base treatment will
carry the beat fine on its own. Better to skip than to force.

**Available primitives:**

- `counter` — a big number that ticks up dramatically over ~2 seconds.
  Use this when the beat's punchline is a specific large quantity:
  casualty counts, distances, percentages, time durations, populations,
  money amounts. The number must be IN the beat text. Do NOT invent
  numbers the script doesn't already mention.

  Shape:
  ```
  "animation": {{
    "type": "counter",
    "from": 0,
    "to": 70000,
    "unit": "dead"           // optional suffix shown after the number
  }}
  ```

  Good examples:
  - Beat: "The blast killed seventy thousand people instantly."
    → `{{ "type": "counter", "from": 0, "to": 70000, "unit": "dead" }}`
  - Beat: "Mount Everest rises eight thousand eight hundred metres."
    → `{{ "type": "counter", "from": 0, "to": 8848, "unit": "metres" }}`
  - Beat: "Only 12 humans have walked on the moon."
    → `{{ "type": "counter", "from": 0, "to": 12, "unit": "humans" }}`

  Bad examples (do NOT emit):
  - Beat: "Yamaguchi survived both atomic bombings." → no specific number
  - Beat: "Many soldiers died in the trenches." → "many" is not a number
  - Beat: "He lived for over a year afterwards." → "over a year" is vague

**Rule of thumb:** if you cannot extract one exact integer from the beat
text, do not pick counter. Future primitives will follow the same rule —
the renderer pulls values from the script, never invents them.

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


VALID_ANIMATIONS = {"counter"}


def _scrub_animation(anim: dict | None, beat_text: str, beat_index: int) -> dict | None:
    """Validate the optional `animation` field. If it's malformed or its
    referenced value can't be cross-checked against the beat text, drop it
    rather than letting the renderer fail or invent a number.
    """
    if not anim or not isinstance(anim, dict):
        return None
    atype = anim.get("type")
    if atype not in VALID_ANIMATIONS:
        log.info("animation_unknown_type", beat_index=beat_index, got=atype)
        return None
    if atype == "counter":
        # Validate shape: from + to must be numeric, to > 0.
        try:
            from_val = int(anim.get("from", 0))
            to_val = int(anim["to"])
        except (KeyError, TypeError, ValueError):
            log.info("animation_counter_bad_shape", beat_index=beat_index)
            return None
        if to_val <= 0:
            return None
        # Cross-check: the `to` value MUST appear somewhere in the beat
        # text (digits, with optional commas). This is the "agent must
        # never invent numbers" guard — if the script doesn't say it,
        # the counter doesn't show it.
        beat_digits = beat_text.replace(",", "").replace(".", "")
        to_str = str(to_val)
        # Allow round-number matches too (e.g. "70,000" in text matches to=70000)
        if to_str not in beat_digits:
            # Try common spelled-out fallbacks: "seventy thousand" → 70000
            log.info("animation_counter_value_not_in_text",
                     beat_index=beat_index, to=to_val,
                     text_preview=beat_text[:80])
            return None
        unit = anim.get("unit")
        if unit is not None and not isinstance(unit, str):
            unit = None
        return {
            "type": "counter",
            "from": from_val,
            "to": to_val,
            "unit": unit,
        }
    return None


def _scrub_script(data: dict) -> dict:
    """Walk every voice-facing string and strip banned punctuation.

    Also validates `scene_treatment` per beat. If the writer omitted one or
    picked a treatment the renderer doesn't know, fall back to ken_burns so
    the renderer never has to handle a missing-or-unknown enum. Validates
    optional `animation` overlay shape per beat.
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
        # Validate the optional animation overlay.
        beat["animation"] = _scrub_animation(beat.get("animation"), beat.get("text", ""), idx)
    return data


def _format_recent_treatments(recent: list[list[str]] | None) -> str:
    if not recent:
        return ""
    lines = []
    for i, ts in enumerate(recent):
        lines.append(f"- Reel {i+1} ago: {' → '.join(ts)}")
    return (
        "\n# RECENT REEL HISTORY — AVOID REPETITION\n"
        "Your last few reels used these treatment sequences:\n"
        + "\n".join(lines)
        + "\n\nPick a DIFFERENT mix this time. If you're tempted to use a treatment "
          "that appears in 3+ of the last 5 reels, choose something else unless "
          "the beat content genuinely demands it (e.g. don't pick `redacted_doc` "
          "just because the last reel did; pick it only if the beat is about "
          "secrecy/cover-up/hidden info).\n"
    )


def generate_script(
    topic: str,
    angle: str,
    recent_treatments: list[list[str]] | None = None,
) -> Script:
    if os.getenv("FACTJOT_FROZEN") == "1":
        raise FrozenModeViolation(
            "generate_script() called while FACTJOT_FROZEN=1. Use the fixture's "
            "spec.json instead of regenerating, or drop --frozen if you really "
            "want to hit Anthropic."
        )
    sys = SYSTEM_PROMPT.format(style_guide=_load_style_guide())
    history = _format_recent_treatments(recent_treatments)
    user = (
        f"Write a Fact Jot reel script about: {topic}\n"
        f"Angle: {angle}\n"
        f"{history}\n"
        "Return JSON only."
    )
    raw = _call_writer(sys, user)
    try:
        data = json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        log.error("script_json_parse_failed", error=str(e), preview=raw[:500])
        raise
    data = _scrub_script(data)
    return Script.model_validate(data)
