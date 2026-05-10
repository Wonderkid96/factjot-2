from unittest.mock import patch, MagicMock
from src.runner.run_pipeline import main


def test_main_dispatches_to_pipeline():
    fake_pipeline_cls = MagicMock()
    fake_pipeline = MagicMock()
    fake_pipeline_cls.return_value = fake_pipeline
    fake_pipeline.verify.return_value = MagicMock(verified=True, failures=[])
    fake_script = MagicMock()
    fake_script.title = "x"
    fake_script.beats = []
    fake_pipeline.generate.return_value = fake_script
    fake_pipeline.acquire_media.return_value = MagicMock(assets=[])
    fake_pipeline.render.return_value = "/tmp/x.mp4"
    with patch("src.runner.run_pipeline.get_pipeline", return_value=fake_pipeline_cls):
        with patch("sys.argv", ["run_pipeline.py", "--pipeline", "reel_evergreen", "--dry-run"]):
            rc = main()
    assert rc == 0
    fake_pipeline_cls.assert_called_once()
    fake_pipeline.source.assert_called_once()
    fake_pipeline.render.assert_called_once()
