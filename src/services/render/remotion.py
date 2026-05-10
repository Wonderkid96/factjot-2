import json
import subprocess
from pathlib import Path
from src.core.paths import REMOTION_DIR
from src.pipelines.models import Script, MediaSet


def build_video_spec(script: Script, media: MediaSet, composition_id: str) -> dict:
    asset_by_beat = {a.beat_index: a for a in media.assets}
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
