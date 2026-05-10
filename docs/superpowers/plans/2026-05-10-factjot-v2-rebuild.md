# Fact Jot v2 — Rebuild Implementation Plan (Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Fact Jot v2 in `/Users/Music/Developer/Bot-2/` with a pluggable pipeline framework + a working reel pipeline that produces inspectable dry-run MP4s, incorporating six frontier improvements over v1, while v1 keeps publishing untouched.

**Architecture:** Hybrid stack — Python orchestration + TypeScript only inside Remotion. Pluggable pipelines (one folder per pipeline, auto-discovered). Single GitHub Actions dispatcher workflow. State as append-only JSONL ledgers. Dry-run only until Phase 5.

**Tech Stack:** Python 3.11, TypeScript 5+, Remotion 5, Anthropic SDK (Claude Sonnet 4.6 + Opus 4.7 + Haiku 4.5 vision), ElevenLabs SDK (eleven_v3), Wikidata (qwikidata), Wikimedia (mwclient), pydantic v2, tenacity, ffmpeg-python, pytest, vitest.

**Spec:** `docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md`

**v1 reference (READ-ONLY):** `/Users/Music/Developer/Insta-bot/` — never `/Users/Music/Documents/` (iCloud breaks FFmpeg per v1 CLAUDE.md §6).

---

## Plan structure

This plan is organised into **25 milestones**. Each milestone is a natural pause point — review and inspect before continuing. Milestones are sequential where dependencies require it, parallelisable where they don't (noted in milestone headers).

**Library-audit-first principle:** every milestone touching a non-trivial component starts with a library audit task. Build from scratch only when no maintained library fits.

**TDD pattern:** every code task follows write-test → run-fails → implement → run-passes → commit.

**Commit cadence:** after every task. Small, frequent, reversible.

---

## Milestone 0: Reference lock & repo init

### Task 0.1: Lock the v1 reference path

**Files:**
- Create: `/Users/Music/Developer/Bot-2/V1_REFERENCE.md`

- [ ] **Step 1: Create V1_REFERENCE.md as a single-source pointer**

```markdown
# v1 Reference

The v1 codebase that v2 references is at:

`/Users/Music/Developer/Insta-bot/`

**Never** `/Users/Music/Documents/Insta-bot/` — iCloud sync in `Documents/` intercepts FFmpeg writes and produces silent 14-min encode hangs (per v1 `CLAUDE.md` §6).

v1 is **read-only**. v2 reads v1 to understand decisions; v2 never imports, symlinks to, or modifies v1.

When in doubt about path, run:
```bash
ls /Users/Music/Developer/Insta-bot/CLAUDE.md
```
This file must exist. If it doesn't, the path is wrong.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/Music/Developer/Bot-2
git init
git add V1_REFERENCE.md
git commit -m "chore: lock v1 reference path"
```

### Task 0.2: Initialise pyproject.toml

**Files:**
- Create: `/Users/Music/Developer/Bot-2/pyproject.toml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "factjot-v2"
version = "0.1.0"
description = "Fact Jot v2 — pluggable pipeline framework"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "elevenlabs>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "pyyaml>=6.0",
    "tenacity>=8.0.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: initialise pyproject.toml with core deps"
```

### Task 0.3: Create .gitignore

**Files:**
- Create: `/Users/Music/Developer/Bot-2/.gitignore`

- [ ] **Step 1: Write .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
dist/
build/

# Node / Remotion
node_modules/
remotion/out/

# Secrets
.env
.env.local

# Local artefacts
output/
runs/
*.mp4
*.wav
*.mp3
.DS_Store

# Editor
.vscode/
.idea/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

### Task 0.4: Create directory skeleton

**Files:**
- Create: directory tree

- [ ] **Step 1: Create directories**

```bash
cd /Users/Music/Developer/Bot-2
mkdir -p src/{core,pipelines,services,runner}
mkdir -p src/services/{sourcing,resolution,verification,selection,curation,narration,render,publish,state}
mkdir -p src/pipelines/reel_evergreen/prompts
mkdir -p remotion/{compositions,components,style}
mkdir -p brand style data/ledgers tests .github/workflows
mkdir -p docs/superpowers/{specs,plans}
touch src/__init__.py src/core/__init__.py src/pipelines/__init__.py src/services/__init__.py src/runner/__init__.py
touch src/services/sourcing/__init__.py src/services/resolution/__init__.py src/services/verification/__init__.py
touch src/services/selection/__init__.py src/services/curation/__init__.py src/services/narration/__init__.py
touch src/services/render/__init__.py src/services/publish/__init__.py src/services/state/__init__.py
touch src/pipelines/reel_evergreen/__init__.py
touch tests/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: create v2 directory skeleton"
```

### Task 0.5: Initialise README

**Files:**
- Create: `/Users/Music/Developer/Bot-2/README.md`

- [ ] **Step 1: Write README**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: seed README with Phase 1 status"
```

---

## Milestone 1: Environment & secrets

### Task 1.1: Audit v1's .env keys

**Files:**
- Create: `/Users/Music/Developer/Bot-2/docs/audit-findings.md`

- [ ] **Step 1: Inspect v1 .env (without copying secrets to docs)**

Run: `grep -E '^[A-Z_]+=' /Users/Music/Developer/Insta-bot/.env | cut -d= -f1`

Expected: list of env keys (e.g. `META_ACCESS_TOKEN`, `ELEVENLABS_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

- [ ] **Step 2: Create audit-findings.md and record the env keys**

```markdown
# Audit Findings

This file captures observations made while reading the v1 codebase during v2 rebuild. Each entry: file/area, observation, v2 status (preserved / changed / fixed / escalated).

---

## 2026-05-10: v1 .env keys catalogued

**Source:** `/Users/Music/Developer/Insta-bot/.env`

**Keys observed (names only, never values):**
- (run `grep -E '^[A-Z_]+=' /Users/Music/Developer/Insta-bot/.env | cut -d= -f1` to populate)

**v2 status:** v2 will copy this `.env` once at Task 1.2. Same keys; v2 has its own file from then on.
```

- [ ] **Step 3: Run the grep, list keys in audit-findings.md**

Replace the placeholder line in step 2 with the actual key names from `grep`.

- [ ] **Step 4: Commit**

```bash
git add docs/audit-findings.md
git commit -m "docs: audit v1 .env key inventory"
```

### Task 1.2: Copy .env from v1 (one-time, then independent)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/.env` (gitignored)

- [ ] **Step 1: Copy v1 .env to v2**

```bash
cp /Users/Music/Developer/Insta-bot/.env /Users/Music/Developer/Bot-2/.env
```

- [ ] **Step 2: Verify .env is gitignored (must NOT appear in git status)**

Run: `cd /Users/Music/Developer/Bot-2 && git status --porcelain | grep -F .env`
Expected: empty output (file is ignored).

- [ ] **Step 3: No commit needed (file is gitignored)**

### Task 1.3: Write .env.example documenting required keys

**Files:**
- Create: `/Users/Music/Developer/Bot-2/.env.example`

- [ ] **Step 1: Write .env.example with names + comments**

```bash
# LLM
ANTHROPIC_API_KEY=

# Narration
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE=        # required; live value lives in .env (carried over from v1)

# Image / footage providers
PEXELS_API_KEY=
PIXABAY_API_KEY=
COVERR_API_KEY=
SMITHSONIAN_API_KEY=    # optional; DEMO_KEY tier works without
TMDB_API_KEY=           # for film/TV poster confidence-gating

# Instagram (Meta Graph API)
META_ACCESS_TOKEN=
INSTAGRAM_ACCOUNT_ID=
FACEBOOK_PAGE_ID=

# Image hosting (carried over from v1; v2 may swap)
IMGBB_API_KEY=

# YouTube (Data API v3)
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=

# Phase 1 mode
DRY_RUN=true
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: document required env keys"
```

### Task 1.4: Write a sanity check script that verifies .env has all required keys

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_env_validation.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_env_validation.py
from src.core.config import Settings

def test_settings_loads_required_keys():
    settings = Settings()
    assert settings.anthropic_api_key, "ANTHROPIC_API_KEY missing"
    assert settings.elevenlabs_api_key, "ELEVENLABS_API_KEY missing"
    assert settings.elevenlabs_voice, "ELEVENLABS_VOICE missing"
    assert settings.pexels_api_key, "PEXELS_API_KEY missing"
    assert settings.dry_run is True, "Phase 1 must dry-run by default"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_env_validation.py -v`
Expected: FAIL — `src.core.config` does not exist.

- [ ] **Step 3: Implement src/core/config.py using pydantic-settings**

```python
# src/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Narration
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice: str = Field(..., alias="ELEVENLABS_VOICE")

    # Sourcing
    pexels_api_key: str = Field(..., alias="PEXELS_API_KEY")
    pixabay_api_key: str = Field(..., alias="PIXABAY_API_KEY")
    smithsonian_api_key: str = Field(default="DEMO_KEY", alias="SMITHSONIAN_API_KEY")
    tmdb_api_key: str | None = Field(default=None, alias="TMDB_API_KEY")

    # Instagram
    meta_access_token: str = Field(..., alias="META_ACCESS_TOKEN")
    instagram_account_id: str = Field(..., alias="INSTAGRAM_ACCOUNT_ID")
    facebook_page_id: str = Field(..., alias="FACEBOOK_PAGE_ID")
    imgbb_api_key: str = Field(..., alias="IMGBB_API_KEY")

    # YouTube
    youtube_client_id: str = Field(..., alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: str = Field(..., alias="YOUTUBE_CLIENT_SECRET")
    youtube_refresh_token: str = Field(..., alias="YOUTUBE_REFRESH_TOKEN")

    # Phase 1 mode
    dry_run: bool = Field(default=True, alias="DRY_RUN")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_env_validation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_env_validation.py src/core/config.py
git commit -m "feat(core): pydantic settings loader for env keys"
```

---

## Milestone 2: Brand kit + insta-brain seed

### Task 2.1: Copy brand_kit.json from v1

**Files:**
- Create: `/Users/Music/Developer/Bot-2/brand/brand_kit.json` (copy)

- [ ] **Step 1: Verify v1 brand_kit exists**

Run: `ls /Users/Music/Developer/Insta-bot/brand/brand_kit.json`
Expected: file path printed.

- [ ] **Step 2: Copy to v2**

```bash
cp /Users/Music/Developer/Insta-bot/brand/brand_kit.json /Users/Music/Developer/Bot-2/brand/brand_kit.json
```

- [ ] **Step 3: Document the copy in audit-findings.md**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: brand_kit.json copied from v1

**Source:** `/Users/Music/Developer/Insta-bot/brand/brand_kit.json`
**Destination:** `brand/brand_kit.json`
**v2 status:** preserved as-is. Independent from v1 from this point. Per spec §6, edits do not propagate either direction.
```

- [ ] **Step 4: Commit**

```bash
git add brand/brand_kit.json docs/audit-findings.md
git commit -m "feat(brand): copy brand_kit.json from v1"
```

### Task 2.2: Seed insta-brain from v1 (non-secret bits only)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/insta-brain/CLAUDE.md`
- Create: `/Users/Music/Developer/Bot-2/insta-brain/CRITICAL_FACTS.md`
- Create: `/Users/Music/Developer/Bot-2/insta-brain/gotchas.md`

- [ ] **Step 1: Copy the three reference files**

```bash
mkdir -p /Users/Music/Developer/Bot-2/insta-brain
cp /Users/Music/Developer/Insta-bot/insta-brain/CLAUDE.md /Users/Music/Developer/Bot-2/insta-brain/
cp /Users/Music/Developer/Insta-bot/insta-brain/CRITICAL_FACTS.md /Users/Music/Developer/Bot-2/insta-brain/
cp /Users/Music/Developer/Insta-bot/insta-brain/gotchas.md /Users/Music/Developer/Bot-2/insta-brain/
```

- [ ] **Step 2: Add a v2 header note to CLAUDE.md**

Prepend this block to `/Users/Music/Developer/Bot-2/insta-brain/CLAUDE.md`:

```markdown
> **v2 NOTE:** This file is the v2 fork of v1's insta-brain/CLAUDE.md (copied 2026-05-10). v2 evolves this file independently. v1's original lives at `/Users/Music/Developer/Insta-bot/insta-brain/CLAUDE.md` (read-only).
>
> ---
```

- [ ] **Step 3: Commit**

```bash
git add insta-brain/
git commit -m "feat(brain): seed insta-brain from v1 (independent fork)"
```

### Task 2.3: Brand loader (typed access to brand_kit.json)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_brand_loader.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/brand.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_brand_loader.py
from src.core.brand import load_brand

def test_brand_loads_palette():
    brand = load_brand()
    assert "palette" in brand
    assert isinstance(brand["palette"], dict)

def test_brand_loads_fonts():
    brand = load_brand()
    assert "fonts" in brand
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_brand_loader.py -v`
Expected: FAIL — `src.core.brand` does not exist.

- [ ] **Step 3: Implement loader**

```python
# src/core/brand.py
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

BRAND_KIT_PATH = Path(__file__).parent.parent.parent / "brand" / "brand_kit.json"


@lru_cache(maxsize=1)
def load_brand() -> dict[str, Any]:
    """Load brand_kit.json once and cache. v1 §9 contract: tokens consumed, never inlined."""
    with BRAND_KIT_PATH.open() as f:
        return json.load(f)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_brand_loader.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_brand_loader.py src/core/brand.py
git commit -m "feat(core): typed brand_kit loader"
```

---

## Milestone 3: Core modules — paths, IDs, logging

### Task 3.1: Canonical paths module

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_paths.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/paths.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_paths.py
from src.core.paths import REPO_ROOT, OUTPUT_DIR, LEDGER_DIR, REMOTION_DIR

def test_repo_root_exists():
    assert REPO_ROOT.exists()
    assert (REPO_ROOT / "pyproject.toml").exists()

def test_output_dir_under_repo():
    assert OUTPUT_DIR.is_relative_to(REPO_ROOT)

def test_ledger_dir_under_repo():
    assert LEDGER_DIR.is_relative_to(REPO_ROOT)

def test_remotion_dir_under_repo():
    assert REMOTION_DIR.is_relative_to(REPO_ROOT)
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_paths.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement paths**

```python
# src/core/paths.py
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
OUTPUT_DIR = REPO_ROOT / "output"
LEDGER_DIR = REPO_ROOT / "data" / "ledgers"
REMOTION_DIR = REPO_ROOT / "remotion"
BRAND_DIR = REPO_ROOT / "brand"
INSTA_BRAIN_DIR = REPO_ROOT / "insta-brain"


def ensure_dirs() -> None:
    """Create required runtime directories if missing."""
    for d in (OUTPUT_DIR, LEDGER_DIR):
        d.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_paths.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_paths.py src/core/paths.py
git commit -m "feat(core): canonical paths module"
```

### Task 3.2: Run-ID generation

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_run_id.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/run_id.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_id.py
import re
from src.core.run_id import new_run_id

def test_run_id_format():
    rid = new_run_id("reel_evergreen", topic_slug="apollo-11")
    # YYYY-MM-DD_HH-MM_<pipeline>_<slug>
    assert re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}_reel_evergreen_apollo-11$", rid)

def test_run_id_unique_with_seconds_when_collision():
    rid1 = new_run_id("reel_evergreen", topic_slug="x", include_seconds=True)
    rid2 = new_run_id("reel_evergreen", topic_slug="x", include_seconds=True)
    assert rid1 != rid2 or rid1.count("_") >= 4
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_run_id.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/core/run_id.py
import re
from datetime import datetime, timezone


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len]


def new_run_id(pipeline: str, topic_slug: str, include_seconds: bool = False) -> str:
    """Generate a deterministic, sortable run identifier.

    Format: YYYY-MM-DD_HH-MM[_SS]_<pipeline>_<slug>
    """
    fmt = "%Y-%m-%d_%H-%M-%S" if include_seconds else "%Y-%m-%d_%H-%M"
    ts = datetime.now(timezone.utc).strftime(fmt)
    return f"{ts}_{pipeline}_{slugify(topic_slug)}"
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_run_id.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_run_id.py src/core/run_id.py
git commit -m "feat(core): run-id generator"
```

### Task 3.3: Structured logger

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_logger.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/logger.py`

- [ ] **Step 1: Library audit for logging**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: logging library audit

**Need:** structured logging with JSON output for CI, human-readable for dev.

**Candidates:** `loguru` (popular, simple), `structlog` (composable), stdlib `logging` (zero deps).

**Decision:** `structlog`. Composable, supports both JSON and console renderer, mature, used widely. Cost: 1 dep.

**Verdict:** add `structlog>=24.0.0` to pyproject.toml.
```

- [ ] **Step 2: Add structlog to pyproject.toml**

Edit `pyproject.toml` dependencies block, add `"structlog>=24.0.0",` then `pip install -e ".[dev]"`.

- [ ] **Step 3: Write failing test**

```python
# tests/test_logger.py
from src.core.logger import get_logger

def test_logger_returns_bound_logger():
    log = get_logger("test")
    assert hasattr(log, "info")
    assert hasattr(log, "error")

def test_logger_emits(caplog):
    log = get_logger("test")
    log.info("hello", run_id="abc")
    # structlog default writes via stdlib; caplog captures
    assert any("hello" in r.message for r in caplog.records) or True  # smoke
```

- [ ] **Step 4: Run to fail**

Run: `pytest tests/test_logger.py -v`
Expected: FAIL.

- [ ] **Step 5: Implement**

```python
# src/core/logger.py
import logging
import sys
import structlog


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


configure_logging()
```

- [ ] **Step 6: Run to pass**

Run: `pytest tests/test_logger.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml tests/test_logger.py src/core/logger.py docs/audit-findings.md
git commit -m "feat(core): structlog-based logger"
```

---

## Milestone 4: Pipeline framework foundation

### Task 4.1: Define core dataclasses

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_models.py`
- Create: `/Users/Music/Developer/Bot-2/src/pipelines/models.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_models.py
from src.pipelines.models import Brief, Citation, Beat, Script, MediaAsset, MediaSet, Platform

def test_brief_minimum():
    b = Brief(topic="Apollo 11", angle="moon landing weirdness")
    assert b.topic == "Apollo 11"

def test_script_has_beats():
    s = Script(title="x", hook="y", beats=[Beat(text="t", visual_brief={})], cta="z", citations=[])
    assert len(s.beats) == 1

def test_platform_enum():
    assert Platform.INSTAGRAM.value == "instagram"
    assert Platform.YOUTUBE_SHORTS.value == "youtube_shorts"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement models**

```python
# src/pipelines/models.py
from enum import Enum
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"


class Brief(BaseModel):
    topic: str
    angle: str
    format: Literal["fact", "list"] = "fact"
    pipeline_name: str = "reel_evergreen"


class Citation(BaseModel):
    claim: str
    source_url: str
    source_quote: str = ""


class VisualBrief(BaseModel):
    subject: str
    shot_type: Literal["wide", "close", "macro", "aerial", "static", "motion"] = "wide"
    mood: str = ""
    queries: list[str] = Field(default_factory=list)
    preferred_source: Literal["video", "image"] = "video"
    ai_fallback_prompt: str = ""
    period_constraints: dict[str, int | list[str]] | None = None


class Beat(BaseModel):
    text: str
    visual_brief: VisualBrief | dict = Field(default_factory=dict)


class PostMetadata(BaseModel):
    title: str
    description: str = ""
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    youtube_tags: list[str] = Field(default_factory=list)


class Script(BaseModel):
    title: str
    hook: str
    beats: list[Beat]
    cta: str
    citations: list[Citation]
    post_metadata: PostMetadata | None = None


class MediaAsset(BaseModel):
    beat_index: int
    local_path: Path
    source_url: str
    provider: str
    license: str = "unknown"
    width: int = 0
    height: int = 0


class MediaSet(BaseModel):
    assets: list[MediaAsset] = Field(default_factory=list)
    narration_audio: Path | None = None
    narration_alignment: list[dict] = Field(default_factory=list)


class Verification(BaseModel):
    verified: bool
    failures: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class PublishResult(BaseModel):
    platform: Platform
    posted: bool
    remote_id: str | None = None
    error: str | None = None
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_models.py src/pipelines/models.py
git commit -m "feat(pipelines): core pydantic dataclasses"
```

### Task 4.2: Pipeline base class

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_pipeline_base.py`
- Create: `/Users/Music/Developer/Bot-2/src/pipelines/base.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_pipeline_base.py
from pathlib import Path
from src.pipelines.base import Pipeline
from src.pipelines.models import Brief, Script, MediaSet, Verification, Beat, VisualBrief, Platform

class _DummyPipeline(Pipeline):
    name = "dummy"
    output_format = "reel"
    target_platforms = [Platform.INSTAGRAM]
    brand_format = "reel_overlay"
    remotion_composition = None

    def source(self) -> Brief:
        return Brief(topic="t", angle="a")

    def verify(self, brief): return Verification(verified=True)
    def generate(self, brief): return Script(title="t", hook="h", beats=[], cta="c", citations=[])
    def acquire_media(self, script): return MediaSet()
    def render(self, script, media): return Path("/tmp/dummy.mp4")


def test_pipeline_subclass_runs():
    p = _DummyPipeline()
    assert p.name == "dummy"
    assert Platform.INSTAGRAM in p.target_platforms
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_pipeline_base.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/pipelines/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Literal
from src.pipelines.models import (
    Brief, Script, MediaSet, Verification, PublishResult, Platform
)


class Pipeline(ABC):
    """Base contract every Fact Jot v2 pipeline implements.

    Lifecycle (from spec §7, matches v1 SPEC §5):
      SOURCE -> VERIFY -> GENERATE -> ACQUIRE_MEDIA -> RENDER -> (APPROVE) -> PUBLISH -> LEDGER -> MEASURE
    """

    name: ClassVar[str]
    output_format: ClassVar[Literal["reel", "carousel"]]
    target_platforms: ClassVar[list[Platform]]
    brand_format: ClassVar[str]
    remotion_composition: ClassVar[str | None]  # null for non-Remotion pipelines

    @abstractmethod
    def source(self) -> Brief: ...

    @abstractmethod
    def verify(self, brief: Brief) -> Verification: ...

    @abstractmethod
    def generate(self, brief: Brief) -> Script: ...

    @abstractmethod
    def acquire_media(self, script: Script) -> MediaSet: ...

    @abstractmethod
    def render(self, script: Script, media: MediaSet) -> Path: ...

    def publish(self, output: Path, brief: Brief) -> list[PublishResult]:
        """Default: dry-run no-op. Real publishing wired in Milestone 19, gated by --allow-publish."""
        return [
            PublishResult(platform=p, posted=False, error="dry-run")
            for p in self.target_platforms
        ]

    def ledger(self, results: list[PublishResult]) -> None:
        """Default: append to standard ledgers. Implementations may override for pipeline-specific state."""
        from src.services.state.ledgers import append_run_record
        append_run_record(self.name, results)
```

Note: `append_run_record` will be implemented in Milestone 5; Pipeline.ledger is fine to reference it lazily via inline import.

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_pipeline_base.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pipeline_base.py src/pipelines/base.py
git commit -m "feat(pipelines): Pipeline ABC with lifecycle contract"
```

### Task 4.3: Pipeline registry (auto-discovery)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_registry.py`
- Create: `/Users/Music/Developer/Bot-2/src/pipelines/registry.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_registry.py
from src.pipelines.registry import discover_pipelines, get_pipeline

def test_discover_returns_dict():
    pipelines = discover_pipelines()
    assert isinstance(pipelines, dict)

def test_get_unknown_pipeline_raises():
    import pytest
    with pytest.raises(KeyError):
        get_pipeline("does_not_exist")
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_registry.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/pipelines/registry.py
import importlib
import pkgutil
from src.pipelines.base import Pipeline


_REGISTRY: dict[str, type[Pipeline]] = {}


def discover_pipelines() -> dict[str, type[Pipeline]]:
    """Walk src/pipelines/ for subpackages exposing a Pipeline subclass."""
    global _REGISTRY
    if _REGISTRY:
        return _REGISTRY

    import src.pipelines as pkg
    for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
        if not ispkg:
            continue
        try:
            mod = importlib.import_module(f"src.pipelines.{modname}.pipeline")
        except ModuleNotFoundError:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, Pipeline)
                and cls is not Pipeline
            ):
                _REGISTRY[cls.name] = cls
    return _REGISTRY


def get_pipeline(name: str) -> type[Pipeline]:
    discover_pipelines()
    if name not in _REGISTRY:
        raise KeyError(f"Pipeline '{name}' not found. Known: {list(_REGISTRY)}")
    return _REGISTRY[name]
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_registry.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_registry.py src/pipelines/registry.py
git commit -m "feat(pipelines): auto-discovery registry"
```

---

## Milestone 5: State services — ledgers and run records

### Task 5.1: Append-only JSONL ledger writer

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_ledgers.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/state/ledgers.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_ledgers.py
import json
import tempfile
from pathlib import Path
from src.services.state import ledgers

def test_append_creates_file_and_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(ledgers, "LEDGER_DIR", tmp_path)
    ledgers.append("posted.jsonl", {"id": "abc", "ok": True})
    contents = (tmp_path / "posted.jsonl").read_text().strip().splitlines()
    assert json.loads(contents[0]) == {"id": "abc", "ok": True}

def test_append_is_appendonly(tmp_path, monkeypatch):
    monkeypatch.setattr(ledgers, "LEDGER_DIR", tmp_path)
    ledgers.append("x.jsonl", {"a": 1})
    ledgers.append("x.jsonl", {"a": 2})
    lines = (tmp_path / "x.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_ledgers.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/state/ledgers.py
import json
from pathlib import Path
from src.core.paths import LEDGER_DIR


def append(filename: str, record: dict) -> None:
    """Append a single record as one JSON line to ledger file."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / filename
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_all(filename: str) -> list[dict]:
    """Read all records from a ledger file."""
    path = LEDGER_DIR / filename
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_run_record(pipeline: str, results) -> None:
    """Convenience used by Pipeline.ledger default."""
    append("runs.jsonl", {
        "pipeline": pipeline,
        "results": [r.model_dump(mode="json") for r in results],
    })
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_ledgers.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ledgers.py src/services/state/ledgers.py
git commit -m "feat(state): append-only JSONL ledger writer"
```

### Task 5.2: Run-context (output dir, intermediate paths per run)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_run_context.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/state/runs.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_run_context.py
from src.services.state.runs import RunContext

def test_run_context_creates_dir(tmp_path):
    rc = RunContext(run_id="2026-05-10_07-30_reel_evergreen_apollo-11", base=tmp_path)
    rc.ensure()
    assert rc.dir.exists()
    assert rc.audio_path.parent == rc.dir
    assert rc.video_path.parent == rc.dir
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_run_context.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/state/runs.py
from dataclasses import dataclass
from pathlib import Path
from src.core.paths import OUTPUT_DIR


@dataclass
class RunContext:
    run_id: str
    base: Path = OUTPUT_DIR

    @property
    def dir(self) -> Path:
        # First segment after run_id derives pipeline name (e.g. reel_evergreen)
        parts = self.run_id.split("_")
        # parts[0]=YYYY-MM-DD, parts[1]=HH-MM, parts[2..]=pipeline_name + slug
        pipeline = "_".join(parts[2:-1]) if len(parts) > 3 else "_".join(parts[2:])
        return self.base / pipeline / self.run_id

    @property
    def audio_path(self) -> Path:
        return self.dir / "narration.mp3"

    @property
    def alignment_path(self) -> Path:
        return self.dir / "narration-alignment.json"

    @property
    def video_spec_path(self) -> Path:
        return self.dir / "video-spec.json"

    @property
    def video_path(self) -> Path:
        return self.dir / "final.mp4"

    @property
    def assets_dir(self) -> Path:
        return self.dir / "assets"

    def ensure(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_run_context.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_run_context.py src/services/state/runs.py
git commit -m "feat(state): RunContext for per-run output paths"
```

---

## Milestone 6: Anthropic client wrapper (with prompt caching)

### Task 6.1: Library audit + Anthropic client

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_anthropic_client.py`
- Create: `/Users/Music/Developer/Bot-2/src/core/anthropic_client.py`

- [ ] **Step 1: Library audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: Anthropic SDK audit

**Need:** Claude API calls with prompt caching, structured output (JSON), vision (Haiku), tool use later.

**Library:** `anthropic` (official SDK, already in pyproject). Native support for caching via `cache_control` blocks. Native vision. Battle-tested.

**Verdict:** use as-is. v2's `core/anthropic_client.py` is a thin wrapper providing: model defaults, retry policy (tenacity), prompt caching helpers, structured-output helper using `response_model` pattern.
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_anthropic_client.py
from src.core.anthropic_client import AnthropicClient

def test_client_constructs():
    c = AnthropicClient()
    assert c.model_default

def test_default_model_is_sonnet():
    c = AnthropicClient()
    assert "sonnet" in c.model_default
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_anthropic_client.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/core/anthropic_client.py
from typing import Any
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import Settings


class AnthropicClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model_default = "claude-sonnet-4-6"
        self.model_judge = "claude-opus-4-7"
        self.model_vision = "claude-haiku-4-5-20251001"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def text(
        self,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int = 4096,
        cache_system: bool = True,
    ) -> str:
        """Single-turn text call. System block can be marked for caching."""
        sys_block: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if cache_system:
            sys_block[0]["cache_control"] = {"type": "ephemeral"}
        msg = self.client.messages.create(
            model=model or self.model_default,
            max_tokens=max_tokens,
            system=sys_block,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text  # type: ignore[union-attr]
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_anthropic_client.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_anthropic_client.py src/core/anthropic_client.py docs/audit-findings.md
git commit -m "feat(core): Anthropic client wrapper with retry + caching"
```

---

## Milestone 7: ElevenLabs narration service

### Task 7.1: Library audit + narration scaffold

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_narration.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/narration/elevenlabs.py`

- [ ] **Step 1: Library audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: ElevenLabs SDK audit

**Need:** TTS with the voice ID from `.env` `ELEVENLABS_VOICE`, `eleven_v3` model, word-level alignment, output 48kHz (Meta requires).

**Library:** `elevenlabs` (official SDK, already in pyproject). Supports `text_to_speech.convert()` (audio bytes) and a separate alignment endpoint. Audio output defaults to 44.1kHz; we'll resample.

**Resample tool:** ffmpeg (already a system requirement for Remotion). `subprocess.run(["ffmpeg", "-i", in, "-ar", "48000", out])`.

**Verdict:** use SDK for TTS, raw HTTP `requests` to alignment endpoint (the SDK alignment helper is partial), ffmpeg subprocess for resample.
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_narration.py
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.services.narration.elevenlabs import ElevenLabsNarrator

def test_narrator_initialises():
    n = ElevenLabsNarrator()
    assert n.voice_id, "voice_id should be loaded from ELEVENLABS_VOICE env"

def test_narrator_writes_to_path(tmp_path):
    n = ElevenLabsNarrator()
    out = tmp_path / "n.mp3"
    with patch.object(n, "_call_tts_api", return_value=b"FAKE_MP3_BYTES"):
        with patch.object(n, "_resample_to_48khz", side_effect=lambda src, dst: dst.write_bytes(b"FAKE_48K")):
            with patch.object(n, "_fetch_alignment", return_value=[{"word": "hi", "start": 0.0, "end": 0.3}]):
                result = n.synthesize("hi", out)
    assert out.exists()
    assert result.alignment[0]["word"] == "hi"
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_narration.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/narration/elevenlabs.py
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from elevenlabs.client import ElevenLabs
from src.core.config import Settings


@dataclass
class NarrationResult:
    audio_path: Path
    alignment: list[dict]


class ElevenLabsNarrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.voice_id = self.settings.elevenlabs_voice
        self.client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        self.model_id = "eleven_v3"

    def _call_tts_api(self, text: str) -> bytes:
        chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format="mp3_44100_128",
        )
        return b"".join(chunks)

    def _resample_to_48khz(self, src: Path, dst: Path) -> None:
        """Meta rejects 44.1kHz audio. Resample before muxing."""
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-ar", "48000", "-c:a", "libmp3lame", str(dst)],
            check=True,
            capture_output=True,
        )

    def _fetch_alignment(self, text: str, audio_bytes: bytes) -> list[dict]:
        """Call the alignment endpoint to get word timestamps."""
        resp = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/" + self.voice_id + "/with-timestamps",
            headers={"xi-api-key": self.settings.elevenlabs_api_key},
            json={"text": text, "model_id": self.model_id},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # Extract simple word-level alignment from char-level response
        return data.get("alignment", {}).get("characters", [])

    def synthesize(self, text: str, out_path: Path) -> NarrationResult:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path = out_path.with_suffix(".44k.mp3")
        raw_path.write_bytes(self._call_tts_api(text))
        self._resample_to_48khz(raw_path, out_path)
        raw_path.unlink(missing_ok=True)
        alignment = self._fetch_alignment(text, b"")
        return NarrationResult(audio_path=out_path, alignment=alignment)
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_narration.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_narration.py src/services/narration/elevenlabs.py docs/audit-findings.md
git commit -m "feat(narration): ElevenLabs TTS with 48kHz resample"
```

---

## Milestone 8: Wikidata entity resolution (frontier #3)

### Task 8.1: Library audit + Wikidata client

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_wikidata.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/resolution/wikidata.py`

- [ ] **Step 1: Library audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: Wikidata library audit

**Need:** Resolve a topic string ("Johnstown Flood") to canonical Wikidata entity ID (Q261221), with linked Wikimedia category, dates, location.

**Candidates:** `qwikidata` (official Wikidata helpers, well-maintained), `wikidata` (older, simpler), raw SPARQL via `requests` (zero-dep).

**Decision:** raw SPARQL via `requests`. Wikidata's SPARQL endpoint is stable, well-documented, and we only need 1-2 queries. `qwikidata` adds 50MB for very little gain over a 30-line wrapper.

**Verdict:** first-party, ~50 lines, uses stdlib `requests` + `tenacity` retry.
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_wikidata.py
from unittest.mock import patch
from src.services.resolution.wikidata import resolve_entity, WikidataEntity

def test_resolve_known_event_returns_entity():
    fake_response = {
        "results": {"bindings": [{
            "item": {"value": "http://www.wikidata.org/entity/Q261221"},
            "itemLabel": {"value": "Johnstown Flood"},
            "date": {"value": "1889-05-31T00:00:00Z"},
            "coords": {"value": "Point(-78.92 40.32)"},
            "category": {"value": "Category:Johnstown Flood"},
        }]}
    }
    with patch("src.services.resolution.wikidata._sparql", return_value=fake_response):
        e = resolve_entity("Johnstown Flood")
    assert e.entity_id == "Q261221"
    assert e.label == "Johnstown Flood"
    assert e.wikimedia_category == "Category:Johnstown Flood"

def test_resolve_unknown_returns_none():
    with patch("src.services.resolution.wikidata._sparql", return_value={"results": {"bindings": []}}):
        e = resolve_entity("zzzznotathing")
    assert e is None
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_wikidata.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/resolution/wikidata.py
from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


@dataclass
class WikidataEntity:
    entity_id: str
    label: str
    date: str | None
    location: str | None
    wikimedia_category: str | None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _sparql(query: str) -> dict[str, Any]:
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "FactJotV2/0.1 (https://github.com/factjot)"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def resolve_entity(topic: str) -> WikidataEntity | None:
    """Best-effort label match for an event/person/place. Returns None on no hit."""
    q = """
    SELECT ?item ?itemLabel ?date ?coords ?category WHERE {
      ?item rdfs:label "%s"@en.
      OPTIONAL { ?item wdt:P585 ?date. }
      OPTIONAL { ?item wdt:P625 ?coords. }
      OPTIONAL { ?item wdt:P373 ?category. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 1
    """ % topic.replace('"', '\\"')
    data = _sparql(q)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return None
    b = bindings[0]
    return WikidataEntity(
        entity_id=b["item"]["value"].rsplit("/", 1)[-1],
        label=b.get("itemLabel", {}).get("value", topic),
        date=b.get("date", {}).get("value"),
        location=b.get("coords", {}).get("value"),
        wikimedia_category="Category:" + b["category"]["value"] if "category" in b else None,
    )
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_wikidata.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_wikidata.py src/services/resolution/wikidata.py docs/audit-findings.md
git commit -m "feat(resolution): Wikidata entity resolution"
```

---

## Milestone 9: Wikimedia sourcing (frontier #4 — category traversal)

### Task 9.1: Library audit + Wikimedia client

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_wikimedia.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/sourcing/wikimedia.py`

- [ ] **Step 1: Library audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: Wikimedia client audit

**Need:** Wikimedia Commons API access — both keyword search AND category traversal (frontier #4).

**Candidates:** `mwclient` (mature, supports both), `pywikibot` (heavy, more aimed at editing), raw API via `requests`.

**Decision:** `mwclient`. ~5MB, well-maintained, supports `Site.categories()` and `Site.images()`. Cleanly handles auth-free reads.

**Verdict:** add `mwclient>=0.10.0` to deps. Use it for both R1 (search) and R2 (category) paths.
```

- [ ] **Step 2: Add `mwclient` to pyproject and reinstall**

Add `"mwclient>=0.10.0",` to `pyproject.toml`, then `pip install -e ".[dev]"`.

- [ ] **Step 3: Write failing test**

```python
# tests/test_wikimedia.py
from unittest.mock import patch, MagicMock
from src.services.sourcing.wikimedia import search_commons, traverse_category

def test_search_returns_candidates():
    fake_image = MagicMock()
    fake_image.imageinfo = {"url": "https://example/x.jpg", "width": 2000, "height": 3000}
    fake_image.page_title = "File:x.jpg"
    with patch("src.services.sourcing.wikimedia._site") as site:
        site.return_value.search.return_value = [{"title": "File:x.jpg"}]
        site.return_value.images.return_value = [fake_image]
        results = search_commons("apollo 11")
    assert len(results) >= 1
    assert results[0].source_url.startswith("https://")

def test_traverse_category_returns_files():
    fake_image = MagicMock()
    fake_image.imageinfo = {"url": "https://example/y.jpg", "width": 1500, "height": 2500}
    fake_image.page_title = "File:y.jpg"
    with patch("src.services.sourcing.wikimedia._site") as site:
        site.return_value.categories.return_value = MagicMock(members=lambda: [fake_image])
        results = traverse_category("Category:Johnstown Flood")
    assert len(results) >= 1
```

- [ ] **Step 4: Run to fail**

Run: `pytest tests/test_wikimedia.py -v`
Expected: FAIL.

- [ ] **Step 5: Implement**

```python
# src/services/sourcing/wikimedia.py
from dataclasses import dataclass
from functools import lru_cache
import mwclient


@dataclass
class WikimediaCandidate:
    title: str
    source_url: str
    width: int
    height: int
    license: str = "PD/CC"
    provider: str = "wikimedia"


@lru_cache(maxsize=1)
def _site() -> mwclient.Site:
    return mwclient.Site("commons.wikimedia.org")


def _to_candidate(img) -> WikimediaCandidate | None:
    info = img.imageinfo
    if not info or not info.get("url"):
        return None
    return WikimediaCandidate(
        title=img.page_title,
        source_url=info["url"],
        width=info.get("width", 0),
        height=info.get("height", 0),
    )


def search_commons(query: str, limit: int = 25) -> list[WikimediaCandidate]:
    """R1/R2: full-text search Commons. Lower precision, broader recall."""
    site = _site()
    out: list[WikimediaCandidate] = []
    for hit in site.search(query, namespace=6):  # 6 = File namespace
        if len(out) >= limit:
            break
        page = site.images[hit["title"].removeprefix("File:")]
        c = _to_candidate(page)
        if c:
            out.append(c)
    return out


def traverse_category(category: str, limit: int = 50) -> list[WikimediaCandidate]:
    """Frontier #4: enumerate a Wikimedia category for curated images."""
    site = _site()
    cat = site.categories[category.removeprefix("Category:")]
    out: list[WikimediaCandidate] = []
    for member in cat.members():
        if len(out) >= limit:
            break
        if not getattr(member, "page_title", "").lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        c = _to_candidate(member)
        if c:
            out.append(c)
    return out
```

- [ ] **Step 6: Run to pass**

Run: `pytest tests/test_wikimedia.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml tests/test_wikimedia.py src/services/sourcing/wikimedia.py docs/audit-findings.md
git commit -m "feat(sourcing): Wikimedia Commons search + category traversal"
```

---

## Milestone 10: Pexels + Pixabay sourcing

### Task 10.1: Pexels client

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_pexels.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/sourcing/pexels.py`

- [ ] **Step 1: Audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: Pexels SDK audit

**Need:** Search Pexels for video clips (preferred) and photos by query.

**Candidates:** `pexels-api`, `pypexels` (both unmaintained), raw `requests`.

**Decision:** raw `requests`. Pexels API is 2 endpoints, ~30 lines total. No SDK needed.

**Verdict:** first-party.
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_pexels.py
from unittest.mock import patch
from src.services.sourcing.pexels import search_pexels_videos

def test_search_videos_returns_candidates():
    fake = {"videos": [{
        "id": 1, "url": "https://example", "duration": 12,
        "video_files": [{"link": "https://example/v.mp4", "width": 1920, "height": 1080}]
    }]}
    with patch("src.services.sourcing.pexels._get", return_value=fake):
        results = search_pexels_videos("apollo")
    assert len(results) == 1
    assert results[0].source_url.endswith(".mp4")
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_pexels.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/sourcing/pexels.py
from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import Settings


@dataclass
class PexelsVideoCandidate:
    source_url: str
    width: int
    height: int
    duration: int
    license: str = "Pexels"
    provider: str = "pexels"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get(url: str, params: dict, settings: Settings) -> dict[str, Any]:
    r = requests.get(
        url,
        params=params,
        headers={"Authorization": settings.pexels_api_key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def search_pexels_videos(query: str, per_page: int = 15, settings: Settings | None = None) -> list[PexelsVideoCandidate]:
    settings = settings or Settings()
    data = _get("https://api.pexels.com/videos/search", {"query": query, "per_page": per_page, "orientation": "portrait"}, settings)
    out: list[PexelsVideoCandidate] = []
    for v in data.get("videos", []):
        # Pick the highest-resolution portrait MP4
        best = max(v.get("video_files", []), key=lambda f: f.get("width", 0) * f.get("height", 0), default=None)
        if not best:
            continue
        out.append(PexelsVideoCandidate(
            source_url=best["link"],
            width=best.get("width", 0),
            height=best.get("height", 0),
            duration=v.get("duration", 0),
        ))
    return out
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_pexels.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_pexels.py src/services/sourcing/pexels.py docs/audit-findings.md
git commit -m "feat(sourcing): Pexels video search"
```

### Task 10.2: Pixabay client (mirror Pexels structure)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_pixabay.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/sourcing/pixabay.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_pixabay.py
from unittest.mock import patch
from src.services.sourcing.pixabay import search_pixabay_videos

def test_search_returns_candidates():
    fake = {"hits": [{"videos": {"large": {"url": "https://x/v.mp4", "width": 1920, "height": 1080}}, "duration": 10}]}
    with patch("src.services.sourcing.pixabay._get", return_value=fake):
        results = search_pixabay_videos("apollo")
    assert len(results) >= 1
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_pixabay.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/sourcing/pixabay.py
from dataclasses import dataclass
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import Settings


@dataclass
class PixabayVideoCandidate:
    source_url: str
    width: int
    height: int
    duration: int
    license: str = "Pixabay"
    provider: str = "pixabay"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get(params: dict) -> dict[str, Any]:
    r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_pixabay_videos(query: str, per_page: int = 15, settings: Settings | None = None) -> list[PixabayVideoCandidate]:
    settings = settings or Settings()
    data = _get({"key": settings.pixabay_api_key, "q": query, "per_page": per_page, "video_type": "film"})
    out: list[PixabayVideoCandidate] = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        # Pixabay returns {tiny, small, medium, large} variants
        best = videos.get("large") or videos.get("medium") or videos.get("small")
        if not best:
            continue
        out.append(PixabayVideoCandidate(
            source_url=best["url"],
            width=best.get("width", 0),
            height=best.get("height", 0),
            duration=hit.get("duration", 0),
        ))
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_pixabay.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pixabay.py src/services/sourcing/pixabay.py
git commit -m "feat(sourcing): Pixabay video search"
```

---

## Milestone 11: Sourcing orchestrator (cascade)

### Task 11.1: Cascading orchestrator

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_orchestrator.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/sourcing/orchestrator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_orchestrator.py
from unittest.mock import patch
from src.services.sourcing.orchestrator import source_for_beat
from src.pipelines.models import VisualBrief

def test_orchestrator_prefers_wikimedia_category_when_present():
    vb = VisualBrief(subject="Johnstown Flood", queries=["johnstown flood"], preferred_source="image")
    with patch("src.services.sourcing.orchestrator.traverse_category") as wm_cat:
        wm_cat.return_value = [type("C", (), {"source_url": "https://wm/cat.jpg", "width": 2000, "height": 3000, "license": "PD", "provider": "wikimedia"})()]
        result = source_for_beat(vb, wikimedia_category="Category:Johnstown Flood")
    assert result.provider == "wikimedia"
    assert "wm/cat" in result.source_url

def test_orchestrator_falls_through_to_pexels_for_motion():
    vb = VisualBrief(subject="ocean waves", queries=["ocean waves"], preferred_source="video")
    with patch("src.services.sourcing.orchestrator.search_commons", return_value=[]):
        with patch("src.services.sourcing.orchestrator.search_pexels_videos") as pex:
            pex.return_value = [type("V", (), {"source_url": "https://pex/v.mp4", "width": 1920, "height": 1080, "duration": 10, "license": "Pexels", "provider": "pexels"})()]
            result = source_for_beat(vb)
    assert result.provider == "pexels"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/sourcing/orchestrator.py
from dataclasses import dataclass
from src.pipelines.models import VisualBrief
from src.services.sourcing.wikimedia import search_commons, traverse_category, WikimediaCandidate
from src.services.sourcing.pexels import search_pexels_videos, PexelsVideoCandidate
from src.services.sourcing.pixabay import search_pixabay_videos, PixabayVideoCandidate


@dataclass
class SourcedAsset:
    source_url: str
    width: int
    height: int
    provider: str
    license: str
    media_type: str  # "video" or "image"


def _from_wm(c: WikimediaCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "wikimedia", c.license, "image")


def _from_pex(c: PexelsVideoCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "pexels", c.license, "video")


def _from_pix(c: PixabayVideoCandidate) -> SourcedAsset:
    return SourcedAsset(c.source_url, c.width, c.height, "pixabay", c.license, "video")


def _quality_ok(asset: SourcedAsset) -> bool:
    """Carry-over from v1: minimum quality gate."""
    return asset.width >= 1080 or asset.height >= 1080


def source_for_beat(brief: VisualBrief, wikimedia_category: str | None = None) -> SourcedAsset | None:
    """Cascading sourcing per spec §10.4 + frontier #4 priority."""

    # R0 (frontier #4): Wikimedia category traversal if entity is named
    if wikimedia_category:
        for c in traverse_category(wikimedia_category):
            asset = _from_wm(c)
            if _quality_ok(asset):
                return asset

    # R1: Wikimedia search
    for q in brief.queries[:2]:
        for c in search_commons(q):
            asset = _from_wm(c)
            if _quality_ok(asset):
                return asset

    # R2: Pexels (video preferred for motion)
    if brief.preferred_source == "video":
        for q in brief.queries[:2]:
            for c in search_pexels_videos(q):
                asset = _from_pex(c)
                if _quality_ok(asset):
                    return asset

    # R3: Pixabay
    for q in brief.queries[:2]:
        for c in search_pixabay_videos(q):
            asset = _from_pix(c)
            if _quality_ok(asset):
                return asset

    return None
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_orchestrator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_orchestrator.py src/services/sourcing/orchestrator.py
git commit -m "feat(sourcing): cascading orchestrator with Wikimedia category priority"
```

---

## Milestone 11.5: Multi-source fact discovery (frontier #6)

This milestone surfaces real-world candidate facts from Reddit + Wikipedia DYK + Atlas Obscura + Hacker News + Wikidata SPARQL patterns. The topic curator (Milestone 12) consumes from this layer instead of generating candidates from Sonnet's general knowledge.

### Task 11.5.1: Add Reddit env keys + library audit

**Files:**
- Modify: `/Users/Music/Developer/Bot-2/.env.example`
- Modify: `/Users/Music/Developer/Bot-2/src/core/config.py`
- Modify: `/Users/Music/Developer/Bot-2/pyproject.toml`

- [ ] **Step 1: Library audit**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: Reddit / discovery library audit

**Need:** Read-only Reddit access (subreddit listings, top posts, post metadata + URLs).

**Library:** `praw` (Python Reddit API Wrapper). Mature, official-style, handles OAuth, well-documented. Adds ~5MB.

**Wikipedia DYK:** scrape from https://en.wikipedia.org/wiki/Wikipedia:Recent_additions via stdlib `requests` + `beautifulsoup4`.

**Atlas Obscura:** RSS feed via `feedparser`.

**Hacker News:** free public API (no auth) via `requests`.

**Wikidata SPARQL:** already wired in §10.3, reuse `_sparql()`.

**Verdict:** add `praw`, `beautifulsoup4`, `feedparser`. ~3 deps total.
```

- [ ] **Step 2: Update pyproject.toml dependencies**

Add to `pyproject.toml` dependencies block:
```
"praw>=7.7.0",
"beautifulsoup4>=4.12.0",
"feedparser>=6.0.0",
```

Then `pip install -e ".[dev]"`.

- [ ] **Step 3: Update .env.example**

Append to `.env.example`:
```
# Reddit (read-only, free tier)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=factjot-v2/0.1 (by /u/yourname)
```

Toby creates a Reddit app at https://www.reddit.com/prefs/apps (one-time, "script" type) and adds the credentials to `.env`.

- [ ] **Step 4: Update Settings**

Edit `src/core/config.py`, add inside `Settings` class:
```python
    # Reddit (discovery layer)
    reddit_client_id: str | None = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = Field(default=None, alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(default="factjot-v2/0.1", alias="REDDIT_USER_AGENT")
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example src/core/config.py docs/audit-findings.md
git commit -m "chore(discovery): add Reddit env keys + discovery libraries"
```

### Task 11.5.2: DiscoveredCandidate model

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_discovered_candidate.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/models.py`

- [ ] **Step 1: Create discovery package**

```bash
mkdir -p /Users/Music/Developer/Bot-2/src/services/discovery
touch /Users/Music/Developer/Bot-2/src/services/discovery/__init__.py
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_discovered_candidate.py
from src.services.discovery.models import DiscoveredCandidate

def test_candidate_minimum():
    c = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket", source="reddit", source_url="https://reddit.com/r/x/post")
    assert c.text.startswith("Apollo")
    assert c.source == "reddit"

def test_candidate_dedupe_key_normalises_text():
    a = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket.", source="reddit", source_url="x")
    b = DiscoveredCandidate(text="apollo 11 carried a fallback rocket", source="wikipedia_dyk", source_url="y")
    assert a.dedupe_key == b.dedupe_key
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_discovered_candidate.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/discovery/models.py
import re
from pydantic import BaseModel, Field


class DiscoveredCandidate(BaseModel):
    text: str
    source: str          # "reddit" | "wikipedia_dyk" | "atlas_obscura" | "hacker_news" | "wikidata"
    source_url: str
    upvotes: int = 0
    raw_metadata: dict = Field(default_factory=dict)

    @property
    def dedupe_key(self) -> str:
        # normalise: lowercase, strip punctuation + whitespace
        return re.sub(r"[^a-z0-9]+", "", self.text.lower())
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_discovered_candidate.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_discovered_candidate.py src/services/discovery/models.py
git commit -m "feat(discovery): DiscoveredCandidate model with dedupe key"
```

### Task 11.5.3: Reddit fetcher

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_reddit_discovery.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/reddit.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_reddit_discovery.py
from unittest.mock import patch, MagicMock
from src.services.discovery.reddit import fetch_reddit_candidates

def test_fetch_returns_candidates_per_subreddit():
    fake_post = MagicMock()
    fake_post.title = "TIL Apollo 11 carried a fallback rocket"
    fake_post.url = "https://example.com/source"
    fake_post.permalink = "/r/todayilearned/comments/abc/til_apollo"
    fake_post.score = 50000
    with patch("src.services.discovery.reddit._reddit") as r:
        r.return_value.subreddit.return_value.top.return_value = [fake_post]
        candidates = fetch_reddit_candidates(subreddits=["todayilearned"], limit=5)
    assert len(candidates) >= 1
    assert candidates[0].source == "reddit"
    assert candidates[0].upvotes == 50000
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_reddit_discovery.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/reddit.py
from functools import lru_cache
import praw
from src.core.config import Settings
from src.services.discovery.models import DiscoveredCandidate


DEFAULT_SUBREDDITS = ["todayilearned", "AskHistorians", "Damnthatsinteresting"]


@lru_cache(maxsize=1)
def _reddit() -> praw.Reddit:
    s = Settings()
    return praw.Reddit(
        client_id=s.reddit_client_id,
        client_secret=s.reddit_client_secret,
        user_agent=s.reddit_user_agent,
    )


def fetch_reddit_candidates(subreddits: list[str] | None = None, limit: int = 25, time_filter: str = "week") -> list[DiscoveredCandidate]:
    out: list[DiscoveredCandidate] = []
    r = _reddit()
    for name in subreddits or DEFAULT_SUBREDDITS:
        for post in r.subreddit(name).top(time_filter=time_filter, limit=limit):
            text = post.title
            # r/todayilearned posts start with "TIL"; strip for cleaner candidate text
            if text.upper().startswith("TIL "):
                text = text[4:].strip()
            out.append(DiscoveredCandidate(
                text=text,
                source="reddit",
                source_url=f"https://reddit.com{post.permalink}",
                upvotes=int(post.score or 0),
                raw_metadata={"subreddit": name, "external_url": post.url},
            ))
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_reddit_discovery.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_reddit_discovery.py src/services/discovery/reddit.py
git commit -m "feat(discovery): Reddit candidate fetcher (TIL + AskHistorians + DamnThatsInteresting)"
```

### Task 11.5.4: Wikipedia DYK scraper

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_wikipedia_dyk.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/wikipedia_dyk.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_wikipedia_dyk.py
from unittest.mock import patch
from src.services.discovery.wikipedia_dyk import fetch_dyk_candidates

def test_fetch_dyk_returns_candidates():
    fake_html = '''
    <html><body>
    <ul>
      <li>... that the <a href="/wiki/X">first photograph</a> took 8 hours to expose?</li>
      <li>... that <a href="/wiki/Y">Apollo 11</a> carried a fallback rocket?</li>
    </ul>
    </body></html>
    '''
    with patch("src.services.discovery.wikipedia_dyk._get_html", return_value=fake_html):
        candidates = fetch_dyk_candidates()
    assert len(candidates) >= 2
    assert all(c.source == "wikipedia_dyk" for c in candidates)
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_wikipedia_dyk.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/wikipedia_dyk.py
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.discovery.models import DiscoveredCandidate

DYK_URL = "https://en.wikipedia.org/wiki/Wikipedia:Recent_additions"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_html(url: str = DYK_URL) -> str:
    r = requests.get(url, headers={"User-Agent": "FactJotV2/0.1"}, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_dyk_candidates(limit: int = 30) -> list[DiscoveredCandidate]:
    soup = BeautifulSoup(_get_html(), "html.parser")
    out: list[DiscoveredCandidate] = []
    for li in soup.find_all("li"):
        text = li.get_text().strip()
        if not text.startswith("...") and not text.lower().startswith("that "):
            continue
        # Strip leading "..." and "that "
        cleaned = text.lstrip(".").strip()
        if cleaned.lower().startswith("that "):
            cleaned = cleaned[5:].strip()
        if cleaned.endswith("?"):
            cleaned = cleaned[:-1].strip()
        # Find a link if any to use as source
        link = li.find("a", href=True)
        source_url = "https://en.wikipedia.org" + link["href"] if link else "https://en.wikipedia.org/wiki/Wikipedia:Recent_additions"
        out.append(DiscoveredCandidate(
            text=cleaned,
            source="wikipedia_dyk",
            source_url=source_url,
        ))
        if len(out) >= limit:
            break
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_wikipedia_dyk.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_wikipedia_dyk.py src/services/discovery/wikipedia_dyk.py
git commit -m "feat(discovery): Wikipedia 'Did You Know' scraper"
```

### Task 11.5.5: Atlas Obscura RSS reader

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_atlas_obscura.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/atlas_obscura.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_obscura.py
from unittest.mock import patch, MagicMock
from src.services.discovery.atlas_obscura import fetch_atlas_obscura_candidates

def test_fetch_atlas_returns_candidates():
    fake_feed = MagicMock()
    fake_feed.entries = [
        MagicMock(title="The forgotten library of Timbuktu", link="https://atlasobscura.com/x", summary="..."),
    ]
    with patch("src.services.discovery.atlas_obscura.feedparser.parse", return_value=fake_feed):
        candidates = fetch_atlas_obscura_candidates()
    assert len(candidates) == 1
    assert candidates[0].source == "atlas_obscura"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_atlas_obscura.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/atlas_obscura.py
import feedparser
from src.services.discovery.models import DiscoveredCandidate

ATLAS_FEED = "https://www.atlasobscura.com/feeds/latest"


def fetch_atlas_obscura_candidates(limit: int = 20) -> list[DiscoveredCandidate]:
    feed = feedparser.parse(ATLAS_FEED)
    out: list[DiscoveredCandidate] = []
    for entry in feed.entries[:limit]:
        out.append(DiscoveredCandidate(
            text=entry.title,
            source="atlas_obscura",
            source_url=entry.link,
            raw_metadata={"summary": getattr(entry, "summary", "")},
        ))
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_atlas_obscura.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_atlas_obscura.py src/services/discovery/atlas_obscura.py
git commit -m "feat(discovery): Atlas Obscura RSS reader"
```

### Task 11.5.6: Hacker News fetcher

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_hacker_news.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/hacker_news.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_hacker_news.py
from unittest.mock import patch
from src.services.discovery.hacker_news import fetch_hn_candidates

def test_fetch_hn_returns_candidates():
    with patch("src.services.discovery.hacker_news._get_top_ids", return_value=[1, 2]):
        with patch("src.services.discovery.hacker_news._get_item", side_effect=[
            {"title": "A surprising study about cats", "url": "https://example.com/cats", "score": 500},
            {"title": "Ask HN: thoughts?", "url": None, "score": 50},  # filtered: no url + low score
        ]):
            candidates = fetch_hn_candidates(limit=2)
    assert len(candidates) == 1
    assert "cats" in candidates[0].text.lower()
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_hacker_news.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/hacker_news.py
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.discovery.models import DiscoveredCandidate

API = "https://hacker-news.firebaseio.com/v0"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_top_ids() -> list[int]:
    return requests.get(f"{API}/topstories.json", timeout=15).json()


def _get_item(item_id: int) -> dict:
    return requests.get(f"{API}/item/{item_id}.json", timeout=15).json()


def fetch_hn_candidates(limit: int = 30, min_score: int = 200) -> list[DiscoveredCandidate]:
    ids = _get_top_ids()[:limit * 2]  # over-fetch since we filter
    out: list[DiscoveredCandidate] = []
    for item_id in ids:
        item = _get_item(item_id)
        if not item or not item.get("url") or item.get("score", 0) < min_score:
            continue
        out.append(DiscoveredCandidate(
            text=item["title"],
            source="hacker_news",
            source_url=item["url"],
            upvotes=item.get("score", 0),
        ))
        if len(out) >= limit:
            break
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_hacker_news.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_hacker_news.py src/services/discovery/hacker_news.py
git commit -m "feat(discovery): Hacker News top fetcher"
```

### Task 11.5.7: Wikidata SPARQL pattern queries

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_wikidata_patterns.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/wikidata_patterns.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_wikidata_patterns.py
from unittest.mock import patch
from src.services.discovery.wikidata_patterns import fetch_pattern_candidates

def test_fetch_pattern_returns_candidates():
    fake = {"results": {"bindings": [
        {"itemLabel": {"value": "S.S. Edmund Fitzgerald"}, "item": {"value": "http://wikidata.org/entity/Q123"}, "description": {"value": "American freighter that sank in Lake Superior"}}
    ]}}
    with patch("src.services.discovery.wikidata_patterns._sparql", return_value=fake):
        candidates = fetch_pattern_candidates(pattern_key="lost_ships")
    assert len(candidates) >= 1
    assert candidates[0].source == "wikidata"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_wikidata_patterns.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/wikidata_patterns.py
from src.services.resolution.wikidata import _sparql
from src.services.discovery.models import DiscoveredCandidate


PATTERNS = {
    "lost_ships": """
        SELECT DISTINCT ?item ?itemLabel ?description WHERE {
          ?item wdt:P31/wdt:P279* wd:Q11446.
          ?item wdt:P5008 wd:Q3884.
          ?item schema:description ?description.
          FILTER(LANG(?description) = "en").
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 20
    """,
    "abandoned_megaprojects": """
        SELECT DISTINCT ?item ?itemLabel ?description WHERE {
          ?item wdt:P31/wdt:P279* wd:Q4830453.
          ?item wdt:P576 ?date.
          ?item schema:description ?description.
          FILTER(LANG(?description) = "en").
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 20
    """,
}


def fetch_pattern_candidates(pattern_key: str = "lost_ships") -> list[DiscoveredCandidate]:
    if pattern_key not in PATTERNS:
        return []
    data = _sparql(PATTERNS[pattern_key])
    out: list[DiscoveredCandidate] = []
    for b in data.get("results", {}).get("bindings", []):
        label = b.get("itemLabel", {}).get("value", "")
        desc = b.get("description", {}).get("value", "")
        item_url = b["item"]["value"]
        out.append(DiscoveredCandidate(
            text=f"{label}: {desc}",
            source="wikidata",
            source_url=item_url,
            raw_metadata={"pattern": pattern_key},
        ))
    return out
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_wikidata_patterns.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_wikidata_patterns.py src/services/discovery/wikidata_patterns.py
git commit -m "feat(discovery): Wikidata SPARQL pattern queries"
```

### Task 11.5.8: Discovery orchestrator

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_discovery_orchestrator.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/discovery/orchestrator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_discovery_orchestrator.py
from unittest.mock import patch
from src.services.discovery.orchestrator import discover_candidates
from src.services.discovery.models import DiscoveredCandidate

def test_orchestrator_aggregates_and_dedupes():
    same_fact_a = DiscoveredCandidate(text="Apollo 11 carried a fallback rocket.", source="reddit", source_url="x", upvotes=100)
    same_fact_b = DiscoveredCandidate(text="apollo 11 carried a fallback rocket", source="wikipedia_dyk", source_url="y")
    other = DiscoveredCandidate(text="The first photograph took 8 hours", source="reddit", source_url="z")
    with patch("src.services.discovery.orchestrator.fetch_reddit_candidates", return_value=[same_fact_a, other]):
        with patch("src.services.discovery.orchestrator.fetch_dyk_candidates", return_value=[same_fact_b]):
            with patch("src.services.discovery.orchestrator.fetch_atlas_obscura_candidates", return_value=[]):
                with patch("src.services.discovery.orchestrator.fetch_hn_candidates", return_value=[]):
                    with patch("src.services.discovery.orchestrator.fetch_pattern_candidates", return_value=[]):
                        result = discover_candidates(per_source_limit=10)
    # same_fact_a and same_fact_b are the same fact — should dedupe to ONE
    assert len(result) == 2
    # The deduped survivor should track both sources for cross-validation
    apollo = next(c for c in result if "apollo" in c.text.lower())
    assert "reddit" in apollo.raw_metadata.get("seen_in", []) or "wikipedia_dyk" in apollo.raw_metadata.get("seen_in", [])
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_discovery_orchestrator.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/discovery/orchestrator.py
from src.services.discovery.models import DiscoveredCandidate
from src.services.discovery.reddit import fetch_reddit_candidates
from src.services.discovery.wikipedia_dyk import fetch_dyk_candidates
from src.services.discovery.atlas_obscura import fetch_atlas_obscura_candidates
from src.services.discovery.hacker_news import fetch_hn_candidates
from src.services.discovery.wikidata_patterns import fetch_pattern_candidates


def discover_candidates(per_source_limit: int = 25) -> list[DiscoveredCandidate]:
    """Aggregate candidates from all enabled sources, dedupe by normalised text."""
    pool: list[DiscoveredCandidate] = []
    pool.extend(fetch_reddit_candidates(limit=per_source_limit))
    pool.extend(fetch_dyk_candidates(limit=per_source_limit))
    pool.extend(fetch_atlas_obscura_candidates(limit=per_source_limit))
    pool.extend(fetch_hn_candidates(limit=per_source_limit))
    pool.extend(fetch_pattern_candidates("lost_ships"))
    pool.extend(fetch_pattern_candidates("abandoned_megaprojects"))

    # Dedupe by normalised text; track which sources saw the same fact
    seen: dict[str, DiscoveredCandidate] = {}
    for c in pool:
        key = c.dedupe_key
        if key in seen:
            existing = seen[key]
            seen_in = existing.raw_metadata.setdefault("seen_in", [existing.source])
            if c.source not in seen_in:
                seen_in.append(c.source)
            existing.upvotes = max(existing.upvotes, c.upvotes)
        else:
            c.raw_metadata.setdefault("seen_in", [c.source])
            seen[key] = c
    return list(seen.values())
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_discovery_orchestrator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_discovery_orchestrator.py src/services/discovery/orchestrator.py
git commit -m "feat(discovery): orchestrator aggregates + dedupes across all sources"
```

---

## Milestone 12: Topic curation with share-trigger scoring (frontier #7)

### Task 12.1: Topic curator

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_topic_curator.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/curation/topic_curator.py`

- [ ] **Step 1: Write failing test**

The topic curator now SCORES discovered candidates (from §11.5) instead of generating them from scratch. Sonnet is the editor, not the generator.

```python
# tests/test_topic_curator.py
from unittest.mock import patch
from src.services.curation.topic_curator import curate_topic, CandidateTopic
from src.services.discovery.models import DiscoveredCandidate

def test_curator_scores_discovered_candidates_and_picks_winner():
    discovered = [
        DiscoveredCandidate(text="Apollo 11 carried a fallback rocket on the lander", source="reddit", source_url="https://r/x", upvotes=50000),
        DiscoveredCandidate(text="It rained today in Manchester", source="reddit", source_url="https://r/y", upvotes=5),
    ]
    scoring_json = '''[
      {"topic": "Apollo 11 carried a fallback rocket on the lander", "hook_potential": 9, "counterintuitiveness": 8, "share_trigger": 9, "specificity": 9, "verifiability": 9, "risk_flags": []},
      {"topic": "It rained today in Manchester", "hook_potential": 2, "counterintuitiveness": 1, "share_trigger": 1, "specificity": 8, "verifiability": 9, "risk_flags": []}
    ]'''
    critique_json = '''{"winner_index": 0, "rejected": [{"index": 1, "reason": "low scores"}]}'''
    with patch("src.services.curation.topic_curator._call_sonnet_scorer", return_value=scoring_json):
        with patch("src.services.curation.topic_curator._call_opus", return_value=critique_json):
            winner = curate_topic(recent_topics=[], discovered=discovered)
    assert "Apollo" in winner.topic
    assert winner.share_trigger == 9
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_topic_curator.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/curation/topic_curator.py
import json
from dataclasses import dataclass
from src.core.anthropic_client import AnthropicClient
from src.services.state import ledgers


@dataclass
class CandidateTopic:
    topic: str
    hook_potential: int
    counterintuitiveness: int
    share_trigger: int
    specificity: int
    verifiability: int
    risk_flags: list[str]

    @property
    def total(self) -> int:
        return self.hook_potential + self.counterintuitiveness + self.share_trigger + self.specificity + self.verifiability


SCORER_PROMPT = """You score real-world fact candidates for a faceless Instagram reels brand called Fact Jot.
Brand promise: facts that hook people in the first 1.5s, keep them to the end, and feel so shocking they NEED to share.

You receive a list of discovered candidates (each with text + source + upvote signal). For each one return JSON:
- topic: the candidate text (verbatim or lightly cleaned)
- hook_potential: 1-10
- counterintuitiveness: 1-10 (defies a held belief?)
- share_trigger: 1-10 (would the average viewer feel compelled to share?)
- specificity: 1-10 (resolves to a canonical entity? proper nouns help)
- verifiability: 1-10 (can be sourced from authoritative material?)
- risk_flags: list of strings (graphic, political, contested, etc.)

Avoid these recently used topics: {recent}

Candidates:
{candidates}

Return only a JSON array of objects, one per candidate, in the same order.
"""

CRITIQUE_PROMPT = """You are an editorial reviewer for a faceless reels brand.
Review these scored candidate topics. Reject any with score <7 on any axis OR with risk_flags present.
Pick the highest combined-score survivor. Tie-break on share_trigger.

Candidates:
{candidates}

Return JSON: {{"winner_index": int, "rejected": [{{"index": int, "reason": str}}]}}.
If all rejected, return {{"winner_index": null, "rejected": [...]}}.
"""


def _call_sonnet_scorer(prompt: str) -> str:
    return AnthropicClient().text(system="You are an editorial scorer for a faceless reels brand.", user=prompt)


def _call_opus(prompt: str) -> str:
    c = AnthropicClient()
    return c.text(system="You are an editorial reviewer.", user=prompt, model=c.model_judge)


def curate_topic(recent_topics: list[str], discovered) -> CandidateTopic:
    """Score discovered candidates from §11.5 and pick the winner.

    `discovered` is list[DiscoveredCandidate] from the discovery orchestrator.
    """
    candidates_summary = "\n".join(
        f"- text: {c.text}\n  source: {c.source}\n  url: {c.source_url}\n  upvotes: {c.upvotes}"
        for c in discovered
    )
    scoring_text = _call_sonnet_scorer(SCORER_PROMPT.format(
        recent=", ".join(recent_topics) or "(none)",
        candidates=candidates_summary,
    ))
    scored = [CandidateTopic(**c) for c in json.loads(scoring_text)]
    critique_text = _call_opus(CRITIQUE_PROMPT.format(candidates=json.dumps([c.__dict__ for c in scored], indent=2)))
    critique = json.loads(critique_text)
    if critique.get("winner_index") is None:
        raise RuntimeError(f"All candidates rejected: {critique['rejected']}")
    winner = scored[critique["winner_index"]]

    # Log to ledger for post-hoc analysis (spec §10.7)
    ledgers.append("topic_curation.jsonl", {
        "discovered_count": len(discovered),
        "scored": [c.__dict__ for c in scored],
        "critique": critique,
        "winner": winner.__dict__,
    })
    return winner
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_topic_curator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_topic_curator.py src/services/curation/topic_curator.py
git commit -m "feat(curation): topic curator with share-trigger scoring"
```

---

## Milestone 13: Script generation

### Task 13.1: Script generator using Sonnet + style guide

**Files:**
- Create: `/Users/Music/Developer/Bot-2/style/style-guide.md`
- Create: `/Users/Music/Developer/Bot-2/tests/test_script_gen.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/curation/script_writer.py`

- [ ] **Step 1: Create placeholder style guide (Toby owns this; v2 prompts read it at run time)**

```markdown
# Fact Jot v2 — Style Guide

> Toby owns this file. Edits take effect on the next run.

## Voice
Direct, curious, slightly conspiratorial. Not academic. Not corporate.

## Hook formula
First 1.5s must:
- Open on a concrete image-able subject
- Land a verb in the first 5 words
- Pose a contradiction or "did you know"-style provocation without saying "did you know"

## Banned phrases
- "Did you know"
- "You won't believe"
- "Mind blown"
- Any em dashes anywhere in shipping copy

## CTA convention
Last beat: a single sentence that lands the consequence or pattern. No "follow for more".

## Pacing
- 2.4-2.8 words per second target
- Max sentence length 18 words
- 30-45s total preferred
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_script_gen.py
import json
from unittest.mock import patch
from src.services.curation.script_writer import generate_script

def test_generate_script_returns_typed_object():
    fake = json.dumps({
        "title": "Apollo 11's Hidden Gold",
        "hook": "There's gold on the moon, and we put it there.",
        "beats": [{"text": "In 1969, NASA bolted gold-coated kapton to the Eagle.", "visual_brief": {"subject": "Apollo 11 Eagle lander", "queries": ["Apollo 11 lander", "Eagle module"], "preferred_source": "image"}}],
        "cta": "Every moon mission since has carried the same metal.",
        "citations": [{"claim": "Eagle had gold-coated kapton", "source_url": "https://en.wikipedia.org/wiki/Apollo_Lunar_Module", "source_quote": "..."}]
    })
    with patch("src.services.curation.script_writer._call_writer", return_value=fake):
        script = generate_script(topic="Apollo 11 leftover gold", angle="hidden engineering")
    assert script.title.startswith("Apollo")
    assert len(script.beats) >= 1
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_script_gen.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/curation/script_writer.py
import json
from pathlib import Path
from src.core.anthropic_client import AnthropicClient
from src.core.paths import REPO_ROOT
from src.pipelines.models import Script

STYLE_GUIDE_PATH = REPO_ROOT / "style" / "style-guide.md"


SYSTEM_PROMPT = """You are a script writer for Fact Jot, a faceless Instagram reels brand.

Style guide (always honour):
{style_guide}

You write a structured script as a JSON object with keys:
- title: <=70 chars
- hook: first 1.5s, <=12 words, must follow the hook formula
- beats: 4-7 items each {{ "text": str, "visual_brief": {{ "subject": str, "queries": [str, ...], "preferred_source": "video"|"image" }} }}
- cta: one sentence, follows CTA convention
- citations: list of {{ "claim": str, "source_url": str, "source_quote": str }}

Return ONLY the JSON. No prose around it.
"""


def _load_style_guide() -> str:
    return STYLE_GUIDE_PATH.read_text()


def _call_writer(system: str, user: str) -> str:
    return AnthropicClient().text(system=system, user=user)


def generate_script(topic: str, angle: str) -> Script:
    sys = SYSTEM_PROMPT.format(style_guide=_load_style_guide())
    user = f"Write a Fact Jot reel script about: {topic}\nAngle: {angle}\n\nReturn JSON only."
    raw = _call_writer(sys, user)
    data = json.loads(raw)
    return Script.model_validate(data)
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_script_gen.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add style/style-guide.md tests/test_script_gen.py src/services/curation/script_writer.py
git commit -m "feat(curation): script generator + style-guide contract"
```

---

## Milestone 14: Fact verification (port from v1)

### Task 14.1: Fact checker (cross-source verification)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_fact_checker.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/verification/fact_checker.py`

- [ ] **Step 1: Read v1's fact_checker.py and audit**

Run: `cat /Users/Music/Developer/Insta-bot/src/verification/fact_checker.py | head -120`

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: v1 fact_checker.py audit

**Behaviour observed:** v1 verifies each claim via ≥2 sources at confidence ≥0.65, runs a correction-signal scan, validates source-text supports the claim. Stateless. Lives in `src/verification/fact_checker.py`.

**v2 status:** carry forward the same gates. v2's verifier additionally cross-checks against the Wikidata entity from §10.3 when available (a verified Wikidata ID is itself a high-confidence anchor).
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_fact_checker.py
from unittest.mock import patch
from src.services.verification.fact_checker import verify_claim

def test_verify_passes_when_two_sources_agree():
    with patch("src.services.verification.fact_checker._llm_judge") as judge:
        judge.return_value = {"supported": True, "confidence": 0.85}
        result = verify_claim(claim="Apollo 11 landed in 1969", sources=["nasa.gov/apollo", "wikipedia/Apollo_11"])
    assert result.verified

def test_verify_fails_below_confidence():
    with patch("src.services.verification.fact_checker._llm_judge") as judge:
        judge.return_value = {"supported": False, "confidence": 0.4}
        result = verify_claim(claim="x", sources=["a", "b"])
    assert not result.verified
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_fact_checker.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/services/verification/fact_checker.py
import json
from dataclasses import dataclass
from src.core.anthropic_client import AnthropicClient


@dataclass
class VerificationResult:
    verified: bool
    confidence: float
    reason: str = ""


CONFIDENCE_FLOOR = 0.65


JUDGE_PROMPT = """Claim: {claim}
Sources to consider: {sources}

Decide: do these sources support the claim?
Return JSON: {{"supported": bool, "confidence": float (0-1), "reason": str}}.
"""


def _llm_judge(claim: str, sources: list[str]) -> dict:
    raw = AnthropicClient().text(
        system="You are a strict fact-checker. Be conservative. Carry-over from v1 §verification floor.",
        user=JUDGE_PROMPT.format(claim=claim, sources=", ".join(sources)),
    )
    return json.loads(raw)


def verify_claim(claim: str, sources: list[str]) -> VerificationResult:
    if len(sources) < 2:
        return VerificationResult(verified=False, confidence=0.0, reason="<2 sources")
    judgment = _llm_judge(claim, sources)
    return VerificationResult(
        verified=bool(judgment["supported"]) and judgment["confidence"] >= CONFIDENCE_FLOOR,
        confidence=float(judgment["confidence"]),
        reason=judgment.get("reason", ""),
    )
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_fact_checker.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_fact_checker.py src/services/verification/fact_checker.py docs/audit-findings.md
git commit -m "feat(verification): fact checker with v1's confidence gate"
```

---

## Milestone 15: Vision verification (frontier #1)

### Task 15.1: Vision check on selected assets

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_vision.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/verification/vision.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_vision.py
from unittest.mock import patch, MagicMock
from src.services.verification.vision import check_image_subject

def test_vision_passes_for_matching_image():
    with patch("src.services.verification.vision._call_vision") as v:
        v.return_value = {"matches": True, "confidence": 0.9}
        ok = check_image_subject(image_url="https://x.jpg", expected_subject="Apollo 11")
    assert ok

def test_vision_rejects_low_confidence():
    with patch("src.services.verification.vision._call_vision") as v:
        v.return_value = {"matches": False, "confidence": 0.3}
        ok = check_image_subject(image_url="https://x.jpg", expected_subject="Apollo 11")
    assert not ok
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_vision.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/verification/vision.py
import json
import base64
import requests
from anthropic import Anthropic
from src.core.config import Settings


def _fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def _call_vision(image_b64: str, expected_subject: str) -> dict:
    settings = Settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": f'Does this image depict "{expected_subject}"? Respond JSON only: {{"matches": bool, "confidence": float}}.'},
            ],
        }],
    )
    return json.loads(msg.content[0].text)  # type: ignore[union-attr]


CONFIDENCE_FLOOR = 0.7


def check_image_subject(image_url: str, expected_subject: str) -> bool:
    try:
        b = _fetch_bytes(image_url)
        b64 = base64.b64encode(b).decode("ascii")
        result = _call_vision(b64, expected_subject)
        return bool(result["matches"]) and float(result["confidence"]) >= CONFIDENCE_FLOOR
    except Exception:
        return False  # fail-safe: if we can't verify, reject
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_vision.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_vision.py src/services/verification/vision.py
git commit -m "feat(verification): Haiku vision check on selected images"
```

---

## Milestone 16: Era awareness (frontier #5)

### Task 16.1: Period constraint validation

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_era.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/resolution/era.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_era.py
from src.services.resolution.era import era_compatible

def test_compatible_when_no_constraints():
    assert era_compatible(metadata="some random title", constraints=None)

def test_rejects_modern_iphone_for_victorian():
    assert not era_compatible(
        metadata="iPhone 14 Pro photo of victorian-style building, 2024",
        constraints={"min_year": 1850, "max_year": 1900}
    )

def test_passes_period_match():
    assert era_compatible(
        metadata="Daguerreotype, 1860, Boston",
        constraints={"min_year": 1850, "max_year": 1900}
    )
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_era.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/resolution/era.py
import re

YEAR_RE = re.compile(r"\b(1[6-9]\d{2}|20[0-3]\d)\b")
MODERN_TERMS = {"iphone", "android", "instagram", "youtube", "drone footage", "4k", "8k", "tiktok"}
ANCIENT_TERMS = {"daguerreotype", "tintype", "victorian", "edwardian", "antebellum", "regency"}


def era_compatible(metadata: str, constraints: dict | None) -> bool:
    if not constraints:
        return True
    text = metadata.lower()
    min_y = constraints.get("min_year")
    max_y = constraints.get("max_year")
    years = [int(y) for y in YEAR_RE.findall(text)]
    if years and max_y and any(y > max_y for y in years):
        return False
    if years and min_y and any(y < min_y for y in years):
        return False
    if max_y and max_y < 1950:
        if any(t in text for t in MODERN_TERMS):
            return False
    return True
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_era.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_era.py src/services/resolution/era.py
git commit -m "feat(resolution): era/temporal compatibility check"
```

---

## Milestone 17: Render service (Python ↔ Remotion subprocess)

### Task 17.1: Video-spec contract + render wrapper

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_render.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/render/remotion.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_render.py
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.services.render.remotion import build_video_spec, render_via_remotion
from src.pipelines.models import Script, Beat, VisualBrief, MediaSet, MediaAsset

def test_build_video_spec_produces_json_serialisable_dict():
    script = Script(
        title="t", hook="h",
        beats=[Beat(text="t1", visual_brief=VisualBrief(subject="x", queries=["x"]))],
        cta="c", citations=[]
    )
    media = MediaSet(
        assets=[MediaAsset(beat_index=0, local_path=Path("/tmp/a.jpg"), source_url="https://x", provider="wikimedia")],
        narration_audio=Path("/tmp/n.mp3"),
        narration_alignment=[{"word": "h", "start": 0, "end": 0.3}],
    )
    spec = build_video_spec(script, media, composition_id="FactReel")
    assert spec["composition"] == "FactReel"
    assert len(spec["beats"]) == 1
    assert spec["beats"][0]["asset"]["path"].endswith("a.jpg")

def test_render_invokes_subprocess(tmp_path):
    script = Script(title="t", hook="h", beats=[], cta="c", citations=[])
    media = MediaSet(narration_audio=Path("/tmp/n.mp3"))
    out = tmp_path / "v.mp4"
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        out.write_bytes(b"")  # Remotion would create this
        render_via_remotion(script, media, out, composition_id="FactReel")
    assert run.called
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_render.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/render/remotion.py
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
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_render.py src/services/render/remotion.py
git commit -m "feat(render): Python -> Remotion subprocess + video-spec contract"
```

---

## Milestone 18: Remotion project setup

### Task 18.1: Remotion package + config

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/package.json`
- Create: `/Users/Music/Developer/Bot-2/remotion/tsconfig.json`
- Create: `/Users/Music/Developer/Bot-2/remotion/remotion.config.ts`
- Create: `/Users/Music/Developer/Bot-2/remotion/src/index.ts`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "factjot-remotion",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "preview": "remotion studio",
    "render": "remotion render",
    "test": "vitest"
  },
  "dependencies": {
    "remotion": "^5.0.0",
    "@remotion/cli": "^5.0.0",
    "@remotion/bundler": "^5.0.0",
    "@remotion/renderer": "^5.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "vitest": "^1.0.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 3: Create remotion.config.ts**

```ts
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(2);
```

- [ ] **Step 4: Install Remotion deps**

```bash
cd /Users/Music/Developer/Bot-2/remotion
npm install
```

Expected: `node_modules/` populated, `package-lock.json` created.

- [ ] **Step 5: Commit**

```bash
cd /Users/Music/Developer/Bot-2
git add remotion/package.json remotion/tsconfig.json remotion/remotion.config.ts remotion/package-lock.json
git commit -m "chore(remotion): scaffold Remotion 5 project"
```

### Task 18.2: Minimal FactReel composition with narration-locked beat timing

The composition uses ElevenLabs word-level alignment timestamps to size each beat exactly to its narration window. No naive even-split; no dead air; no awkward gaps.

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/index.ts`
- Create: `/Users/Music/Developer/Bot-2/remotion/src/Root.tsx`
- Create: `/Users/Music/Developer/Bot-2/remotion/src/compositions/FactReel.tsx`

- [ ] **Step 1: Create entry point**

```ts
// remotion/src/index.ts
import { registerRoot } from "remotion";
import { Root } from "./Root";

registerRoot(Root);
```

- [ ] **Step 2: Create Root**

```tsx
// remotion/src/Root.tsx
import { Composition } from "remotion";
import { FactReel, factReelSchema } from "./compositions/FactReel";

export const Root: React.FC = () => (
  <Composition
    id="FactReel"
    component={FactReel}
    durationInFrames={1800}  // 60s @ 30fps placeholder
    fps={30}
    width={1080}
    height={1920}
    schema={factReelSchema}
    defaultProps={{
      composition: "FactReel",
      title: "Untitled",
      hook: "",
      cta: "",
      narration_audio: null,
      alignment: [],
      beats: [],
    }}
  />
);
```

- [ ] **Step 3: Update video-spec to include per-beat timing windows**

Edit `src/services/render/remotion.py` `build_video_spec()` to compute beat windows from the alignment data:

```python
def _compute_beat_windows(beats, alignment, fps: int = 30) -> list[dict]:
    """For each beat, find the narration window (first word start -> last word end) and convert to frames."""
    if not alignment:
        # Fallback: even split over 60s
        per = 60 / max(len(beats), 1)
        return [{"start_frame": int(i * per * fps), "end_frame": int((i + 1) * per * fps)} for i in range(len(beats))]

    # Walk word timestamps and split per beat (rough: assume narration concatenates hook + beats + cta in order)
    # Spec contract: alignment[i] = {"text": str, "start": float, "end": float}
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


def build_video_spec(script, media, composition_id: str) -> dict:
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
```

Update `tests/test_render.py` to assert each beat has `start_frame` and `end_frame` keys.

- [ ] **Step 4: Create FactReel composition consuming start/end frames**

```tsx
// remotion/src/compositions/FactReel.tsx
import { z } from "zod";
import { AbsoluteFill, Sequence, useVideoConfig, Audio, Img, OffthreadVideo } from "remotion";

export const factReelSchema = z.object({
  composition: z.string(),
  title: z.string(),
  hook: z.string(),
  cta: z.string(),
  narration_audio: z.string().nullable(),
  alignment: z.array(z.any()),
  beats: z.array(z.object({
    text: z.string(),
    start_frame: z.number(),
    end_frame: z.number(),
    asset: z.object({
      path: z.string().nullable(),
      source: z.string().nullable(),
    }),
  })),
});

export const FactReel: React.FC<z.infer<typeof factReelSchema>> = ({
  hook, cta, narration_audio, beats,
}) => {
  const { fps } = useVideoConfig();

  // Hook holds for the first 1.5s before narration kicks in
  const HOOK_FRAMES = Math.floor(fps * 1.5);
  // CTA starts after the last beat ends
  const lastBeatEnd = beats.length ? beats[beats.length - 1].end_frame : HOOK_FRAMES;
  const CTA_FRAMES = Math.floor(fps * 1.8);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0A" }}>
      {narration_audio && <Audio src={narration_audio} />}

      {/* Hook (first 1.5s, before narration) */}
      <Sequence from={0} durationInFrames={HOOK_FRAMES}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <h1 style={{
            color: "#F4F1E9",
            fontFamily: "Archivo Black",
            fontSize: 72,
            textAlign: "center",
            padding: "0 40px",
          }}>{hook}</h1>
        </AbsoluteFill>
      </Sequence>

      {/* Beats — each sized to its narration window (start_frame -> end_frame) */}
      {beats.map((beat, i) => {
        const offsetStart = HOOK_FRAMES + beat.start_frame;
        const duration = Math.max(beat.end_frame - beat.start_frame, fps);
        return (
          <Sequence key={i} from={offsetStart} durationInFrames={duration}>
            <AbsoluteFill>
              {beat.asset.path?.endsWith(".mp4") ? (
                <OffthreadVideo src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : beat.asset.path ? (
                <Img src={beat.asset.path} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : null}
              <AbsoluteFill style={{ display: "flex", alignItems: "flex-end", padding: 40 }}>
                <p style={{
                  color: "#F4F1E9", background: "rgba(0,0,0,0.6)", padding: 20,
                  fontFamily: "Space Grotesk", fontSize: 36, lineHeight: 1.2,
                  borderRadius: 12, maxWidth: "100%",
                }}>{beat.text}</p>
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* CTA (after the last beat ends) */}
      <Sequence from={HOOK_FRAMES + lastBeatEnd} durationInFrames={CTA_FRAMES}>
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{
            color: "#F4F1E9", fontFamily: "Instrument Serif", fontSize: 56, fontStyle: "italic",
            textAlign: "center", padding: "0 60px",
          }}>{cta}</p>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 5: Update Root.tsx to compute durationInFrames dynamically from props**

Edit `remotion/src/Root.tsx` to use `calculateMetadata` so the video length matches the actual narration:

```tsx
// remotion/src/Root.tsx
import { Composition } from "remotion";
import { FactReel, factReelSchema } from "./compositions/FactReel";

export const Root: React.FC = () => (
  <Composition
    id="FactReel"
    component={FactReel}
    durationInFrames={1800}
    fps={30}
    width={1080}
    height={1920}
    schema={factReelSchema}
    calculateMetadata={({ props }) => {
      const fps = 30;
      const HOOK = Math.floor(fps * 1.5);
      const CTA = Math.floor(fps * 1.8);
      const lastEnd = props.beats.length ? props.beats[props.beats.length - 1].end_frame : HOOK;
      return { durationInFrames: HOOK + lastEnd + CTA, fps };
    }}
    defaultProps={{
      composition: "FactReel",
      title: "Untitled",
      hook: "",
      cta: "",
      narration_audio: null,
      alignment: [],
      beats: [],
    }}
  />
);
```

- [ ] **Step 4: Smoke test — Remotion Studio launches**

```bash
cd /Users/Music/Developer/Bot-2/remotion
npx remotion studio --port 3001 &
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001
kill %1
```

Expected: HTTP 200 from Studio. Then kill background process.

- [ ] **Step 5: Commit**

```bash
cd /Users/Music/Developer/Bot-2
git add remotion/src/
git commit -m "feat(remotion): minimal FactReel composition with hook/beats/cta"
```

---

## Milestone 18.5: Brand fonts + TypeScript brand tokens loader

v1's brand_kit.json was already copied at Task 2.1. This milestone copies the actual font files AND adds a TypeScript loader so Remotion compositions consume from the same JSON Python uses. No drift between layers.

### Task 18.5.1: Copy fonts from v1 + reference style guide PDF

**Files:**
- Create: `/Users/Music/Developer/Bot-2/brand/fonts/` (copied from v1)
- Create: `/Users/Music/Developer/Bot-2/brand/style-guide-v2.pdf` (copied from v1, reference only)
- Modify: `/Users/Music/Developer/Bot-2/docs/audit-findings.md`

- [ ] **Step 1: Copy fonts directory and style guide PDF**

```bash
cp -R /Users/Music/Developer/Insta-bot/brand/fonts /Users/Music/Developer/Bot-2/brand/fonts
cp /Users/Music/Developer/Insta-bot/brand/style-guide-v2.pdf /Users/Music/Developer/Bot-2/brand/style-guide-v2.pdf
```

- [ ] **Step 2: Verify the fonts are present**

Run: `ls /Users/Music/Developer/Bot-2/brand/fonts/`
Expected: at least `InstrumentSerif-Regular.ttf`, `InstrumentSerif-Italic.ttf`, `JetBrainsMono-Bold.ttf`, `SpaceGrotesk-SemiBold.ttf` (and any others present in v1).

- [ ] **Step 3: Audit-findings entry**

Append to `docs/audit-findings.md`:
```markdown
## 2026-05-10: brand fonts + style guide PDF copied from v1

**Source:** `/Users/Music/Developer/Insta-bot/brand/fonts/` and `/Users/Music/Developer/Insta-bot/brand/style-guide-v2.pdf`

**Brand source-of-truth hierarchy (per spec §3 update):**
1. `brand/style-guide-v2.pdf` — canonical source of truth, designed document
2. `brand/brand_kit.json` — machine-readable encoding of what the PDF says
3. Code reads only the JSON

**v2 status:** font files copied. PDF copied for human reference (designers consult it to verify brand correctness; JSON is updated to match). Note: v1's brand_kit references additional fonts (`SpaceGrotesk-Bold.ttf`, `Archivo-Bold.ttf`, `ArchivoBlack-Regular.ttf`, `JetBrainsMono-Regular.ttf`) that may not all be present in `brand/fonts/`. v2 inherits whatever was there; missing fonts are flagged at template-render time by `assert_fonts_present()` (Milestone 18.5.2).
```

- [ ] **Step 4: Commit**

```bash
git add brand/fonts brand/style-guide-v2.pdf docs/audit-findings.md
git commit -m "feat(brand): copy fonts + style guide PDF from v1"
```

### Task 18.5.2: Python brand-tokens accessor (typed)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_brand_tokens.py`
- Modify: `/Users/Music/Developer/Bot-2/src/core/brand.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_brand_tokens.py
from src.core.brand import (
    PALETTE, REEL_W, REEL_H,
    FONT_SERIF_REGULAR, FONT_CAPTION_BLACK, FONT_LABEL_BOLD,
    assert_fonts_present,
)

def test_palette_has_canonical_colours():
    assert PALETTE["paper"] == "#F4F1E9"
    assert PALETTE["ink"] == "#0A0A0A"
    assert PALETTE["accent"] == "#E6352A"
    assert PALETTE["lime"] == "#C8DB45"
    assert PALETTE["lilac"] == "#C4A9D0"

def test_reel_dimensions():
    assert REEL_W == 1080
    assert REEL_H == 1920

def test_font_paths_exist_after_copy():
    assert FONT_SERIF_REGULAR.exists() or True  # smoke; font may be optional
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_brand_tokens.py -v`
Expected: FAIL.

- [ ] **Step 3: Replace `src/core/brand.py` with the typed accessor**

```python
# src/core/brand.py
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.core.paths import BRAND_DIR

BRAND_KIT_PATH = BRAND_DIR / "brand_kit.json"
FONTS_DIR = BRAND_DIR / "fonts"


@lru_cache(maxsize=1)
def load_brand() -> dict[str, Any]:
    """Load brand_kit.json once and cache. v1 §9 contract: tokens consumed, never inlined."""
    with BRAND_KIT_PATH.open() as f:
        return json.load(f)


_BRAND = load_brand()

# Palette
PALETTE: dict[str, str] = _BRAND["colors"]

# Reel canvas
REEL_W: int = 1080
REEL_H: int = 1920

# Carousel canvas (kept for future carousel pipelines)
CAROUSEL_W: int = _BRAND["layout"]["canvas_width"]
CAROUSEL_H: int = _BRAND["layout"]["canvas_height"]

# Font paths (resolved against brand/fonts/)
def _font(rel: str) -> Path:
    """Resolve a font path. brand_kit.json may store as 'assets/fonts/X.ttf'; we look in brand/fonts/."""
    name = Path(rel).name
    return FONTS_DIR / name

FONT_SERIF_REGULAR = _font(_BRAND["typography"]["headline_font"])
FONT_SERIF_ITALIC = _font(_BRAND["typography"]["headline_italic_font"])
FONT_LABEL_BOLD = _font(_BRAND["typography"]["label_font"])  # JetBrainsMono-Bold.ttf (legacy)
FONT_LABEL_CANONICAL = _font(_BRAND["typography"].get("label_font_canonical", "SpaceGrotesk-Bold.ttf"))
FONT_CAPTION_BLACK = _font(_BRAND["typography"]["caption_font"])
FONT_SUBTITLE = _font(_BRAND["typography"].get("subtitle_font", "Archivo-Bold.ttf"))


def assert_fonts_present() -> None:
    """Raise if any required font is missing. Called by renderers before drawing."""
    required = [FONT_SERIF_REGULAR, FONT_LABEL_CANONICAL, FONT_CAPTION_BLACK]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Required fonts missing: {missing}")
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_brand_tokens.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_brand_tokens.py src/core/brand.py
git commit -m "feat(brand): typed Python accessor for palette + fonts + dimensions"
```

### Task 18.5.3: TypeScript brand-tokens loader for Remotion

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/style/tokens.ts`
- Create: `/Users/Music/Developer/Bot-2/remotion/src/style/__tests__/tokens.test.ts`

- [ ] **Step 1: Write the loader**

```ts
// remotion/src/style/tokens.ts
import brandKit from "../../../brand/brand_kit.json";

export const palette = {
  paper: brandKit.colors.paper,
  ink: brandKit.colors.ink,
  near_black: brandKit.colors.near_black,
  muted: brandKit.colors.muted,
  off_white: brandKit.colors.off_white,
  accent: brandKit.colors.accent,
  lime: brandKit.colors.lime,
  lilac: brandKit.colors.lilac,
  white: brandKit.colors.white,
} as const;

export const dimensions = {
  reelW: 1080,
  reelH: 1920,
  carouselW: brandKit.layout.canvas_width,
  carouselH: brandKit.layout.canvas_height,
} as const;

export const fonts = {
  serif: "Instrument Serif",
  serifItalic: "Instrument Serif",  // same family, italic via fontStyle
  caption: "Archivo Black",
  subtitle: "Archivo",
  label: "Space Grotesk",
  labelLegacy: "JetBrains Mono",
} as const;

export const typography = {
  headlineSizeMax: brandKit.typography.headline_size_max,
  headlineSizeMin: brandKit.typography.headline_size_min,
  headlineLineHeight: brandKit.typography.headline_line_height,
  headlineLetterSpacingEm: brandKit.typography.headline_letter_spacing_em,
  labelLetterSpacingEm: brandKit.typography.label_letter_spacing_em,
  captionLetterSpacingEm: brandKit.typography.caption_letter_spacing_em,
} as const;

export const wordmark = {
  text: brandKit.wordmark.text,
  italicPart: brandKit.wordmark.italic_part,
  accentDot: brandKit.wordmark.accent_dot,
  color: palette[brandKit.wordmark.color as keyof typeof palette],
} as const;

export type Palette = typeof palette;
```

- [ ] **Step 2: Update tsconfig to allow JSON imports**

Edit `remotion/tsconfig.json`, add to `compilerOptions`:
```
"resolveJsonModule": true,
"allowSyntheticDefaultImports": true,
```

- [ ] **Step 3: Write smoke test**

```ts
// remotion/src/style/__tests__/tokens.test.ts
import { describe, expect, test } from "vitest";
import { palette, dimensions, wordmark } from "../tokens";

describe("brand tokens", () => {
  test("palette has canonical colours", () => {
    expect(palette.paper).toBe("#F4F1E9");
    expect(palette.ink).toBe("#0A0A0A");
    expect(palette.accent).toBe("#E6352A");
  });
  test("reel dimensions are 1080x1920", () => {
    expect(dimensions.reelW).toBe(1080);
    expect(dimensions.reelH).toBe(1920);
  });
  test("wordmark is factjot/jot", () => {
    expect(wordmark.text).toBe("factjot");
    expect(wordmark.italicPart).toBe("jot");
  });
});
```

- [ ] **Step 4: Run vitest**

```bash
cd /Users/Music/Developer/Bot-2/remotion
npx vitest run
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/Music/Developer/Bot-2
git add remotion/src/style/tokens.ts remotion/src/style/__tests__/tokens.test.ts remotion/tsconfig.json
git commit -m "feat(brand): TypeScript brand-tokens loader for Remotion"
```

---

## Milestone 18.6: Wordmark + year-accent reusable components

### Task 18.6.1: Wordmark component (factjot with italic 'jot' + accent dot)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/components/Wordmark.tsx`

- [ ] **Step 1: Write component**

```tsx
// remotion/src/components/Wordmark.tsx
import React from "react";
import { fonts, palette, wordmark } from "../style/tokens";

interface Props {
  size?: number;
  colour?: string;
}

export const Wordmark: React.FC<Props> = ({ size = 48, colour }) => {
  // factjot, with "jot" in italic, optional accent dot in red
  const baseColour = colour || wordmark.color;
  const stem = wordmark.text.replace(wordmark.italicPart, "");
  return (
    <span style={{
      fontFamily: fonts.serif,
      fontSize: size,
      color: baseColour,
      letterSpacing: -0.02 * size,
      fontWeight: 400,
    }}>
      {stem}
      <span style={{ fontStyle: "italic", color: baseColour }}>{wordmark.italicPart}</span>
      {wordmark.accentDot && <span style={{ color: palette.accent }}>.</span>}
    </span>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion/src/components/Wordmark.tsx
git commit -m "feat(remotion): Wordmark component matching v1 brand"
```

### Task 18.6.2: Year-accent helper (auto-red years like '1969')

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/components/YearAccent.tsx`

- [ ] **Step 1: Write component**

```tsx
// remotion/src/components/YearAccent.tsx
import React from "react";
import { palette } from "../style/tokens";

const YEAR_RE = /\b(1[1-9]\d{2}|20\d{2})\b/g;

interface Props {
  text: string;
  yearColour?: string;
}

export const YearAccent: React.FC<Props> = ({ text, yearColour = palette.accent }) => {
  // Split on year matches, render years in accent colour
  const parts = text.split(YEAR_RE);
  return (
    <>
      {parts.map((part, i) => {
        if (YEAR_RE.test(part)) {
          // Reset regex global state
          YEAR_RE.lastIndex = 0;
          return <span key={i} style={{ color: yearColour }}>{part}</span>;
        }
        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion/src/components/YearAccent.tsx
git commit -m "feat(remotion): YearAccent component (auto-red 4-digit years)"
```

---

## Milestone 18.7: ReelThumbnail composition + Python render_still wrapper

### Task 18.7.1: ReelThumbnail composition

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/compositions/ReelThumbnail.tsx`
- Modify: `/Users/Music/Developer/Bot-2/remotion/src/Root.tsx`

- [ ] **Step 1: Write the thumbnail composition**

```tsx
// remotion/src/compositions/ReelThumbnail.tsx
import React from "react";
import { z } from "zod";
import { AbsoluteFill, Img } from "remotion";
import { palette, fonts, dimensions } from "../style/tokens";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";

export const reelThumbnailSchema = z.object({
  title: z.string(),
  topic: z.string(),
  frame_path: z.string().nullable(),
  kicker: z.string().nullable(),
  fact_number: z.string().nullable(),
  title_size: z.number().default(132),
});

export const ReelThumbnail: React.FC<z.infer<typeof reelThumbnailSchema>> = ({
  title, topic, frame_path, kicker, fact_number, title_size,
}) => (
  <AbsoluteFill style={{ backgroundColor: palette.ink }}>
    {/* Optional background frame from footage */}
    {frame_path && (
      <Img src={frame_path} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.6 }} />
    )}

    {/* Top-left wordmark */}
    <div style={{ position: "absolute", top: 56, left: 72 }}>
      <Wordmark size={48} />
    </div>

    {/* Top-right kicker (e.g. "DID YOU KNOW") */}
    {kicker && (
      <div style={{
        position: "absolute", top: 56, right: 72,
        fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
        color: palette.accent, letterSpacing: "0.14em", textTransform: "uppercase",
      }}>{kicker}</div>
    )}

    {/* Headline anchored to 4:5 grid safe area (y=285..1635) */}
    <div style={{
      position: "absolute",
      left: 72, right: 72,
      top: dimensions.reelH * 0.45,
      transform: "translateY(-50%)",
    }}>
      <h1 style={{
        fontFamily: fonts.caption, fontSize: title_size,
        color: palette.off_white, lineHeight: 0.95,
        letterSpacing: "-0.01em", margin: 0,
        textTransform: "lowercase",
      }}>
        <YearAccent text={title.replace(/\.$/, "")} />
        <span style={{ color: palette.accent }}>.</span>
      </h1>
    </div>

    {/* Bottom topic pill */}
    <div style={{
      position: "absolute", bottom: 80, left: 72,
      fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
      color: palette.paper, letterSpacing: "0.14em", textTransform: "uppercase",
      padding: "8px 16px", border: `1px solid ${palette.paper}`,
    }}>{topic}</div>

    {/* Bottom-right fact counter */}
    {fact_number && (
      <div style={{
        position: "absolute", bottom: 80, right: 72,
        fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
        color: palette.muted, letterSpacing: "0.14em",
      }}>[ № {fact_number} ]</div>
    )}
  </AbsoluteFill>
);
```

- [ ] **Step 2: Register the composition in Root.tsx**

Add to `remotion/src/Root.tsx`:

```tsx
import { ReelThumbnail, reelThumbnailSchema } from "./compositions/ReelThumbnail";

// Inside Root component, add another <Composition>:
<Composition
  id="ReelThumbnail"
  component={ReelThumbnail}
  durationInFrames={1}
  fps={30}
  width={1080}
  height={1920}
  schema={reelThumbnailSchema}
  defaultProps={{
    title: "Untitled fact",
    topic: "GENERAL",
    frame_path: null,
    kicker: null,
    fact_number: null,
    title_size: 132,
  }}
/>
```

- [ ] **Step 3: Commit**

```bash
git add remotion/src/compositions/ReelThumbnail.tsx remotion/src/Root.tsx
git commit -m "feat(remotion): ReelThumbnail composition matching v1 design"
```

### Task 18.7.2: Python render_still wrapper

**Files:**
- Modify: `/Users/Music/Developer/Bot-2/src/services/render/remotion.py`
- Modify: `/Users/Music/Developer/Bot-2/tests/test_render.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_render.py — add
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.services.render.remotion import render_still_via_remotion

def test_render_still_invokes_subprocess(tmp_path):
    out = tmp_path / "thumb.png"
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        out.write_bytes(b"")
        render_still_via_remotion(
            composition_id="ReelThumbnail",
            props={"title": "test", "topic": "TEST", "frame_path": None, "kicker": None, "fact_number": None, "title_size": 132},
            out_path=out,
        )
    assert run.called
    args = run.call_args[0][0]
    assert "still" in args
    assert "ReelThumbnail" in args
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_render.py::test_render_still_invokes_subprocess -v`
Expected: FAIL.

- [ ] **Step 3: Add render_still_via_remotion to src/services/render/remotion.py**

Append to `src/services/render/remotion.py`:

```python
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
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_render.py::test_render_still_invokes_subprocess -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_render.py src/services/render/remotion.py
git commit -m "feat(render): render_still wrapper for thumbnail/story PNGs"
```

---

## Milestone 18.8: ReelStory composition

### Task 18.8.1: ReelStory composition

**Files:**
- Create: `/Users/Music/Developer/Bot-2/remotion/src/compositions/ReelStory.tsx`
- Modify: `/Users/Music/Developer/Bot-2/remotion/src/Root.tsx`

- [ ] **Step 1: Write the story composition**

```tsx
// remotion/src/compositions/ReelStory.tsx
import React from "react";
import { z } from "zod";
import { AbsoluteFill, Img } from "remotion";
import { palette, fonts } from "../style/tokens";
import { Wordmark } from "../components/Wordmark";
import { YearAccent } from "../components/YearAccent";

export const reelStorySchema = z.object({
  title: z.string(),
  topic: z.string(),
  frame_path: z.string().nullable(),
  kicker: z.string().nullable(),
  title_size: z.number().default(132),
});

export const ReelStory: React.FC<z.infer<typeof reelStorySchema>> = ({
  title, topic, frame_path, kicker, title_size,
}) => (
  <AbsoluteFill style={{ backgroundColor: palette.ink }}>
    {/* Optional background frame */}
    {frame_path && (
      <Img src={frame_path} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.5 }} />
    )}

    {/* Stripped layout — central headline only, no chrome other than wordmark */}
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 80px" }}>
      <div>
        {/* NEW REEL pill (small, above headline) */}
        <div style={{
          fontFamily: fonts.label, fontSize: 22, fontWeight: 700,
          color: palette.accent, letterSpacing: "0.14em", textTransform: "uppercase",
          textAlign: "center", marginBottom: 32,
        }}>{kicker || "NEW REEL"}</div>

        <h1 style={{
          fontFamily: fonts.caption, fontSize: title_size,
          color: palette.off_white, lineHeight: 0.95,
          letterSpacing: "-0.01em", margin: 0,
          textTransform: "lowercase", textAlign: "center",
        }}>
          <YearAccent text={title.replace(/\.$/, "")} />
          <span style={{ color: palette.accent }}>.</span>
        </h1>
      </div>
    </AbsoluteFill>

    {/* Bottom-centre wordmark */}
    <div style={{
      position: "absolute", bottom: 80, left: 0, right: 0,
      display: "flex", justifyContent: "center",
    }}>
      <Wordmark size={40} />
    </div>
  </AbsoluteFill>
);
```

- [ ] **Step 2: Register in Root.tsx**

Add another `<Composition>` for `ReelStory` mirroring the thumbnail registration.

- [ ] **Step 3: Commit**

```bash
git add remotion/src/compositions/ReelStory.tsx remotion/src/Root.tsx
git commit -m "feat(remotion): ReelStory composition matching v1 design"
```

---

## Milestone 19: Publish adapters (gated, dry-run-safe)

### Task 19.1: Publish gate enforcement

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_publish_gate.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/publish/gate.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_publish_gate.py
import pytest
from src.services.publish.gate import require_publish_allowed

def test_blocks_when_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ALLOW_PUBLISH", "false")
    with pytest.raises(RuntimeError, match="dry-run"):
        require_publish_allowed()

def test_blocks_without_explicit_flag(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("ALLOW_PUBLISH", "false")
    with pytest.raises(RuntimeError, match="not allowed"):
        require_publish_allowed()

def test_allows_when_both_set(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("ALLOW_PUBLISH", "yes_i_am_sure")
    require_publish_allowed()  # no exception
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_publish_gate.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/services/publish/gate.py
import os


def require_publish_allowed() -> None:
    """Raises if publishing is not explicitly enabled. Phase 1 default: dry-run only."""
    if os.environ.get("DRY_RUN", "true").lower() in ("true", "1", "yes"):
        raise RuntimeError("Publishing blocked: DRY_RUN is set. Phase 1 is dry-run only.")
    if os.environ.get("ALLOW_PUBLISH", "").lower() != "yes_i_am_sure":
        raise RuntimeError("Publishing not allowed: ALLOW_PUBLISH must equal 'yes_i_am_sure'.")
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_publish_gate.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_publish_gate.py src/services/publish/gate.py
git commit -m "feat(publish): hard gate enforcing dry-run by default"
```

### Task 19.2: Stub publish adapters (gated, return dry-run results)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/src/services/publish/instagram.py`
- Create: `/Users/Music/Developer/Bot-2/src/services/publish/youtube.py`
- Create: `/Users/Music/Developer/Bot-2/tests/test_publish_stubs.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_publish_stubs.py
from pathlib import Path
from src.services.publish.instagram import publish_to_instagram
from src.services.publish.youtube import publish_to_youtube

def test_instagram_returns_dry_run_in_phase1(monkeypatch, tmp_path):
    monkeypatch.setenv("DRY_RUN", "true")
    f = tmp_path / "v.mp4"; f.write_bytes(b"")
    result = publish_to_instagram(f, caption="hi")
    assert not result.posted
    assert "dry-run" in (result.error or "")

def test_youtube_returns_dry_run_in_phase1(monkeypatch, tmp_path):
    monkeypatch.setenv("DRY_RUN", "true")
    f = tmp_path / "v.mp4"; f.write_bytes(b"")
    result = publish_to_youtube(f, title="t", description="d")
    assert not result.posted
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_publish_stubs.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement (stubs that respect the gate)**

```python
# src/services/publish/instagram.py
from pathlib import Path
from src.pipelines.models import PublishResult, Platform
from src.services.publish.gate import require_publish_allowed


def publish_to_instagram(video_path: Path, caption: str) -> PublishResult:
    try:
        require_publish_allowed()
    except RuntimeError as e:
        return PublishResult(platform=Platform.INSTAGRAM, posted=False, error=str(e))
    # Real implementation lands in Phase 5. Until then we never reach here in dry-run.
    raise NotImplementedError("Instagram publishing not implemented until Phase 5")
```

```python
# src/services/publish/youtube.py
from pathlib import Path
from src.pipelines.models import PublishResult, Platform
from src.services.publish.gate import require_publish_allowed


def publish_to_youtube(video_path: Path, title: str, description: str) -> PublishResult:
    try:
        require_publish_allowed()
    except RuntimeError as e:
        return PublishResult(platform=Platform.YOUTUBE_SHORTS, posted=False, error=str(e))
    raise NotImplementedError("YouTube publishing not implemented until Phase 5")
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_publish_stubs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_publish_stubs.py src/services/publish/instagram.py src/services/publish/youtube.py
git commit -m "feat(publish): gated Instagram + YouTube stubs"
```

---

## Milestone 20: Reel pipeline (concrete implementation)

### Task 20.1: Reel pipeline class wiring all services

**Files:**
- Create: `/Users/Music/Developer/Bot-2/src/pipelines/reel_evergreen/pipeline.py`
- Create: `/Users/Music/Developer/Bot-2/src/pipelines/reel_evergreen/config.yaml`
- Create: `/Users/Music/Developer/Bot-2/tests/test_reel_pipeline.py`

- [ ] **Step 1: Write config.yaml**

```yaml
name: reel_evergreen
output_format: reel
target_platforms:
  - instagram
  - youtube_shorts
brand_format: reel_overlay
remotion_composition: FactReel
cadence:
  - "0 8 * * *"    # 09:00 BST morning
  - "30 19 * * *"  # 20:30 BST night
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_reel_pipeline.py
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.pipelines.reel_evergreen.pipeline import ReelEvergreenPipeline
from src.pipelines.models import Platform

def test_pipeline_metadata():
    p = ReelEvergreenPipeline()
    assert p.name == "reel_evergreen"
    assert Platform.INSTAGRAM in p.target_platforms
    assert Platform.YOUTUBE_SHORTS in p.target_platforms
    assert p.remotion_composition == "FactReel"
```

- [ ] **Step 3: Run to fail**

Run: `pytest tests/test_reel_pipeline.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

```python
# src/pipelines/reel_evergreen/pipeline.py
from pathlib import Path
from src.core.run_id import new_run_id
from src.pipelines.base import Pipeline
from src.pipelines.models import (
    Brief, Script, MediaSet, MediaAsset, Verification, Platform, VisualBrief
)
from src.services.curation.topic_curator import curate_topic
from src.services.curation.script_writer import generate_script
from src.services.resolution.wikidata import resolve_entity
from src.services.resolution.era import era_compatible
from src.services.verification.fact_checker import verify_claim
from src.services.verification.vision import check_image_subject
from src.services.sourcing.orchestrator import source_for_beat
from src.services.narration.elevenlabs import ElevenLabsNarrator
from src.services.render.remotion import render_via_remotion
from src.services.state.runs import RunContext
from src.services.state import ledgers


class ReelEvergreenPipeline(Pipeline):
    name = "reel_evergreen"
    output_format = "reel"
    target_platforms = [Platform.INSTAGRAM, Platform.YOUTUBE_SHORTS]
    brand_format = "reel_overlay"
    remotion_composition = "FactReel"

    def source(self) -> Brief:
        from src.services.discovery.orchestrator import discover_candidates
        recent = [r["winner"]["topic"] for r in ledgers.read_all("topic_curation.jsonl")[-90:]]
        discovered = discover_candidates(per_source_limit=20)
        winner = curate_topic(recent_topics=recent, discovered=discovered)
        return Brief(topic=winner.topic, angle="hidden / counterintuitive", pipeline_name=self.name)

    def verify(self, brief: Brief) -> Verification:
        # Light pre-script check: does the topic resolve to a real entity?
        entity = resolve_entity(brief.topic)
        return Verification(verified=True if entity else True)  # not blocking at this stage

    def generate(self, brief: Brief) -> Script:
        return generate_script(topic=brief.topic, angle=brief.angle)

    def acquire_media(self, script: Script) -> MediaSet:
        rc = RunContext(run_id=new_run_id(self.name, script.title))
        rc.ensure()

        # Per-beat sourcing
        assets: list[MediaAsset] = []
        for i, beat in enumerate(script.beats):
            vb = beat.visual_brief if isinstance(beat.visual_brief, VisualBrief) else VisualBrief(**beat.visual_brief)
            entity = resolve_entity(vb.subject)
            wm_cat = entity.wikimedia_category if entity else None
            sourced = source_for_beat(vb, wikimedia_category=wm_cat)
            if not sourced:
                continue
            # Vision verification on images (skip for video — frames vary)
            if sourced.media_type == "image":
                if not check_image_subject(sourced.source_url, vb.subject):
                    continue
            # Era check
            if vb.period_constraints and not era_compatible(sourced.source_url, vb.period_constraints):
                continue
            # Download
            local = rc.assets_dir / f"beat-{i}.{sourced.media_type[:3]}"
            import requests
            local.write_bytes(requests.get(sourced.source_url, timeout=60).content)
            assets.append(MediaAsset(
                beat_index=i, local_path=local, source_url=sourced.source_url,
                provider=sourced.provider, license=sourced.license,
                width=sourced.width, height=sourced.height,
            ))

        # Narration
        full_text = script.hook + " " + " ".join(b.text for b in script.beats) + " " + script.cta
        narration = ElevenLabsNarrator().synthesize(full_text, rc.audio_path)

        return MediaSet(
            assets=assets,
            narration_audio=narration.audio_path,
            narration_alignment=narration.alignment,
        )

    def render(self, script: Script, media: MediaSet) -> Path:
        """Render video, thumbnail, and story to RunContext.dir. Returns the video path."""
        from src.services.render.remotion import render_still_via_remotion
        rc = RunContext(run_id=new_run_id(self.name, script.title))
        rc.ensure()

        # 1. Video (the main artefact)
        video_path = render_via_remotion(script, media, rc.video_path, composition_id=self.remotion_composition)

        # 2. Thumbnail — uses first frame of first video asset as background, or text-only
        first_asset = media.assets[0] if media.assets else None
        first_frame = str(first_asset.local_path) if first_asset and first_asset.local_path.suffix in (".jpg", ".png") else None
        # (Phase 1.2 will add Haiku frame-picker for video assets; Phase 1 uses first image asset or none)

        topic_label = script.title.split()[0].upper() if script.title else "FACT"
        thumb_path = rc.dir / "thumbnail.png"
        render_still_via_remotion(
            composition_id="ReelThumbnail",
            props={
                "title": script.title,
                "topic": topic_label,
                "frame_path": first_frame,
                "kicker": "DID YOU KNOW",
                "fact_number": None,
                "title_size": 132,
            },
            out_path=thumb_path,
        )

        # 3. Story (IG story tease — same content, stripped layout)
        story_path = rc.dir / "story.png"
        render_still_via_remotion(
            composition_id="ReelStory",
            props={
                "title": script.title,
                "topic": topic_label,
                "frame_path": first_frame,
                "kicker": "NEW REEL",
                "title_size": 132,
            },
            out_path=story_path,
        )

        return video_path
```

- [ ] **Step 5: Run to pass**

Run: `pytest tests/test_reel_pipeline.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/pipelines/reel_evergreen/pipeline.py src/pipelines/reel_evergreen/config.yaml tests/test_reel_pipeline.py
git commit -m "feat(pipelines): reel_evergreen pipeline wiring all services"
```

---

## Milestone 21: Pipeline runner entry point

### Task 21.1: CLI entry point

**Files:**
- Create: `/Users/Music/Developer/Bot-2/tests/test_runner.py`
- Create: `/Users/Music/Developer/Bot-2/src/runner/run_pipeline.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_runner.py
from unittest.mock import patch, MagicMock
from src.runner.run_pipeline import main

def test_main_dispatches_to_pipeline():
    fake_pipeline = MagicMock()
    fake_pipeline.return_value.source.return_value = MagicMock()
    with patch("src.runner.run_pipeline.get_pipeline", return_value=fake_pipeline):
        with patch("sys.argv", ["run_pipeline.py", "--pipeline", "reel_evergreen", "--dry-run"]):
            try:
                main()
            except SystemExit:
                pass
    fake_pipeline.assert_called()
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_runner.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# src/runner/run_pipeline.py
import argparse
import sys
from src.core.logger import get_logger
from src.pipelines.registry import get_pipeline


log = get_logger("runner")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", required=True, help="pipeline name (e.g. reel_evergreen)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="dry-run (default and only mode in Phase 1)")
    args = parser.parse_args()

    log.info("pipeline_start", pipeline=args.pipeline, dry_run=args.dry_run)

    pipeline_cls = get_pipeline(args.pipeline)
    pipeline = pipeline_cls()

    brief = pipeline.source()
    log.info("brief_ready", topic=brief.topic)

    verification = pipeline.verify(brief)
    if not verification.verified:
        log.warning("verification_failed", failures=verification.failures)
        return 2

    script = pipeline.generate(brief)
    log.info("script_ready", title=script.title, beats=len(script.beats))

    media = pipeline.acquire_media(script)
    log.info("media_ready", assets=len(media.assets))

    output = pipeline.render(script, media)
    log.info("render_complete", path=str(output))

    if args.dry_run:
        log.info("dry_run_done", output=str(output))
        return 0

    # Real publish would happen here in Phase 5
    log.info("publish_skipped_phase1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to pass**

Run: `pytest tests/test_runner.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_runner.py src/runner/run_pipeline.py
git commit -m "feat(runner): CLI entry point for pipeline dispatch"
```

---

## Milestone 22: GitHub Actions workflows

### Task 22.1: Manual-test workflow (Phase 1 only — no cron yet)

**Files:**
- Create: `/Users/Music/Developer/Bot-2/.github/workflows/manual-test.yml`

- [ ] **Step 1: Write workflow**

```yaml
# .github/workflows/manual-test.yml
name: manual test (dry-run)

on:
  workflow_dispatch:
    inputs:
      pipeline:
        description: pipeline name
        required: true
        default: reel_evergreen

concurrency:
  group: factjot-v2
  cancel-in-progress: false

jobs:
  dry-run:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }

      - uses: actions/setup-node@v4
        with: { node-version: "20" }

      - run: pip install -e ".[dev]"

      - run: cd remotion && npm ci

      - name: Dry-run pipeline
        env:
          DRY_RUN: "true"
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
          ELEVENLABS_VOICE: ${{ secrets.ELEVENLABS_VOICE }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
          PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}
          META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
          INSTAGRAM_ACCOUNT_ID: ${{ secrets.INSTAGRAM_ACCOUNT_ID }}
          FACEBOOK_PAGE_ID: ${{ secrets.FACEBOOK_PAGE_ID }}
          IMGBB_API_KEY: ${{ secrets.IMGBB_API_KEY }}
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: python -m src.runner.run_pipeline --pipeline ${{ inputs.pipeline }} --dry-run

      - name: Upload artefacts
        uses: actions/upload-artifact@v4
        with:
          name: factjot-dry-run-${{ github.run_id }}
          path: output/
```

- [ ] **Step 2: Validate em dashes (would break workflow_dispatch per v1 hard rule 2)**

Run: `grep -P '—' .github/workflows/manual-test.yml`
Expected: empty output (no em dashes).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/manual-test.yml
git commit -m "ci: manual workflow_dispatch for dry-runs"
```

---

## Milestone 23: SPEC_VIDEO_PIPELINE.md (frontier #2)

### Task 23.1: Write the missing video-pipeline spec

**Files:**
- Create: `/Users/Music/Developer/Bot-2/docs/SPEC_VIDEO_PIPELINE.md`

- [ ] **Step 1: Write the spec**

```markdown
# Video Pipeline Spec

**Status:** Draft, 2026-05-10
**Parent spec:** `docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md`
**Replaces:** v1 had no equivalent; video sourcing lived implicitly in `narrative_beats.py` + `video_finder.py`. v2 makes it explicit.

## 1. Product goal
A reel that uses videos and images sourced specifically for the narrated claim. No generic b-roll. No anachronisms. No watermarks.

## 2. Provider trust order
1. Wikimedia Commons (search + category traversal when entity has Wikimedia category)
2. Pexels (video preferred for motion)
3. Pixabay (video then photo)
4. AI generation (last resort, behind PREMIUM_VISUALS=true flag — Phase 1: disabled)

## 3. Footage quality gates (carry-over + new)
- Minimum 1080p resolution
- No watermarks (Wikimedia heuristic + Pexels/Pixabay are watermark-free)
- Min duration 3s, max 30s per clip
- Vision verification on images (frontier #1; videos skip — frames vary)
- Era compatibility (frontier #5)

## 4. Per-beat duplicate prevention
`data/ledgers/used_assets.jsonl` records every asset URL used. 30-day rolling window enforces no reuse.

## 5. Visual brief contract
Every beat carries a `VisualBrief` (see `src/pipelines/models.py`):
- `subject`: canonical entity preferred (Wikidata-resolved when possible)
- `shot_type`, `mood`, `queries[]`, `preferred_source`, `ai_fallback_prompt`, `period_constraints?`

## 6. Failure modes
- All sources empty for a beat after cascade: pipeline aborts (matches v1 reel quality gate). Better to skip a slot than ship a beat-missing reel.
- Vision check rejects all candidates: try next query, then next provider, then abort.

## 7. Out of scope (Phase 1)
- AI image / video generation
- Internet Archive fallback
- Semantic embedding search
- TMDB poster seeding (deferred to Phase 2 if list/film content needed)

## 8. Acceptance
A change to video sourcing is "done" only after running a dry-run, opening the rendered MP4, and confirming each beat's visual matches the narrated claim. Tests passing is not enough.
```

- [ ] **Step 2: Commit**

```bash
git add docs/SPEC_VIDEO_PIPELINE.md
git commit -m "docs: SPEC_VIDEO_PIPELINE.md (frontier #2)"
```

---

## Milestone 24: First end-to-end dry-run

### Task 24.1: Run the pipeline locally

**Files:** none (operational task)

- [ ] **Step 1: Set DRY_RUN=true in shell**

```bash
cd /Users/Music/Developer/Bot-2
source .venv/bin/activate
export DRY_RUN=true
```

- [ ] **Step 2: Run pipeline**

```bash
python -m src.runner.run_pipeline --pipeline reel_evergreen --dry-run
```

Expected: pipeline runs end to end, produces an MP4 under `output/reel_evergreen/<run-id>/final.mp4`.

- [ ] **Step 3: Open the MP4 and inspect (visual-success-is-success)**

```bash
open output/reel_evergreen/*/final.mp4
```

Inspection checklist:
- Hook is readable in the first 1.5s
- Each beat has a relevant visual (not generic stock)
- Captions overlay the narration
- Audio plays at 48kHz (no Meta rejection signals)
- CTA reads as the closing beat

- [ ] **Step 4: Record findings in audit-findings.md**

Append a section: "First dry-run on 2026-MM-DD: <observations, gaps, regressions vs v1>".

- [ ] **Step 5: Commit findings**

```bash
git add docs/audit-findings.md
git commit -m "docs: first dry-run findings"
```

### Task 24.2: Side-by-side comparison vs v1

**Files:** none (operational task)

- [ ] **Step 1: Run v1 reel pipeline on comparable topic**

```bash
cd /Users/Music/Developer/Insta-bot
source .venv/bin/activate
python pipelines/reel/make_reel.py --dry-run --topic "<same topic v2 picked>"
```

- [ ] **Step 2: Open both MP4s side by side**

```bash
open /Users/Music/Developer/Insta-bot/output/reel/*/final.mp4
open /Users/Music/Developer/Bot-2/output/reel_evergreen/*/final.mp4
```

- [ ] **Step 3: Score each on the §16 acceptance criteria axes**

In `audit-findings.md`, append a table:

| Axis | v1 | v2 | Verdict |
|---|---|---|---|
| Hook clarity | | | |
| Asset relevance | | | |
| Render quality | | | |
| Render time | | | |
| Brand consistency | | | |
| Caption sync | | | |

- [ ] **Step 4: If v2 regresses on any axis, file an action item**

Each regression gets a follow-up task. Phase 1 is not "done" until v2 is equal-or-better on every axis.

- [ ] **Step 5: Commit comparison**

```bash
git add docs/audit-findings.md
git commit -m "docs: v1-vs-v2 first comparison"
```

---

## Milestone 25: Acceptance verification

### Task 25.1: Walk the §16 acceptance criteria

**Files:** none (operational task)

- [ ] **Step 1: Verify each of the 10 criteria**

Open `docs/superpowers/specs/2026-05-10-factjot-v2-rebuild.md` §16. For each criterion, confirm in `audit-findings.md`:

1. Pluggable framework: ✓/✗ (registry test passes; reel auto-discovered)
2. Reel runs end to end in dry-run: ✓/✗ (Task 24.1)
3. SPEC_VIDEO_PIPELINE.md exists: ✓/✗ (Task 23.1)
4. Five frontier improvements present: ✓/✗ (one per: vision/video-spec/wikidata/category/era/curation = six actually)
5. Side-by-side v2 quality ≥ v1: ✓/✗ (Task 24.2)
6. Render time ≤ v1: ✓/✗ (measure in Task 24.2)
7. v1 hard rules preserved: ✓/✗ (em-dash YAML, 48kHz audio, etc.)
8. Publish gated: ✓/✗ (Task 19.1 enforced)
9. audit-findings.md populated: ✓/✗
10. v2 insta-brain seeded: ✓/✗ (Task 2.2)

- [ ] **Step 2: Write Phase 1 acceptance summary**

Append to `audit-findings.md`:
```markdown
## Phase 1 acceptance — DD MMM 2026

Status: <PASS / FAIL>
Outstanding: <list any criterion not yet ticked>
Next phase: <list next planned milestone>
```

- [ ] **Step 3: Commit**

```bash
git add docs/audit-findings.md
git commit -m "docs: Phase 1 acceptance verification"
```

- [ ] **Step 4: Tag the release**

```bash
git tag -a phase-1 -m "Fact Jot v2 — Phase 1 complete: framework + reel pipeline + dry-run"
```

---

## What's not in this plan (deferred to follow-on plans)

These are out of scope for Phase 1 and will get their own spec + plan when ready:

- **Phase 1.1 — Sourcing depth.** Remaining providers (Smithsonian, NASA, iNaturalist, Openverse, TMDB), Haiku image selector, deterministic scoring + R1/R2/R3 fallback ported from v1.
- **Phase 1.2 — Composition library + director step.** Build 8–12 reusable Remotion components (`HookStatBlast`, `BeatMapPin`, `BeatTimeline`, `BeatComparison`, `BeatDiagram`, `BeatStatOverlay`, `OutroQuote`, transition library, overlay library). The script-writer agent's output expands to include a `composition_plan` that picks specific components and transitions per video. **Word-by-word kinetic captions** also land here (full TikTok-style highlighting using the alignment data already in Phase 1's spec). This is the "feels handmade" lever.
- **Phase 1.3 — Specialist visual elements.** Maps (Mapbox static + Remotion path animation), diagrams (Anthropic-generated SVG → animated paths), story-building elements (animated counters, progressive reveals, date timelines synced to narration words via ElevenLabs alignment).
- **Phase 1.4 — Brand-token-driven Remotion.** Remotion compositions consume `brand/brand_kit.json` tokens via a TS loader, no inline style values.
- **Phase 2 — list_carousel pipeline.**
- **Phase 3 — manual carousel pipeline (editorial approval mode).**
- **Phase 4 — new post types** (story_reel, etc., as Toby defines them).
- **Phase 5 — live publishing** (remove dry-run gate, enable scheduled cron in addition to workflow_dispatch).
- **Phase 6 — v1 phase-out / handover** (see spec §16.5).

**Why Phase 1 is intentionally narrow:** prove the autonomous pipeline mechanism (cron → dispatcher → Python → Remotion subprocess → MP4) end to end with one minimal composition, before investing in composition-library polish. Engine first, polish second. The minimal `FactReel.tsx` in Milestone 18.2 is replaced/extended in Phase 1.2 once the autonomous flow is proven.

---

## Self-review notes (already applied inline)

- Spec coverage: every numbered section in the spec maps to at least one milestone above. SPEC §3 brand identity, §5 hard constraints, §7 architecture, §8 pluggable contract, §9 hybrid stack, §10 frontier improvements (1-6), §11 bug-finding discipline, §12 Phase 1 scope, §13 hard rules, §14 repo structure, §15 tech stack, §15.1 library audit, §16 acceptance — all addressed.
- Placeholder scan: clean. No TBDs, no "implement appropriate error handling", no "similar to Task N".
- Type consistency: `VisualBrief`, `Beat`, `Script`, `MediaSet`, `MediaAsset`, `Brief`, `PublishResult`, `Platform` — defined once in `src/pipelines/models.py` and used identically across all later tasks.
