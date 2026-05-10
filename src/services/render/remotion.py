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


def build_video_spec(script: Script, media: MediaSet, composition_id: str) -> dict:
    asset_by_beat = {a.beat_index: a for a in media.assets}
    windows = _compute_beat_windows(script.beats, media.narration_alignment)
    return {
        "composition": composition_id,
        "title": script.title,
        "hook": script.hook,
        "cta": script.cta,
        "narration_audio": str(media.narration_audio) if media.narration_audio else None,
        "alignment": media.narration_alignment,
        "beats": [
            {
                "text": b.text,
                "start_frame": windows[i]["start_frame"],
                "end_frame": windows[i]["end_frame"],
                "asset": {
                    "path": str(asset_by_beat[i].local_path) if i in asset_by_beat else None,
                    "source": asset_by_beat[i].provider if i in asset_by_beat else None,
                },
            }
            for i, b in enumerate(script.beats)
        ],
    }


def render_via_remotion(script: Script, media: MediaSet, out_path: Path, composition_id: str) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path = out_path.with_suffix(".spec.json")
    spec_path.write_text(json.dumps(build_video_spec(script, media, composition_id)))

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
    """Render a single PNG frame from a Remotion composition.

    Used for thumbnails and story tiles. Same Remotion compositions, single-frame export.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path = out_path.with_suffix(".props.json")
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
