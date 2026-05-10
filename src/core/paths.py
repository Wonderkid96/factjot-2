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
