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
