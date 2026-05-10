from unittest.mock import patch, MagicMock
from src.services.sourcing.wikimedia import search_commons, traverse_category


def test_search_returns_candidates():
    fake_image = MagicMock()
    fake_image.imageinfo = {"url": "https://example/x.jpg", "width": 2000, "height": 3000}
    fake_image.page_title = "File:x.jpg"
    with patch("src.services.sourcing.wikimedia._site") as site:
        site.return_value.search.return_value = [{"title": "File:x.jpg"}]
        site.return_value.images = {"x.jpg": fake_image}
        results = search_commons("apollo 11")
    assert len(results) >= 1
    assert results[0].source_url.startswith("https://")


def test_traverse_category_returns_files():
    fake_image = MagicMock()
    fake_image.imageinfo = {"url": "https://example/y.jpg", "width": 1500, "height": 2500}
    fake_image.page_title = "File:y.jpg"
    fake_cat = MagicMock()
    fake_cat.members.return_value = [fake_image]
    with patch("src.services.sourcing.wikimedia._site") as site:
        site.return_value.categories = {"Johnstown Flood": fake_cat}
        results = traverse_category("Category:Johnstown Flood")
    assert len(results) >= 1
