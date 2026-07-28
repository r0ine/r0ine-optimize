from __future__ import annotations

_FALLBACK_CHARS_PER_TOKEN = 4
_MESSAGE_OVERHEAD_TOKENS = 4  # OpenAI chat format için rol/ayraç payı, tiktoken yokken de geçerli

try:
    import tiktoken
except ImportError:  # tiktoken opsiyonel bağımlılık, kurulu değilse yaklaşık sayıma düşülür
    tiktoken = None


class TokenCounter:
    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self._encoding = self._load_encoding(model)

    def _load_encoding(self, model: str):
        if tiktoken is None:
            return None
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return max(1, len(text) // _FALLBACK_CHARS_PER_TOKEN)

    def count_messages(self, messages: list[dict]) -> int:
        total = 0
        for message in messages:
            total += self.count(message.get("content", "") or "")
            total += _MESSAGE_OVERHEAD_TOKENS
        return total
