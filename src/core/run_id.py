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
