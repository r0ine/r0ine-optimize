# r0ine-optimize

[![CI](https://github.com/r0ine/r0ine-optimize/actions/workflows/ci.yml/badge.svg)](https://github.com/r0ine/r0ine-optimize/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A lightweight library + CLI that reduces the number of tokens you send to LLMs. Part of the **r0ine** AI tooling family.

## What it does

Three core mechanisms:

- **Response caching** — identical message list + same model returns from disk (SQLite, TTL-based) without hitting the model at all.
- **History pruning** — fits conversation history into a token budget: keeps system messages and the last N turns, drops oldest first.
- **Profile engine** — different use cases need different token profiles; `code` / `chat` / `plan` profiles carry ready-made defaults.

Plus three additional capabilities:

- **Pipeline** — composable middleware chain for optimization steps (dedup → system-merge → prune → truncate).
- **Strategy modules** — message deduplication, per-message truncation, multi-system-message merging.
- **Async support** — `optimize_async` decorator for async LLM calls.

## Installation

```bash
pip install r0ine-optimize
```

For real tokenization (falls back to ~4 chars/token if `tiktoken` isn't installed):

```bash
pip install "r0ine-optimize[tiktoken]"
```

## One-line integration

Add the decorator on top of your existing LLM call function:

```python
from r0ine_optimize import optimize

@optimize(profile="chat")
def call_llm(messages: list[dict]) -> str:
    return my_llm_client.chat(messages)
```

The `messages` argument gets pruned according to the profile before your function runs. If the same request was made before, it returns from cache — you didn't touch the function internals at all.

Async version:

```python
from r0ine_optimize import optimize_async

@optimize_async(profile="code")
async def call_llm(messages: list[dict]) -> str:
    return await my_async_client.chat(messages)
```

Check the savings:

```python
call_llm(messages=history)
print(call_llm.optimization_report.as_dict())
# {'calls': 1, 'cache_hits': 0, 'tokens_before': 812, 'tokens_after': 340, 'tokens_saved': 472}
```

## Pipeline (composable optimization)

Profile-based ready chain:

```python
from r0ine_optimize import Pipeline

pipe = Pipeline("chat")  # merge_system -> deduplicate -> prune
result = pipe.run(messages)

print(result.tokens_before, "->", result.tokens_after)
print(f"Savings: {result.savings_percent:.1f}%")
print(f"Steps: {result.steps_applied}")
```

Fully custom chain:

```python
pipe = (
    Pipeline()
    .merge_system()              # merge multiple system messages
    .deduplicate(threshold=1.0)  # drop duplicate messages
    .truncate(max_tokens_per_message=500)  # trim long messages
    .prune(keep_last=5, preserve_code=True, budget_tokens=4_000)
)
result = pipe.run(messages)
```

Add your own optimization step:

```python
pipe = Pipeline().add_step("redact", lambda msgs: [
    {**m, "content": m["content"].replace("API_KEY", "***")} for m in msgs
]).prune(keep_last=8, budget_tokens=6_000)
```

## Strategies

Use independently:

```python
from r0ine_optimize import deduplicate, merge_system_messages, truncate_messages

clean = deduplicate(messages, threshold=1.0)
merged = merge_system_messages(messages)
truncated = truncate_messages(messages, max_tokens_per_message=300)
```

## Profiles

| Profile | keep_last | preserve_code | cache_ttl | default budget |
|---|---|---|---|---|
| `code` | 6 | yes | 6 hours | 12,000 tokens |
| `chat` | 8 | no | 15 minutes | 6,000 tokens |
| `plan` | 3 | yes | 24 hours | 20,000 tokens |

Custom profiles:

```python
from r0ine_optimize import Profile

my_profile = Profile(
    name="custom",
    keep_last=10,
    preserve_code=True,
    cache_ttl_seconds=3600,
    default_budget_tokens=8_000,
)
pipe = Pipeline(my_profile)
```

## CLI

```bash
r0ine-optimize analyze conversation.json --profile chat
r0ine-optimize analyze conversation.json --profile code --pipeline
r0ine-optimize profiles
r0ine-optimize cache stats
r0ine-optimize cache purge
r0ine-optimize cache clear
```

## Architecture

```
src/r0ine_optimize/
├── counter.py           # TokenCounter (tiktoken or fallback)
├── cache.py             # ResponseCache (SQLite, TTL, stats)
├── pruner.py            # message pruning (budget + keep_last)
├── profiles.py          # CODE / CHAT / PLAN profiles
├── strategies.py        # dedup, truncate, merge_system
├── pipeline.py          # Pipeline (composable chain)
├── decorator.py         # @optimize (sync)
├── async_support.py     # @optimize_async
└── cli.py               # Click CLI
```

## Limitations (v0.1)

- The `optimize()` decorator assumes the wrapped function returns plain text (`str`) — disable caching for streaming or structured (tool-call) responses.
- Pruning is a deterministic rule engine; it doesn't call a summarization LLM (by design — a token-saving tool shouldn't spend tokens itself).
- Without `tiktoken`, token counting is approximate (chars/4).

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src/r0ine_optimize --ignore-missing-imports
```

## r0ine family

| Project | Purpose |
|---|---|
| **clorfy-ai** | Prompt engineering and optimization |
| **r0ine-optimize** | Token savings (pruning, caching, pipelines) |
| *clorfy-memory* | Long-term LLM memory management (planned) |
| *clorfy-router* | Multi-model routing (planned) |
| *clorfy-guard* | LLM output safety filters (planned) |

## License

MIT

---

## Turkce

LLM'lere gonderdigin token miktarini azaltan kutuphane + CLI. **r0ine** AI arac ailesinin token tasarrufu tarafi.

Uc temel mekanizma: yanit onbellekleme (SQLite + TTL), gecmis budama (butce + son N tur), senaryo profilleri (code/chat/plan). Ustune Pipeline ile composable optimizasyon zincirleri, strateji modulleri (dedup, truncate, merge) ve async dekorator destegi.

Kurulum: `pip install r0ine-optimize`

Tek satirda entegrasyon:

```python
from r0ine_optimize import optimize

@optimize(profile="chat")
def call_llm(messages: list[dict]) -> str:
    return my_llm_client.chat(messages)
```

Pipeline kullanimi:

```python
from r0ine_optimize import Pipeline

pipe = Pipeline("chat")
result = pipe.run(messages)
print(f"Tasarruf: %{result.savings_percent:.1f}")
```

Detayli dokumantasyon icin yukariyi okuyun.
