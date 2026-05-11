import contextlib
import functools
import http.server
import json
import socket
import socketserver
import subprocess
import threading
from pathlib import Path
from src.core.paths import REMOTION_DIR
from src.pipelines.models import Script, MediaSet


WORDS_PER_CAPTION_CHUNK = 5   # 5 keeps chunks on screen long enough that text swaps don't read as flicker. Below 4 reads jumpy.
TITLE_HOLD_SECONDS = 2.5      # Hold the hook on screen before narration starts (Toby's request, v1 used 1.5)
# MP3 encoding adds a small latency that alignment timestamps don't account for —
# raw alignment says "word starts at 1.20s" but the MP3 plays it at 1.40s. We display
# captions a touch EARLIER so they catch up to the encoded audio. Borrowed from
# ViralContent-Factory's SYNC_OFFSET dial (phase2.py).
SUBTITLE_SYNC_OFFSET_SECONDS = -0.2
# Brand outro spoken at the end of every reel. Appended to the narration text
# so the voice says it; FactReel renders it as its own Sequence with the big wordmark.
OUTRO_TEXT = "Follow fact jot for more facts."
# Tail buffer in seconds AFTER the last narrated word, so the video doesn't slam shut.
TAIL_BUFFER_SECONDS = 1.2


KARAOKE_LEAD_FRAMES = 2          # ~67ms lead on word highlight (audio lags visual perception)
EMPHASIS_PATTERN = ("0","1","2","3","4","5","6","7","8","9")

# Words that should be SPOKEN by the narrator but NOT rendered in the caption.
# Brand-name avoidance: when the outro is "Follow fact jot for more facts", the
# big factjot wordmark animates in at the same time — having "fact jot" in the
# caption AND as the logo reads as the brand being shouted twice. We keep the
# audio intact and just suppress these words from the karaoke captions.
SUPPRESSED_CAPTION_WORDS = {"fact", "jot", "factjot"}


def _is_suppressed(word: str) -> bool:
    """True if a word's spoken text should be hidden from captions.
    Strips trailing punctuation before matching.
    """
    stripped = word.lower().rstrip(".,!?:;\"'")
    return stripped in SUPPRESSED_CAPTION_WORDS


def _strip_suppressed_from_chunks(chunks: list[dict]) -> list[dict]:
    """Remove suppressed words from each chunk's word list AND chunk text.

    Chunks whose word lists become empty after filtering are dropped entirely
    (they'd render as empty captions otherwise). Chunk start/end frames are
    re-derived from the surviving words so the karaoke window still aligns
    with what's left on screen.
    """
    out: list[dict] = []
    for c in chunks:
        kept = [w for w in c.get("words", []) if not _is_suppressed(w["text"])]
        if not kept:
            continue
        out.append({
            "text": " ".join(w["text"] for w in kept),
            "start_frame": kept[0]["start_frame"],
            "end_frame": kept[-1]["end_frame"],
            "words": kept,
        })
    return out


def _has_digit(word: str) -> bool:
    """True if the word contains any digit — used to flag stat/year emphasis."""
    return any(c in EMPHASIS_PATTERN for c in word)


def _chunks_from_alignment(words: list[dict], fps: int, f) -> list[dict]:
    """Group an alignment slice into chained caption chunks.

    Each chunk holds 1-WORDS_PER_CAPTION_CHUNK words of spoken text. Chunks
    CLOSE on natural phrase boundaries (`.`, `,`, `;`, `:`, `?`, `!`) so
    captions don't break mid-clause.

    Chained: each chunk's `end_frame` extends to the NEXT chunk's
    `start_frame` so there is no gap on screen between captions — eliminates
    the flicker that comes from ElevenLabs silences between words.

    Per-word entries include:
      - text:        the spoken word
      - start_frame: f(start) - KARAOKE_LEAD_FRAMES (highlight leads audio)
      - end_frame:   f(end)
      - emphasis:    True if the word contains a digit (stats, years)

    Last word's `end_frame` is held to the chunk's end so the highlight
    doesn't snap back to white during the chain-extension.
    """
    # Only break on TERMINAL punctuation. Commas split mid-clause into
    # micro-chunks that read as flicker (e.g. "Three days later," then
    # "the second bomb" then "fell." — three quick swaps in 2s).
    BREAK_CHARS = (".", "?", "!")
    raw_chunks: list[dict] = []
    cur: list[dict] = []

    def flush() -> None:
        if not cur:
            return
        words_out = []
        for w in cur:
            lead = max(0, f(float(w["start"])) - KARAOKE_LEAD_FRAMES)
            words_out.append({
                "text": w["word"],
                "start_frame": lead,
                "end_frame": f(float(w["end"])),
                "emphasis": _has_digit(w["word"]),
            })
        raw_chunks.append({
            "text": " ".join(w["word"] for w in cur),
            "start_frame": f(float(cur[0]["start"])),
            "end_frame": f(float(cur[-1]["end"])),
            "words": words_out,
        })
        cur.clear()

    for w in words:
        cur.append(w)
        ends_phrase = w["word"].rstrip().endswith(BREAK_CHARS)
        if ends_phrase or len(cur) >= WORDS_PER_CAPTION_CHUNK:
            flush()
    flush()

    # Chain: extend each chunk's end_frame to one frame before the next chunk
    # so the caption stays on screen continuously through ElevenLabs silences.
    for i in range(len(raw_chunks) - 1):
        next_start = raw_chunks[i + 1]["start_frame"]
        raw_chunks[i]["end_frame"] = max(raw_chunks[i]["end_frame"], next_start - 1)
        # Hold the last word's highlight through the extension too
        if raw_chunks[i]["words"]:
            raw_chunks[i]["words"][-1]["end_frame"] = raw_chunks[i]["end_frame"]

    return raw_chunks


def _compute_timeline(script, alignment, fps: int = 30) -> dict:
    """Build an ABSOLUTE-frame timeline for the whole reel.

    `alignment` is a single list of `{word, start, end}` covering the
    concatenated narration `hook + beats + cta` in order. Every frame value
    in the returned timeline is in audio-clock time — frame 0 = start of
    narration. The composition just reads these and does no offset math.

    Returns:
        {
          "hook":  {start_frame, end_frame},
          "beats": [{start_frame, end_frame, chunks: [...]}, ...],
          "cta":   {start_frame, end_frame},
          "total_frames": int,
        }
    """
    beats = script.beats
    hook_words = len(script.hook.split()) if script.hook else 0
    cta_words = len(script.cta.split()) if script.cta else 0
    outro_words = len(OUTRO_TEXT.split())

    if not alignment:
        # Fallback: even split over 60s
        per = 60 / max(len(beats), 1)
        beat_dicts = []
        for i, b in enumerate(beats):
            sf, ef = int(i * per * fps), int((i + 1) * per * fps)
            beat_dicts.append({
                "start_frame": sf,
                "end_frame": ef,
                "chunks": [{"text": b.text, "start_frame": sf, "end_frame": ef}],
            })
        return {
            "hook": {"start_frame": 0, "end_frame": int(1.5 * fps)},
            "beats": beat_dicts,
            "cta": {"start_frame": int(60 * fps), "end_frame": int(62 * fps), "chunks": []},
            "outro": {"start_frame": int(62 * fps), "end_frame": int(64 * fps), "chunks": []},
            "total_frames": int(65 * fps),
            "narration_offset_frames": int(TITLE_HOLD_SECONDS * fps),
        }

    # All timestamps from alignment are in audio-clock seconds (0 = start of
    # narration audio). We offset everything by TITLE_HOLD so the hook gets a
    # silent beat before the voice kicks in. Plus SUBTITLE_SYNC_OFFSET to
    # compensate for MP3 encoding latency.
    title_hold = TITLE_HOLD_SECONDS

    def f(t: float) -> int:
        return max(0, int((t + title_hold + SUBTITLE_SYNC_OFFSET_SECONDS) * fps))

    # Hook window — first `hook_words` words of alignment.
    hook_start = float(alignment[0]["start"]) if alignment else 0.0
    hook_end = float(alignment[hook_words - 1]["end"]) if hook_words and hook_words <= len(alignment) else 0.0

    # Beat windows — consume each beat's word count from the alignment.
    # Build chunks DIRECTLY from alignment so chunk text and chunk timing
    # come from the same source — eliminates any drift when beat.text.split()
    # disagrees with ElevenLabs's tokenisation (contractions, punctuation,
    # hyphens). Each chunk also carries a `words[]` array with per-word
    # timing so the renderer can highlight the spoken word inside the chunk.
    beat_dicts: list[dict] = []
    word_idx = hook_words
    for b in beats:
        beat_words = b.text.split()
        n = len(beat_words)
        if n == 0 or word_idx >= len(alignment):
            beat_dicts.append({"start_frame": f(hook_end), "end_frame": f(hook_end), "chunks": []})
            continue

        end_idx = min(word_idx + n - 1, len(alignment) - 1)
        beat_align = alignment[word_idx : end_idx + 1]
        beat_start = float(beat_align[0]["start"])
        beat_end = float(beat_align[-1]["end"]) + 0.15  # tiny breath

        chunks: list[dict] = _chunks_from_alignment(beat_align, fps, f)

        beat_dicts.append({
            "start_frame": f(beat_start),
            "end_frame": f(beat_end),
            "chunks": chunks,
        })
        word_idx = end_idx + 1

    # CTA window — `cta_words` words AFTER beats and BEFORE outro.
    # Outro window — last `outro_words` words.
    outro_word_start = max(0, len(alignment) - outro_words)
    cta_chunks: list[dict] = []
    if cta_words and word_idx < outro_word_start:
        cta_start = float(alignment[word_idx]["start"])
        cta_end_idx = min(word_idx + cta_words - 1, outro_word_start - 1)
        cta_end = float(alignment[cta_end_idx]["end"]) + 0.2
        cta_chunks = _chunks_from_alignment(alignment[word_idx : cta_end_idx + 1], fps, f)
    else:
        cta_start = float(alignment[max(0, outro_word_start - 1)]["end"]) if alignment else 0.0
        cta_end = cta_start + 1.0

    outro_chunks: list[dict] = []
    if outro_words and outro_word_start < len(alignment):
        outro_start = float(alignment[outro_word_start]["start"])
        outro_end = float(alignment[-1]["end"]) + 0.3
        outro_chunks = _chunks_from_alignment(alignment[outro_word_start:], fps, f)
        # The brand name ("fact jot") is part of the SPOKEN outro but should
        # NOT appear in captions — the big factjot wordmark animates in over
        # the outro, so caption + logo would read the brand twice.
        outro_chunks = _strip_suppressed_from_chunks(outro_chunks)
    else:
        outro_start = cta_end
        outro_end = outro_start + 1.5

    # Cross-chunk chaining — extend the END of every chunk to the START of
    # the next chunk in playback order, so captions never blink off between
    # chunks (within-beat, beat-to-beat, beat-to-CTA, CTA-to-outro).
    # Build the in-order chunk list, then chain it.
    ordered_chunks: list[dict] = []
    for bd in beat_dicts:
        ordered_chunks.extend(bd.get("chunks") or [])
    ordered_chunks.extend(cta_chunks)
    ordered_chunks.extend(outro_chunks)
    for i in range(len(ordered_chunks) - 1):
        next_start = ordered_chunks[i + 1]["start_frame"]
        if ordered_chunks[i]["end_frame"] < next_start - 1:
            ordered_chunks[i]["end_frame"] = next_start - 1
            # Hold the last word's highlight through the extension
            if ordered_chunks[i].get("words"):
                ordered_chunks[i]["words"][-1]["end_frame"] = ordered_chunks[i]["end_frame"]

    # total_frames must NOT use f() — f() bakes in SUBTITLE_SYNC_OFFSET_SECONDS
    # which is a negative caption-display nudge, not audio-clock truth.
    # Compose directly from title_hold + audio length + tail.
    audio_end = float(alignment[-1]["end"]) if alignment else 60.0
    total_frames = int((title_hold + audio_end + TAIL_BUFFER_SECONDS) * fps)

    return {
        "hook": {"start_frame": 0, "end_frame": f(hook_end)},
        "beats": beat_dicts,
        "cta": {"start_frame": f(cta_start), "end_frame": f(cta_end), "chunks": cta_chunks},
        "outro": {"start_frame": f(outro_start), "end_frame": f(outro_end), "chunks": outro_chunks},
        "total_frames": total_frames,
        "narration_offset_frames": int(title_hold * fps),
    }


@contextlib.contextmanager
def _serve_dir(directory: Path):
    """Spin up a quiet HTTP server on a free port serving `directory`.

    Remotion's renderer only fetches assets via http(s) URLs (file:// rejected,
    --public-dir was unreliable in 4.0.x). A tiny stdlib HTTP server is the
    most robust bridge: serve the run dir, pass http://localhost:<port>/<name>
    paths in the spec, shut down on exit.
    """
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))

    # Silence the per-request log spam
    handler.log_message = lambda *args, **kwargs: None  # type: ignore[method-assign]

    # Bind to port 0 → OS picks a free one
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()


def _to_url(p: Path | str | None, base_url: str, run_dir: Path) -> str | None:
    """Convert a run-dir asset path into an HTTP URL served by the local server."""
    if p is None:
        return None
    p = Path(p)
    try:
        rel = p.resolve().relative_to(run_dir.resolve())
    except ValueError:
        # Path isn't under the run dir; best-effort use its basename
        rel = Path(p.name)
    return f"{base_url}/{rel.as_posix()}"


def _derive_kicker(script) -> str:
    """Derive the top-right kicker label from script content.

    Rough category map keyed on substrings in the script title + topic_entity.
    Falls back to "FACT". Category-aware curation is queued as a separate
    enhancement; this is the placeholder so chrome lays out correctly today.
    """
    haystack = " ".join(filter(None, [
        getattr(script, "title", "") or "",
        getattr(script, "topic_entity", "") or "",
    ])).lower()
    categories = (
        ("SPACE",   ("apollo", "nasa", "rocket", "satellite", "mars", "moon", "saturn", "galaxy")),
        ("NATURE",  ("whale", "shark", "lion", "tiger", "plant", "ocean", "jungle", "forest", "bird")),
        ("HISTORY", ("century", "ancient", "medieval", "roman", "egypt", "war", "atomic", "bomb",
                     "kennedy", "hitler", "napoleon", "yamaguchi", "hiroshima", "nagasaki",
                     "byzantine", "viking", "pharaoh", "dynasty")),
        ("SCIENCE", ("quantum", "particle", "physics", "chemistry", "neuron", "dna", "genome",
                     "atom", "molecule", "relativity")),
        ("HUMANITY",("survivor", "tragedy", "disaster", "rescue", "miracle")),
    )
    for label, keys in categories:
        if any(k in haystack for k in keys):
            return label
    return "FACT"


def build_video_spec(
    script: Script,
    media: MediaSet,
    composition_id: str,
    base_url: str | None = None,
    run_dir: Path | None = None,
) -> dict:
    """Build the JSON contract Remotion consumes.

    If `base_url` + `run_dir` are given, asset paths are rewritten to HTTP URLs
    served by a local helper. Without them paths stay as-is — useful for unit tests.
    """
    asset_by_beat = {a.beat_index: a for a in media.assets}
    timeline = _compute_timeline(script, media.narration_alignment)
    beat_data = timeline["beats"]
    narration = media.narration_audio

    def asset_url(p: Path | str | None) -> str | None:
        if base_url and run_dir:
            return _to_url(p, base_url, run_dir)
        return str(p) if p else None

    # Brand intro overlay (ProRes 4444 with alpha). Pipeline copies the file
    # into the run dir as `intro.mov` if available; if not, render skips it.
    intro_in_run = run_dir / "intro.mov" if run_dir else None
    intro_url = asset_url(intro_in_run) if intro_in_run and intro_in_run.exists() else None

    # Background music — V1's default.mp3 sits at 20% volume under the VO.
    music_in_run = run_dir / "music.mp3" if run_dir else None
    music_url = asset_url(music_in_run) if music_in_run and music_in_run.exists() else None

    # V1 film-grain overlay — screen-blended at ~65% opacity per V1's
    # reel_composer.py default. Replaces the SVG fractalNoise approach.
    grit_in_run = run_dir / "grit.mov" if run_dir else None
    grit_url = asset_url(grit_in_run) if grit_in_run and grit_in_run.exists() else None

    # Optional ambient background — single curated loop in brand/ambient/
    # served at low opacity between desk and scenes. Falls through silently
    # if no file exists, so reels render fine without one.
    ambient_in_run = run_dir / "ambient.mov" if run_dir else None
    ambient_url = asset_url(ambient_in_run) if ambient_in_run and ambient_in_run.exists() else None

    return {
        "composition": composition_id,
        "title": script.title,
        "hook": script.hook,
        "cta": script.cta,
        # Short uppercase chip rendered top-right next to the wordmark.
        # Defaults to "FACT" — category-aware derivation is queued under
        # gotchas-transfer P2 (script topic → category map).
        "kicker": _derive_kicker(script),
        "narration_audio": asset_url(narration),
        "intro_overlay": intro_url,
        "music_audio": music_url,
        "grit_overlay": grit_url,
        "ambient_overlay": ambient_url,
        "alignment": media.narration_alignment,
        # All frame values below are ABSOLUTE — relative to start of the VIDEO,
        # which begins with a title-hold before narration. narration_offset_frames
        # is how long to delay the audio Sequence so the hook can land first.
        "hook_window": timeline["hook"],
        "cta_window": timeline["cta"],
        "outro_window": timeline["outro"],
        "outro_text": OUTRO_TEXT,
        "total_frames": timeline["total_frames"],
        "narration_offset_frames": timeline["narration_offset_frames"],
        "beats": [
            {
                "text": b.text,
                "start_frame": beat_data[i]["start_frame"],
                "end_frame": beat_data[i]["end_frame"],
                "chunks": beat_data[i]["chunks"],
                # CaseFileReel uses scene_treatment to pick which case-file scene
                # component renders this beat (polaroid, evidence_slide, etc.).
                # FactReel ignores the field — it renders every beat the same way.
                "scene_treatment": getattr(b, "scene_treatment", "ken_burns"),
                "asset": {
                    "path": asset_url(asset_by_beat[i].local_path) if i in asset_by_beat else None,
                    "source": asset_by_beat[i].provider if i in asset_by_beat else None,
                },
            }
            for i, b in enumerate(script.beats)
        ],
    }


def render_via_remotion(script: Script, media: MediaSet, out_path: Path, composition_id: str) -> Path:
    """Render the FactReel composition to MP4.

    Spins up a local HTTP server serving the run directory; rewrites all asset
    paths in the spec to http URLs so Remotion's renderer can fetch them.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run_dir = out_path.parent
    spec_path = out_path.with_suffix(".spec.json")

    with _serve_dir(run_dir) as base_url:
        spec_path.write_text(json.dumps(build_video_spec(script, media, composition_id, base_url=base_url, run_dir=run_dir)))
        cmd = [
            "npx", "remotion", "render",
            composition_id,
            str(out_path),
            "--props", str(spec_path),
            "--config", "remotion.config.ts",
        ]
        result = subprocess.run(cmd, cwd=REMOTION_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Remotion render failed: {result.stderr}")
    return out_path


def render_still_via_remotion(composition_id: str, props: dict, out_path: Path) -> Path:
    """Render a single PNG frame (thumbnail or story tile) via local HTTP server."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run_dir = out_path.parent
    spec_path = out_path.with_suffix(".props.json")

    with _serve_dir(run_dir) as base_url:
        if isinstance(props.get("frame_path"), str):
            props = {**props, "frame_path": _to_url(props["frame_path"], base_url, run_dir)}
        spec_path.write_text(json.dumps(props))
        cmd = [
            "npx", "remotion", "still",
            composition_id,
            str(out_path),
            "--props", str(spec_path),
            "--config", "remotion.config.ts",
        ]
        result = subprocess.run(cmd, cwd=REMOTION_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Remotion still failed: {result.stderr}")
    return out_path
