from types import SimpleNamespace


def test_text_verbosity_mapping(monkeypatch):
    """Ensure text_verbosity values map to API payload correctly."""
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    from src.utils import responses_api

    captured = {}

    def fake_create(**kwargs):
        nonlocal captured
        captured = kwargs
        return SimpleNamespace(output=[], usage=SimpleNamespace(
            prompt_tokens=0, completion_tokens=0, thinking_tokens=0, total_tokens=0
        ))

    monkeypatch.setattr(responses_api.client.responses, "create", fake_create)

    responses_api.create_response("hi", text_verbosity="high")
    assert captured["text"] == {"verbosity": "high"}
