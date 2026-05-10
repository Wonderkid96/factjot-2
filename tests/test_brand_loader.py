from src.core.brand import load_brand


def test_brand_loads_colors():
    brand = load_brand()
    assert "colors" in brand
    assert isinstance(brand["colors"], dict)


def test_brand_loads_typography():
    brand = load_brand()
    assert "typography" in brand


def test_brand_loads_handle():
    brand = load_brand()
    assert brand.get("handle"), "brand_kit.json should declare a handle"
