import json
import subprocess
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


def _rel_to_public(p: Path | str | None, public_dir: Path) -> str | None:
    """Convert an absolute asset path into a path relative to the Remotion public dir.

    Remotion's renderer fetches `<Audio src=...>` and `<Img src=...>` via its
    bundler dev server. The dev server only serves files inside `--public-dir`.
    Absolute paths outside that root produce 404. So we make every asset path
    relative to the public dir we'll pass on the CLI.
    """
    if p is None:
        return None
    p = Path(p)
    try:
        return str(p.resolve().relative_to(public_dir.resolve()))
    except ValueError:
        # Asset isn't under the public dir; return basename as a best-effort
        # (caller is responsible for ensuring it ends up there).
        return p.name


def build_video_spec(script: Script, media: MediaSet, composition_id: str, public_dir: Path | None = None) -> dict:
    """Build the JSON contract Remotion consumes.

    If `public_dir` is given, asset paths in the output are converted to be
    relative to it (so Remotion's --public-dir serves them). Otherwise paths
    are kept as-is — useful for unit tests.
    """
    asset_by_beat = {a.beat_index: a for a in media.assets}
    windows = _compute_beat_windows(script.beats, media.narration_alignment)
    narration = media.narration_audio
    return {
        "composition": composition_id,
        "title": script.title,
        "hook": script.hook,
        "cta": script.cta,
        "narration_audio": (
            _rel_to_public(narration, public_dir) if (public_dir and narration) else (str(narration) if narration else None)
        ),
        "alignment": media.narration_alignment,
        "beats": [
            {
                "text": b.text,
                "start_frame": windows[i]["start_frame"],
                "end_frame": windows[i]["end_frame"],
                "asset": {
                    "path": (
                        _rel_to_public(asset_by_beat[i].local_path, public_dir)
                        if (public_dir and i in asset_by_beat)
                        else (str(asset_by_beat[i].local_path) if i in asset_by_beat else None)
                    ),
                    "source": asset_by_beat[i].provider if i in asset_by_beat else None,
                },
            }
            for i, b in enumerate(script.beats)
        ],
    }


def render_via_remotion(script: Script, media: MediaSet, out_path: Path, composition_id: str) -> Path:
    """Render the FactReel composition to MP4.

    The run-output directory is used as Remotion's --public-dir so the
    narration MP3 and beat assets (already living there) are served by the
    bundler dev server. Spec paths are made relative to this dir.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    public_dir = out_path.parent
    spec_path = out_path.with_suffix(".spec.json")
    spec_path.write_text(json.dumps(build_video_spec(script, media, composition_id, public_dir=public_dir)))

    cmd = [
        "npx", "remotion", "render",
        composition_id,
        str(out_path),
        "--props", str(spec_path),
        "--config", "remotion.config.ts",
        "--public-dir", str(public_dir),
    ]
    result = subprocess.run(cmd, cwd=REMOTION_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Remotion render failed: {result.stderr}")
    return out_path


def render_still_via_remotion(composition_id: str, props: dict, out_path: Path) -> Path:
    """Render a single PNG frame from a Remotion composition.

    Used for thumbnails and story tiles. Same Remotion compositions, single-frame export.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    public_dir = out_path.parent
    spec_path = out_path.with_suffix(".props.json")

    # Convert any absolute frame_path to relative-to-public-dir, mirroring render_via_remotion.
    if isinstance(props.get("frame_path"), str):
        props = {**props, "frame_path": _rel_to_public(props["frame_path"], public_dir)}
    spec_path.write_text(json.dumps(props))

    cmd = [
        "npx", "remotion", "still",
        composition_id,
        str(out_path),
        "--props", str(spec_path),
        "--config", "remotion.config.ts",
        "--public-dir", str(public_dir),
    ]
    result = subprocess.run(cmd, cwd=REMOTION_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Remotion still failed: {result.stderr}")
    return out_path
