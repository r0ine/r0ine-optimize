from r0ine_optimize.counter import TokenCounter
from r0ine_optimize.pruner import prune_messages


def _turn(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def test_prune_keeps_system_and_recent_turns():
    messages = [
        _turn("system", "sen yardımcı bir asistansın"),
        *[_turn("user", f"eski mesaj {i}") for i in range(10)],
        _turn("user", "son mesaj"),
    ]
    pruned = prune_messages(messages, budget_tokens=10_000, keep_last=2)
    assert pruned[0]["role"] == "system"
    assert pruned[-1]["content"] == "son mesaj"


def test_prune_shrinks_message_count_under_tight_budget():
    messages = [_turn("user", "kelime " * 50) for _ in range(20)]
    pruned = prune_messages(messages, budget_tokens=80, keep_last=2)
    assert len(pruned) < len(messages)


def test_prune_never_exceeds_original_token_count():
    messages = [_turn("user", f"mesaj {i} dolgu metni") for i in range(15)]
    counter = TokenCounter()
    before = counter.count_messages(messages)
    pruned = prune_messages(messages, budget_tokens=before // 2, keep_last=3)
    assert counter.count_messages(pruned) <= before


def test_prune_preserves_code_blocks_when_enabled():
    messages = [
        _turn("user", "```python\nprint(1)\n```"),
        *[_turn("user", f"dolgu {i}") for i in range(5)],
        _turn("user", "son"),
    ]
    pruned = prune_messages(messages, budget_tokens=10_000, keep_last=1, preserve_code=True)
    assert any("```" in m["content"] for m in pruned)


def test_prune_drops_code_blocks_when_disabled():
    messages = [
        _turn("user", "```python\nprint(1)\n```"),
        *[_turn("user", f"dolgu {i}") for i in range(5)],
        _turn("user", "son"),
    ]
    pruned = prune_messages(messages, budget_tokens=10_000, keep_last=1, preserve_code=False)
    assert not any("```" in m["content"] for m in pruned[:-1])


def test_prune_empty_input_returns_empty():
    assert prune_messages([], budget_tokens=1000) == []
