from src.core.paths import REPO_ROOT, OUTPUT_DIR, LEDGER_DIR, REMOTION_DIR


def test_repo_root_exists():
    assert REPO_ROOT.exists()
    assert (REPO_ROOT / "pyproject.toml").exists()


def test_output_dir_under_repo():
    assert OUTPUT_DIR.is_relative_to(REPO_ROOT)


def test_ledger_dir_under_repo():
    assert LEDGER_DIR.is_relative_to(REPO_ROOT)


def test_remotion_dir_under_repo():
    assert REMOTION_DIR.is_relative_to(REPO_ROOT)
