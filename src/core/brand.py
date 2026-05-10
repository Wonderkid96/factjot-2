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
