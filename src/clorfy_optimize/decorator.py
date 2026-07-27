from __future__ import annotations

import functools
import inspect

from .cache import ResponseCache
from .counter import TokenCounter
from .profiles import get_profile
from .pruner import prune_messages


class OptimizationReport:
    def __init__(self) -> None:
        self.calls = 0
        self.cache_hits = 0
        self.tokens_before = 0
        self.tokens_after = 0

    @property
    def tokens_saved(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)

    def as_dict(self) -> dict:
        return {
            "calls": self.calls,
            "cache_hits": self.cache_hits,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "tokens_saved": self.tokens_saved,
        }


def optimize(
    profile: str = "chat",
    *,
    model: str = "gpt-4o",
    messages_arg: str = "messages",
    cache: ResponseCache | None = None,
    report: OptimizationReport | None = None,
):
    profile_config = get_profile(profile)
    counter = TokenCounter(model)
    active_cache = cache if cache is not None else ResponseCache(ttl_seconds=profile_config.cache_ttl_seconds)
    active_report = report if report is not None else OptimizationReport()

    def decorator(func):
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            if messages_arg not in bound.arguments:
                raise TypeError(
                    f"{func.__name__} fonksiyonunda '{messages_arg}' argümanı bulunamadı; "
                    f"messages_arg parametresini doğru isimle geç."
                )

            original_messages = bound.arguments[messages_arg]
            active_report.calls += 1
            active_report.tokens_before += counter.count_messages(original_messages)

            pruned = prune_messages(
                original_messages,
                budget_tokens=profile_config.default_budget_tokens,
                model=model,
                keep_last=profile_config.keep_last,
                preserve_code=profile_config.preserve_code,
            )
            active_report.tokens_after += counter.count_messages(pruned)
            bound.arguments[messages_arg] = pruned

            cached = active_cache.get(pruned, model)
            if cached is not None:
                active_report.cache_hits += 1
                return cached

            result = func(*bound.args, **bound.kwargs)
            active_cache.set(pruned, model, result)
            return result

        wrapper.optimization_report = active_report
        wrapper.optimization_cache = active_cache
        return wrapper

    return decorator
