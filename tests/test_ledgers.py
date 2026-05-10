import json
from src.services.state import ledgers


def test_append_creates_file_and_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(ledgers, "LEDGER_DIR", tmp_path)
    ledgers.append("posted.jsonl", {"id": "abc", "ok": True})
    contents = (tmp_path / "posted.jsonl").read_text().strip().splitlines()
    assert json.loads(contents[0]) == {"id": "abc", "ok": True}


def test_append_is_appendonly(tmp_path, monkeypatch):
    monkeypatch.setattr(ledgers, "LEDGER_DIR", tmp_path)
    ledgers.append("x.jsonl", {"a": 1})
    ledgers.append("x.jsonl", {"a": 2})
    lines = (tmp_path / "x.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
