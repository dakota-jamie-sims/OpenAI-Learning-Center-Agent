import pytest

from src.services.openai_responses_client import ResponsesClient
from src.config_production import TIMEOUTS


def test_create_response_honors_timeout(monkeypatch):
    """`create_response` should forward timeout to `_with_retry`.

    If the underlying retry wrapper raises ``TimeoutError`` when the
    configured timeout is exceeded, the error should propagate to the caller.
    """

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    client = ResponsesClient()

    def fake_with_retry(self, func, timeout=None, **kwargs):
        # ensure the computed timeout is forwarded
        assert timeout == TIMEOUTS["llm_call"]
        raise TimeoutError("simulated long-running call")

    monkeypatch.setattr(ResponsesClient, "_with_retry", fake_with_retry)

    with pytest.raises(TimeoutError):
        client.create_response(
            model="gpt-5",
            input_text="hello",
            timeout=TIMEOUTS["llm_call"],
        )

