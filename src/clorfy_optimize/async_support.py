from __future__ import annotations

import functools
import inspect

from .cache import ResponseCache
from .counter import TokenCounter
from .decorator import OptimizationReport
from .profiles import get_profile
from .pruner import prune_messages


def optimize_async(
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
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"{func.__name__} async fonksiyon degil; sync icin optimize() kullan.")

        signature = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            if messages_arg not in bound.arguments:
                raise TypeError(
                    f"{func.__name__} fonksiyonunda '{messages_arg}' argumani bulunamadi; "
                    f"messages_arg parametresini dogru isimle gec."
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

            result = await func(*bound.args, **bound.kwargs)
            if isinstance(result, str):
                active_cache.set(pruned, model, result)
            return result

        wrapper.optimization_report = active_report
        wrapper.optimization_cache = active_cache
        return wrapper

    return decorator
