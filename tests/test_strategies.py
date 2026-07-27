from clorfy_optimize.strategies import deduplicate, merge_system_messages, truncate_messages


def _msg(role, content):
    return {"role": role, "content": content}


class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        msgs = [_msg("user", "merhaba"), _msg("user", "merhaba"), _msg("user", "naber")]
        result = deduplicate(msgs)
        assert len(result) == 2
        assert result[0]["content"] == "merhaba"
        assert result[1]["content"] == "naber"

    def test_keeps_system_messages(self):
        msgs = [_msg("system", "talimat"), _msg("system", "talimat"), _msg("user", "test")]
        result = deduplicate(msgs)
        assert len(result) == 3

    def test_windowed_dedup(self):
        msgs = [_msg("user", "a"), _msg("user", "b"), _msg("user", "c"), _msg("user", "a")]
        result = deduplicate(msgs, window=2)
        assert len(result) == 4  # "a" window=2'nin disinda, tekrar olarak sayilmaz

    def test_empty_input(self):
        assert deduplicate([]) == []


class TestTruncate:
    def test_short_messages_unchanged(self):
        msgs = [_msg("user", "kisa mesaj")]
        result = truncate_messages(msgs, max_tokens_per_message=1000)
        assert result[0]["content"] == "kisa mesaj"

    def test_long_messages_truncated(self):
        long_content = "kelime " * 500
        msgs = [_msg("user", long_content)]
        result = truncate_messages(msgs, max_tokens_per_message=50)
        assert len(result[0]["content"]) < len(long_content)
        assert result[0]["content"].endswith("[...]")

    def test_empty_input(self):
        assert truncate_messages([]) == []


class TestMergeSystem:
    def test_merges_multiple_system(self):
        msgs = [
            _msg("system", "birinci talimat"),
            _msg("system", "ikinci talimat"),
            _msg("user", "soru"),
        ]
        result = merge_system_messages(msgs)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "birinci" in result[0]["content"]
        assert "ikinci" in result[0]["content"]

    def test_no_system_messages(self):
        msgs = [_msg("user", "soru")]
        result = merge_system_messages(msgs)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_empty_input(self):
        assert merge_system_messages([]) == []
