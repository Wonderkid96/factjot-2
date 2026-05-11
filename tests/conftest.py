"""Pytest session-wide fixtures.

The runner module (`src.runner.run_pipeline`) calls `dotenv.load_dotenv()` at
import time so the FACTJOT_FROZEN lock actually takes effect for `uv run`
invocations. But pytest's `test_runner.py` imports the runner during
collection, which means `.env`'s `FACTJOT_FROZEN=1` leaks into the test
process — and any test that touches the script_writer or ElevenLabsNarrator
(even with mocks) hits FrozenModeViolation.

Clear it once at session start so the test environment is deterministic
regardless of what the operator has set in `.env` for live-run safety.
"""
import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _clear_frozen_lock() -> None:
    os.environ.pop("FACTJOT_FROZEN", None)
