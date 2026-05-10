from src.core.brand import (
    PALETTE, REEL_W, REEL_H,
    FONT_SERIF_REGULAR, FONT_CAPTION_BLACK, FONT_LABEL_CANONICAL,
    assert_fonts_present,
)


def test_palette_has_canonical_colours():
    assert PALETTE["paper"] == "#F4F1E9"
    assert PALETTE["ink"] == "#0A0A0A"
    assert PALETTE["accent"] == "#E6352A"
    assert PALETTE["lime"] == "#C8DB45"
    assert PALETTE["lilac"] == "#C4A9D0"


def test_reel_dimensions():
    assert REEL_W == 1080
    assert REEL_H == 1920


def test_font_paths_exist_after_copy():
    assert FONT_SERIF_REGULAR.exists()
    assert FONT_CAPTION_BLACK.exists()
    assert FONT_LABEL_CANONICAL.exists()


def test_assert_fonts_present_passes():
    assert_fonts_present()  # should not raise
