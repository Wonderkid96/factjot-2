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
