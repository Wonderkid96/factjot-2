import json
from src.core.paths import LEDGER_DIR


def append(filename: str, record: dict) -> None:
    """Append a single record as one JSON line to ledger file."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / filename
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_all(filename: str) -> list[dict]:
    """Read all records from a ledger file."""
    path = LEDGER_DIR / filename
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_run_record(pipeline: str, results) -> None:
    """Convenience used by Pipeline.ledger default."""
    append("runs.jsonl", {
        "pipeline": pipeline,
        "results": [r.model_dump(mode="json") for r in results],
    })
