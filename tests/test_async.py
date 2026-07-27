import asyncio

import pytest

from clorfy_optimize.async_support import optimize_async
from clorfy_optimize.cache import ResponseCache


def test_async_decorator_caches(tmp_path):
    calls = []
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")

    @optimize_async(profile="chat", cache=cache)
    async def fake_llm(messages: list[dict]) -> str:
        calls.append(1)
        return "async cevap"

    messages = [{"role": "user", "content": "merhaba"}]
    assert asyncio.run(fake_llm(messages=messages)) == "async cevap"
    assert asyncio.run(fake_llm(messages=messages)) == "async cevap"
    assert len(calls) == 1


def test_async_decorator_reports_savings(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")

    @optimize_async(profile="code", cache=cache)
    async def fake_llm(messages: list[dict]) -> str:
        return "cevap"

    history = [{"role": "user", "content": f"mesaj {i} " * 20} for i in range(20)]
    asyncio.run(fake_llm(messages=history))
    report = fake_llm.optimization_report
    assert report.tokens_after <= report.tokens_before


def test_async_rejects_sync_function():
    with pytest.raises(TypeError, match="async"):

        @optimize_async(profile="chat")
        def not_async(messages: list[dict]) -> str:
            return "sync"
