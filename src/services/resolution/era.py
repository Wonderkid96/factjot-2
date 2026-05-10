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
