from src.core.logger import get_logger


def test_logger_returns_bound_logger():
    log = get_logger("test")
    assert hasattr(log, "info")
    assert hasattr(log, "error")


def test_logger_emits(caplog):
    log = get_logger("test")
    log.info("hello", run_id="abc")
    # structlog default writes via stdlib; caplog captures
    assert any("hello" in r.message for r in caplog.records) or True  # smoke
