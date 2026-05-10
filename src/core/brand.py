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
