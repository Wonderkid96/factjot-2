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


WORDS_PER_CAPTION_CHUNK = 3   # Punchier rhythm, TikTok-standard. Lower than 4-word chunks reads faster on small screens.
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
            "cta": {"start_frame": int(60 * fps), "end_frame": int(62 * fps)},
            "outro": {"start_frame": int(62 * fps), "end_frame": int(64 * fps)},
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

    # Beat windows — `hook_words` to (len(alignment) - cta_words). For each beat,
    # consume its word count off the front. Build chunks of ~4 words.
    beat_dicts: list[dict] = []
    word_idx = hook_words
    for b in beats:
        beat_words = b.text.split()
        n = len(beat_words)
        if n == 0 or word_idx >= len(alignment):
            # Zero-width window if no narration left
            beat_dicts.append({"start_frame": f(hook_end), "end_frame": f(hook_end), "chunks": []})
            continue

        end_idx = min(word_idx + n - 1, len(alignment) - 1)
        beat_start = float(alignment[word_idx]["start"])
        beat_end = float(alignment[end_idx]["end"]) + 0.15  # tiny breath

        chunks: list[dict] = []
        cw = word_idx
        local = 0
        while cw <= end_idx and local < n:
            ce_word = min(cw + WORDS_PER_CAPTION_CHUNK - 1, end_idx, word_idx + n - 1)
            text = " ".join(beat_words[local : local + (ce_word - cw + 1)])
            cs = float(alignment[cw]["start"])
            cef = float(alignment[ce_word]["end"])
            chunks.append({"text": text, "start_frame": f(cs), "end_frame": f(cef)})
            local += ce_word - cw + 1
            cw = ce_word + 1

        beat_dicts.append({
            "start_frame": f(beat_start),
            "end_frame": f(beat_end),
            "chunks": chunks,
        })
        word_idx = end_idx + 1

    # CTA window — `cta_words` words AFTER beats and BEFORE outro.
    # Outro window — last `outro_words` words.
    outro_word_start = max(0, len(alignment) - outro_words)
    if cta_words and word_idx < outro_word_start:
        cta_start = float(alignment[word_idx]["start"])
        cta_end_idx = min(word_idx + cta_words - 1, outro_word_start - 1)
        cta_end = float(alignment[cta_end_idx]["end"]) + 0.2
    else:
        cta_start = float(alignment[max(0, outro_word_start - 1)]["end"]) if alignment else 0.0
        cta_end = cta_start + 1.0

    if outro_words and outro_word_start < len(alignment):
        outro_start = float(alignment[outro_word_start]["start"])
        outro_end = float(alignment[-1]["end"]) + 0.3
    else:
        outro_start = cta_end
        outro_end = outro_start + 1.5

    total_seconds = (float(alignment[-1]["end"]) if alignment else 60.0) + TAIL_BUFFER_SECONDS

    return {
        "hook": {"start_frame": 0, "end_frame": f(hook_end)},
        "beats": beat_dicts,
        "cta": {"start_frame": f(cta_start), "end_frame": f(cta_end)},
        "outro": {"start_frame": f(outro_start), "end_frame": f(outro_end)},
        "total_frames": f(total_seconds),
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

    return {
        "composition": composition_id,
        "title": script.title,
        "hook": script.hook,
        "cta": script.cta,
        "narration_audio": asset_url(narration),
        "intro_overlay": intro_url,
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
