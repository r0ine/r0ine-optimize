from __future__ import annotations

from .counter import TokenCounter


def _is_code_heavy(content: str) -> bool:
    return "```" in content


def prune_messages(
    messages: list[dict],
    *,
    budget_tokens: int,
    model: str = "gpt-4o",
    keep_last: int = 4,
    preserve_code: bool = True,
) -> list[dict]:
    if not messages:
        return []

    counter = TokenCounter(model)

    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    protected_tail = rest[-keep_last:] if keep_last else []
    prunable_head = rest[: len(rest) - len(protected_tail)]

    kept_head = [
        message
        for message in prunable_head
        if preserve_code and _is_code_heavy(message.get("content", "") or "")
    ]

    result = system + kept_head + protected_tail
    if counter.count_messages(result) <= budget_tokens:
        return result

    # Bütçe hâlâ aşılıyorsa en eski korunan mesajdan başlayarak sırayla düş.
    while len(result) > len(system) + 1 and counter.count_messages(result) > budget_tokens:
        result.pop(len(system))

    return result
