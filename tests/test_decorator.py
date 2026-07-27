import pytest

from clorfy_optimize.cache import ResponseCache
from clorfy_optimize.decorator import optimize


def test_optimize_caches_repeated_calls(tmp_path):
    calls = []
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")

    @optimize(profile="chat", cache=cache)
    def fake_llm(messages: list[dict]) -> str:
        calls.append(messages)
        return "cevap"

    messages = [{"role": "user", "content": "merhaba"}]
    assert fake_llm(messages=messages) == "cevap"
    assert fake_llm(messages=messages) == "cevap"
    assert len(calls) == 1


def test_optimize_reports_token_savings(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")

    @optimize(profile="chat", cache=cache)
    def fake_llm(messages: list[dict]) -> str:
        return "cevap"

    long_history = [{"role": "user", "content": f"mesaj {i} " * 20} for i in range(30)]
    fake_llm(messages=long_history)

    report = fake_llm.optimization_report
    assert report.calls == 1
    assert report.tokens_after <= report.tokens_before


def test_optimize_requires_messages_argument(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")

    @optimize(profile="chat", cache=cache)
    def fake_llm(prompt: str) -> str:
        return prompt

    with pytest.raises(TypeError):
        fake_llm(prompt="merhaba")


def test_optimize_unknown_profile_raises(tmp_path):
    with pytest.raises(ValueError):
        optimize(profile="bilinmeyen")
