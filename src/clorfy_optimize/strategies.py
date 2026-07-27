from __future__ import annotations

from .counter import TokenCounter


def deduplicate(
    messages: list[dict],
    *,
    threshold: float = 1.0,
    window: int | None = None,
) -> list[dict]:
    if not messages:
        return []

    seen: set[str] = set()
    result: list[dict] = []

    for i, msg in enumerate(messages):
        content = (msg.get("content") or "").strip()
        role = msg.get("role", "")

        if role == "system":
            result.append(msg)
            continue

        if threshold >= 1.0:
            fingerprint = f"{role}:{content}"
        else:
            words = content.lower().split()
            fingerprint = f"{role}:{' '.join(words[:20])}"

        scope = seen
        if window is not None:
            scope = set()
            for prev in result[max(0, len(result) - window) :]:
                pc = (prev.get("content") or "").strip()
                pr = prev.get("role", "")
                if threshold >= 1.0:
                    scope.add(f"{pr}:{pc}")
                else:
                    pw = pc.lower().split()
                    scope.add(f"{pr}:{' '.join(pw[:20])}")

        if fingerprint in scope:
            continue

        seen.add(fingerprint)
        result.append(msg)

    return result


def truncate_messages(
    messages: list[dict],
    *,
    max_tokens_per_message: int = 500,
    model: str = "gpt-4o",
    suffix: str = " [...]",
) -> list[dict]:
    if not messages or max_tokens_per_message <= 0:
        return list(messages)

    counter = TokenCounter(model)
    result: list[dict] = []

    for msg in messages:
        content = msg.get("content") or ""
        token_count = counter.count(content)

        if token_count <= max_tokens_per_message:
            result.append(msg)
            continue

        chars_budget = max_tokens_per_message * 4
        truncated_content = content[:chars_budget].rsplit(" ", 1)[0] + suffix
        result.append({**msg, "content": truncated_content})

    return result


def merge_system_messages(messages: list[dict], *, separator: str = "\n\n") -> list[dict]:
    if not messages:
        return []

    system_parts: list[str] = []
    non_system: list[dict] = []

    for msg in messages:
        if msg.get("role") == "system":
            content = (msg.get("content") or "").strip()
            if content:
                system_parts.append(content)
        else:
            non_system.append(msg)

    if not system_parts:
        return non_system

    merged_system = {"role": "system", "content": separator.join(system_parts)}
    return [merged_system] + non_system
