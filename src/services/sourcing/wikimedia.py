from dataclasses import dataclass
import mwclient


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")  # PDFs, SVGs, audio etc. excluded — they look like image hits but break the renderer


@dataclass
class WikimediaCandidate:
    title: str
    source_url: str
    width: int
    height: int
    license: str = "PD/CC"
    provider: str = "wikimedia"


_SITE_CACHE: mwclient.Site | None = None


def _site() -> mwclient.Site:
    global _SITE_CACHE
    if _SITE_CACHE is None:
        _SITE_CACHE = mwclient.Site("commons.wikimedia.org")
    return _SITE_CACHE


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


def _is_image_title(title: str) -> bool:
    return title.lower().endswith(IMAGE_EXTS)


def search_commons(query: str, limit: int = 25) -> list[WikimediaCandidate]:
    """R1/R2: full-text search Commons. Lower precision, broader recall.

    Filtered to actual image extensions — Commons search returns PDFs, SVGs,
    audio, and even other multimedia in the File namespace. Picking a PDF as
    a beat 'image' broke the renderer.
    """
    site = _site()
    out: list[WikimediaCandidate] = []
    for hit in site.search(query, namespace=6):  # 6 = File namespace
        if len(out) >= limit:
            break
        title = hit["title"].removeprefix("File:")
        if not _is_image_title(title):
            continue
        page = site.images[title]
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
        title = getattr(member, "page_title", "")
        if not _is_image_title(title):
            continue
        c = _to_candidate(member)
        if c:
            out.append(c)
    return out
