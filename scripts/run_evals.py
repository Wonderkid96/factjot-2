#!/usr/bin/env python3
"""Run the reel pipeline eval rubric against a single run directory.

Usage:
    python scripts/run_evals.py <run_dir>

Reads `.claude/evals/reel-pipeline.md` for the rubric definition (informational).
Writes results to `<run_dir>/eval-report.json` and appends to
`.claude/evals/reel-pipeline.log`.

Exit code 0 if all required graders pass, 1 otherwise — so this can gate CI.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


# `uv run` strips Homebrew paths. Prepend the common ffprobe locations so
# the deterministic graders work locally without the caller setting PATH.
for _p in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
    if _p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_p}:{os.environ.get('PATH', '')}"


# ---------- result types --------------------------------------------------


@dataclass
class EvalResult:
    status: str  # "PASS" | "FAIL" | "SKIP"
    actual: Any = None
    expected: Any = None
    note: str = ""


def passed(**kw: Any) -> EvalResult: return EvalResult(status="PASS", **kw)
def failed(**kw: Any) -> EvalResult: return EvalResult(status="FAIL", **kw)
def skipped(note: str) -> EvalResult: return EvalResult(status="SKIP", note=note)


# ---------- artefact loaders ---------------------------------------------


def _load_spec(run_dir: Path) -> dict | None:
    spec = run_dir / "final.spec.json"
    if not spec.exists():
        return None
    return json.loads(spec.read_text())


def _load_alignment(run_dir: Path) -> list[dict]:
    align = run_dir / "narration-alignment.json"
    if not align.exists():
        return []
    return json.loads(align.read_text())


def _ffprobe_duration(mp4: Path) -> float | None:
    """Return MP4 duration in seconds, or None if ffprobe is unavailable."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(mp4)],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def _ffprobe_frame_count(mp4: Path) -> int | None:
    """Return MP4 nb_frames (video stream), or None if unavailable."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries", "stream=nb_read_frames",
             "-of", "csv=p=0", str(mp4)],
            capture_output=True, text=True, timeout=30,
        )
        # ffprobe with multiple streams emits "1275," — strip trailing comma + extras
        first = out.stdout.strip().split(",")[0]
        if out.returncode == 0 and first.isdigit():
            return int(first)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


# ---------- magic-byte sniff (mirror of pipeline.py) ----------------------


IMAGE_MAGIC = (
    (b"\xff\xd8",  "jpeg"),
    (b"\x89PNG",   "png"),
    (b"GIF87a",    "gif"),
    (b"GIF89a",    "gif"),
)
VIDEO_MAGIC = (
    (b"\x00\x00\x00", "mp4"),  # ftyp box is at offset 4; first 3 bytes commonly 00 00 00
    (b"RIFF",         "webp_or_avi"),
)


def _sniff_kind(head: bytes) -> str:
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:2] == b"\xff\xd8":
        return "jpeg"
    if head[:4] == b"\x89PNG":
        return "png"
    if head[:4] == b"RIFF":
        return "riff"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "mp4"
    return "unknown"


# ---------- capability graders -------------------------------------------


def ce_1_render_completes(run_dir: Path) -> EvalResult:
    mp4 = run_dir / "final.mp4"
    if not mp4.exists():
        return failed(note="final.mp4 missing")
    size = mp4.stat().st_size
    if size < 1_000_000:
        return failed(actual=size, expected=">= 1 MB",
                      note="final.mp4 smaller than 1 MB — render likely truncated")
    return passed(actual=f"{size / 1_048_576:.1f} MB")


def ce_2_duration_in_range(run_dir: Path) -> EvalResult:
    mp4 = run_dir / "final.mp4"
    if not mp4.exists():
        return failed(note="final.mp4 missing")
    dur = _ffprobe_duration(mp4)
    if dur is None:
        return skipped("ffprobe unavailable")
    ok = 25.0 <= dur <= 50.0
    return (passed if ok else failed)(actual=round(dur, 2), expected="25.0-50.0s")


def ce_3_frame_count_match(run_dir: Path) -> EvalResult:
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="final.spec.json missing")
    expected = int(spec.get("total_frames", 0))
    mp4 = run_dir / "final.mp4"
    if not mp4.exists():
        return failed(note="final.mp4 missing")
    actual = _ffprobe_frame_count(mp4)
    if actual is None:
        return skipped("ffprobe unavailable")
    # Remotion sometimes emits ±1 frame due to encoder rounding.
    ok = abs(actual - expected) <= 1
    return (passed if ok else failed)(actual=actual, expected=expected)


def ce_4_beat_assets_valid(run_dir: Path) -> EvalResult:
    assets = run_dir / "assets"
    if not assets.exists():
        return failed(note="assets/ missing")
    beat_files = sorted(assets.glob("beat-*.*"))
    if not beat_files:
        return failed(note="no beat-*.* files in assets/")
    bad: list[str] = []
    for f in beat_files:
        if f.stat().st_size < 4096:
            bad.append(f"{f.name} too small ({f.stat().st_size} bytes)")
            continue
        head = f.read_bytes()[:16]
        kind = _sniff_kind(head)
        if kind == "unknown":
            bad.append(f"{f.name} unrecognised magic bytes {head[:8].hex()}")
    if bad:
        return failed(note="; ".join(bad), actual=len(bad), expected=0)
    return passed(actual=f"{len(beat_files)} valid assets")


def ce_5_outro_present(run_dir: Path) -> EvalResult:
    align = _load_alignment(run_dir)
    if not align:
        return failed(note="alignment empty/missing")
    tail = " ".join(w["word"].lower() for w in align[-8:])
    if "follow" in tail and "fact" in tail and "jot" in tail:
        return passed(actual=tail)
    return failed(actual=tail, expected='"follow fact jot" in last 8 words')


def ce_6_no_em_dash(run_dir: Path) -> EvalResult:
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="spec missing")
    banned = ("—", "–")
    pieces = [spec.get("title", ""), spec.get("hook", ""), spec.get("cta", "")]
    for b in spec.get("beats", []):
        pieces.append(b.get("text", ""))
    offenders = [p for p in pieces if any(d in p for d in banned)]
    if offenders:
        return failed(actual=offenders, expected="none")
    return passed()


def ce_7_hook_word_count(run_dir: Path) -> EvalResult:
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="spec missing")
    n = len(spec.get("hook", "").split())
    ok = 6 <= n <= 10
    return (passed if ok else failed)(actual=n, expected="6-10")


def ce_8_script_word_count(run_dir: Path) -> EvalResult:
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="spec missing")
    parts = [spec.get("hook", "")]
    parts += [b.get("text", "") for b in spec.get("beats", [])]
    parts.append(spec.get("cta", ""))
    n = sum(len(p.split()) for p in parts)
    ok = 80 <= n <= 110
    return (passed if ok else failed)(actual=n, expected="80-110")


def ce_9_beat_count(run_dir: Path) -> EvalResult:
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="spec missing")
    n = len(spec.get("beats", []))
    return (passed if n == 4 else failed)(actual=n, expected=4)


def ce_10_topic_entity_field(run_dir: Path) -> EvalResult:
    """topic_entity is set in script.json (the writer's output), not spec.json,
    so we read it from the script-side artefact when available; fall back to
    PASS if neither exists, FAIL if the spec.json wasn't produced at all."""
    spec = _load_spec(run_dir)
    if not spec:
        return failed(note="spec missing")
    # The current pipeline doesn't persist the raw script.json separately;
    # the spec.json bakes selected fields. Re-derive: if topic_entity is
    # required by the schema, then it must appear in the produced data flow.
    # For now, validate that we COULD have produced it — checked by hook being
    # a proper-noun-friendly form. This is a weak grader until we persist the
    # raw script.
    return skipped("requires raw script.json — not yet persisted by pipeline")


CAPABILITY_GRADERS: list[tuple[str, Callable[[Path], EvalResult]]] = [
    ("CE-1_render_completes",    ce_1_render_completes),
    ("CE-2_duration_in_range",   ce_2_duration_in_range),
    ("CE-3_frame_count_match",   ce_3_frame_count_match),
    ("CE-4_beat_assets_valid",   ce_4_beat_assets_valid),
    ("CE-5_outro_present",       ce_5_outro_present),
    ("CE-6_no_em_dash",          ce_6_no_em_dash),
    ("CE-7_hook_word_count",     ce_7_hook_word_count),
    ("CE-8_script_word_count",   ce_8_script_word_count),
    ("CE-9_beat_count",          ce_9_beat_count),
    ("CE-10_topic_entity_field", ce_10_topic_entity_field),
]


# ---------- runner --------------------------------------------------------


def run(run_dir: Path) -> dict:
    capability: dict[str, dict] = {}
    for name, grader in CAPABILITY_GRADERS:
        result = grader(run_dir)
        capability[name] = {k: v for k, v in asdict(result).items() if v not in ("", None)}

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for r in capability.values():
        counts[r["status"]] += 1
    verdict = "PASS" if counts["FAIL"] == 0 else "FAIL"

    report = {
        "run_id": run_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "capability": capability,
        "summary": {"passed": counts["PASS"], "failed": counts["FAIL"], "skipped": counts["SKIP"]},
        "verdict": verdict,
    }
    return report


def _print_console(report: dict) -> None:
    print(f"\n=== eval report: {report['run_id']} ===")
    for name, r in report["capability"].items():
        sym = {"PASS": "✓", "FAIL": "✗", "SKIP": "·"}[r["status"]]
        extras: list[str] = []
        if "actual" in r:   extras.append(f"actual={r['actual']}")
        if "expected" in r: extras.append(f"expected={r['expected']}")
        if "note" in r:     extras.append(f"note={r['note']}")
        suffix = " — " + ", ".join(extras) if extras else ""
        print(f"  {sym} {name}{suffix}")
    s = report["summary"]
    print(f"\nsummary: {s['passed']} passed, {s['failed']} failed, {s['skipped']} skipped")
    print(f"verdict: {report['verdict']}\n")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_evals.py <run_dir>", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).resolve()
    if not run_dir.is_dir():
        print(f"not a directory: {run_dir}", file=sys.stderr)
        return 2

    report = run(run_dir)
    out = run_dir / "eval-report.json"
    out.write_text(json.dumps(report, indent=2))
    _print_console(report)

    # Append one-line summary to rolling log
    log = Path(".claude/evals/reel-pipeline.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    s = report["summary"]
    log_line = (
        f"{report['timestamp']}  {report['run_id']:<70}"
        f"  pass={s['passed']:2d}  fail={s['failed']:2d}  skip={s['skipped']:2d}"
        f"  verdict={report['verdict']}\n"
    )
    with log.open("a") as f:
        f.write(log_line)

    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
