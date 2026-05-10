from unittest.mock import MagicMock, patch
from src.core.anthropic_client import AnthropicClient, extract_json


def test_client_constructs():
    c = AnthropicClient()
    assert c.model_default


def test_default_model_is_sonnet():
    c = AnthropicClient()
    assert "sonnet" in c.model_default


def test_extract_json_handles_markdown_fence():
    assert extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_json_handles_trailing_prose():
    """Opus often returns valid JSON then explanatory text. Must keep just the JSON."""
    out = extract_json('{"winner_index": 0}\nThis was selected because...')
    assert out == '{"winner_index": 0}'


def test_local_agent_mode_shells_to_claude_cli(monkeypatch):
    """USE_LOCAL_AGENT=true routes the call to `claude -p` instead of the API."""
    monkeypatch.setenv("USE_LOCAL_AGENT", "true")
    fake_result = MagicMock(returncode=0, stdout="local agent response\n", stderr="")
    with patch("src.core.anthropic_client.subprocess.run", return_value=fake_result) as run:
        out = AnthropicClient().text(system="sys", user="usr")
    assert out == "local agent response"
    assert run.called
    cmd = run.call_args.args[0]
    assert cmd[0] == "claude"
    assert "-p" in cmd
    # System + user joined into the final positional arg
    assert "sys" in cmd[-1] and "usr" in cmd[-1]


def test_api_mode_does_not_shell_out(monkeypatch):
    """Default (no USE_LOCAL_AGENT): API path, never invokes claude CLI."""
    monkeypatch.delenv("USE_LOCAL_AGENT", raising=False)
    fake_msg = MagicMock()
    fake_msg.content = [MagicMock(text="api response")]
    with patch("src.core.anthropic_client.subprocess.run") as run, \
         patch.object(AnthropicClient, "__init__", lambda self, *a, **k: None):
        c = AnthropicClient()
        c.client = MagicMock()
        c.client.messages.create.return_value = fake_msg
        c.model_default = "claude-sonnet-4-6"
        out = c.text(system="sys", user="usr")
    assert out == "api response"
    assert not run.called
