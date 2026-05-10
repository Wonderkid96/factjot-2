from src.pipelines.registry import discover_pipelines, get_pipeline


def test_discover_returns_dict():
    pipelines = discover_pipelines()
    assert isinstance(pipelines, dict)


def test_get_unknown_pipeline_raises():
    import pytest
    with pytest.raises(KeyError):
        get_pipeline("does_not_exist")
