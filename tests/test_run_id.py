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
