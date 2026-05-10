import pytest
from src.services.publish.gate import require_publish_allowed


def test_blocks_when_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ALLOW_PUBLISH", "false")
    with pytest.raises(RuntimeError, match="dry-run"):
        require_publish_allowed()


def test_blocks_without_explicit_flag(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("ALLOW_PUBLISH", "false")
    with pytest.raises(RuntimeError, match="not allowed"):
        require_publish_allowed()


def test_allows_when_both_set(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("ALLOW_PUBLISH", "yes_i_am_sure")
    require_publish_allowed()  # no exception
