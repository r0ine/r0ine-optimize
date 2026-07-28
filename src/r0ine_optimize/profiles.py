from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str
    keep_last: int
    preserve_code: bool
    cache_ttl_seconds: int
    default_budget_tokens: int


CODE = Profile(
    name="code",
    keep_last=6,
    preserve_code=True,
    cache_ttl_seconds=6 * 3600,
    default_budget_tokens=12_000,
)

CHAT = Profile(
    name="chat",
    keep_last=8,
    preserve_code=False,
    cache_ttl_seconds=15 * 60,
    default_budget_tokens=6_000,
)

PLAN = Profile(
    name="plan",
    keep_last=3,
    preserve_code=True,
    cache_ttl_seconds=24 * 3600,
    default_budget_tokens=20_000,
)

_REGISTRY = {"code": CODE, "chat": CHAT, "plan": PLAN}


def get_profile(name: str) -> Profile:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Bilinmeyen profil: {name!r}. Kullanılabilir: {available}") from exc
