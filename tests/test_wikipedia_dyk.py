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
