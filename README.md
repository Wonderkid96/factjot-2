# Fact Jot v2

Autonomous Instagram + YouTube Shorts publishing system, rebuilt with a pluggable pipeline framework.

**Status:** Phase 1 build, dry-run only.

**v1 reference (read-only):** `/Users/Music/Developer/Insta-bot/`. See `V1_REFERENCE.md`.

## Quick links
- Spec: [docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md](docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md)
- Plan: [docs/superpowers/plans/2026-05-10-factjot-v2-rebuild.md](docs/superpowers/plans/2026-05-10-factjot-v2-rebuild.md)
- Audit findings: [docs/audit-findings.md](docs/audit-findings.md)

## Hard rules (carried over from v1)
1. Em dashes banned in `.yml` / `.yaml` (GitHub Go YAML parser silently rejects)
2. Audio resampled to 48kHz before muxing (Meta rejects 44.1kHz)
3. Never force-push to main
4. "Visual success is success" — open the rendered artefact, don't trust green tests
5. Append-only ledgers (one named exception: `reel_performance.jsonl`)
6. Library-audit before building from scratch (see spec §15.1)
7. Dry-run by default; publish requires explicit `--allow-publish`

## Setup (Phase 1)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp /Users/Music/Developer/Insta-bot/.env .env
```

Then read the plan and start at Milestone 1.
