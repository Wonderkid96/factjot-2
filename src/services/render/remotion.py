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


def _compute_beat_windows(beats, alignment, fps: int = 30) -> list[dict]:
    """For each beat, find the narration window (first word start -> last word end) and convert to frames."""
    if not alignment:
        # Fallback: even split over 60s
        per = 60 / max(len(beats), 1)
        return [{"start_frame": int(i * per * fps), "end_frame": int((i + 1) * per * fps)} for i in range(len(beats))]

    # Walk word timestamps and split per beat (alignment is concatenated word timing for hook+beats+cta in order)
    word_idx = 0
    windows = []
    for b in beats:
        beat_words = b.text.split()
        n = len(beat_words)
        if word_idx >= len(alignment):
            windows.append({"start_frame": int(60 * fps), "end_frame": int(60 * fps)})
            continue
        start = float(alignment[word_idx]["start"])
        end_idx = min(word_idx + n - 1, len(alignment) - 1)
        end = float(alignment[end_idx]["end"]) + 0.2  # 200ms breath
        windows.append({"start_frame": int(start * fps), "end_frame": int(end * fps)})
        word_idx = end_idx + 1
    return windows


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
    windows = _compute_beat_windows(script.beats, media.narration_alignment)
    narration = media.narration_audio

    def asset_url(p: Path | str | None) -> str | None:
        if base_url and run_dir:
            return _to_url(p, base_url, run_dir)
        return str(p) if p else None

    return {
        "composition": composition_id,
        "title": script.title,
        "hook": script.hook,
        "cta": script.cta,
        "narration_audio": asset_url(narration),
        "alignment": media.narration_alignment,
        "beats": [
            {
                "text": b.text,
                "start_frame": windows[i]["start_frame"],
                "end_frame": windows[i]["end_frame"],
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
