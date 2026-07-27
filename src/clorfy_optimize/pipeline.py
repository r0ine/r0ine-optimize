from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .counter import TokenCounter
from .profiles import Profile, get_profile
from .pruner import prune_messages
from .strategies import deduplicate, merge_system_messages, truncate_messages


@dataclass
class PipelineResult:
    messages: list[dict]
    tokens_before: int
    tokens_after: int
    steps_applied: list[str]

    @property
    def tokens_saved(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)

    @property
    def savings_percent(self) -> float:
        if self.tokens_before == 0:
            return 0.0
        return self.tokens_saved / self.tokens_before * 100


@dataclass
class _Step:
    name: str
    fn: Callable[[list[dict]], list[dict]]


class Pipeline:
    def __init__(self, profile: str | Profile | None = None, *, model: str = "gpt-4o") -> None:
        self._steps: list[_Step] = []
        self._model = model

        if profile is not None:
            p = get_profile(profile) if isinstance(profile, str) else profile
            self.merge_system().deduplicate().prune(
                keep_last=p.keep_last,
                preserve_code=p.preserve_code,
                budget_tokens=p.default_budget_tokens,
            )

    def merge_system(self, *, separator: str = "\n\n") -> Pipeline:
        self._steps.append(_Step(
            "merge_system",
            lambda msgs, sep=separator: merge_system_messages(msgs, separator=sep),
        ))
        return self

    def deduplicate(self, *, threshold: float = 1.0, window: int | None = None) -> Pipeline:
        self._steps.append(_Step(
            "deduplicate",
            lambda msgs, t=threshold, w=window: deduplicate(msgs, threshold=t, window=w),
        ))
        return self

    def prune(
        self,
        *,
        keep_last: int = 4,
        preserve_code: bool = True,
        budget_tokens: int = 8_000,
    ) -> Pipeline:
        self._steps.append(_Step(
            "prune",
            lambda msgs, kl=keep_last, pc=preserve_code, bt=budget_tokens: prune_messages(
                msgs, budget_tokens=bt, model=self._model, keep_last=kl, preserve_code=pc
            ),
        ))
        return self

    def truncate(self, *, max_tokens_per_message: int = 500, suffix: str = " [...]") -> Pipeline:
        self._steps.append(_Step(
            "truncate",
            lambda msgs, mt=max_tokens_per_message, s=suffix: truncate_messages(
                msgs, max_tokens_per_message=mt, model=self._model, suffix=s
            ),
        ))
        return self

    def add_step(self, name: str, fn: Callable[[list[dict]], list[dict]]) -> Pipeline:
        self._steps.append(_Step(name, fn))
        return self

    def run(self, messages: list[dict]) -> PipelineResult:
        counter = TokenCounter(self._model)
        tokens_before = counter.count_messages(messages)

        current = list(messages)
        applied: list[str] = []

        for step in self._steps:
            before_len = len(current)
            current = step.fn(current)
            if len(current) != before_len:
                applied.append(step.name)

        tokens_after = counter.count_messages(current)

        return PipelineResult(
            messages=current,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            steps_applied=applied,
        )
