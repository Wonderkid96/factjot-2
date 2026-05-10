from src.services.resolution.era import era_compatible


def test_compatible_when_no_constraints():
    assert era_compatible(metadata="some random title", constraints=None)


def test_rejects_modern_iphone_for_victorian():
    assert not era_compatible(
        metadata="iPhone 14 Pro photo of victorian-style building, 2024",
        constraints={"min_year": 1850, "max_year": 1900}
    )


def test_passes_period_match():
    assert era_compatible(
        metadata="Daguerreotype, 1860, Boston",
        constraints={"min_year": 1850, "max_year": 1900}
    )
