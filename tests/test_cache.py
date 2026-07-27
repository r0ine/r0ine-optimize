import time

from clorfy_optimize.cache import ResponseCache


def test_cache_miss_then_hit(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3", ttl_seconds=60)
    messages = [{"role": "user", "content": "merhaba"}]

    assert cache.get(messages, "gpt-4o") is None
    cache.set(messages, "gpt-4o", "selam")
    assert cache.get(messages, "gpt-4o") == "selam"

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_cache_entry_expires(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3", ttl_seconds=0)
    messages = [{"role": "user", "content": "merhaba"}]
    cache.set(messages, "gpt-4o", "selam")
    time.sleep(0.01)
    assert cache.get(messages, "gpt-4o") is None


def test_cache_keys_differ_by_model(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.sqlite3")
    messages = [{"role": "user", "content": "merhaba"}]
    cache.set(messages, "gpt-4o", "selam-4o")
    assert cache.get(messages, "gpt-4o-mini") is None
