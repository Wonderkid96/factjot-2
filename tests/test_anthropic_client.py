from src.core.anthropic_client import AnthropicClient


def test_client_constructs():
    c = AnthropicClient()
    assert c.model_default


def test_default_model_is_sonnet():
    c = AnthropicClient()
    assert "sonnet" in c.model_default
