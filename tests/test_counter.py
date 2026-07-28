from r0ine_optimize.counter import TokenCounter


def test_count_empty_string_is_zero():
    counter = TokenCounter()
    assert counter.count("") == 0


def test_count_grows_with_text_length():
    counter = TokenCounter()
    short = counter.count("merhaba")
    long_ = counter.count("merhaba " * 50)
    assert long_ > short


def test_count_messages_includes_overhead():
    counter = TokenCounter()
    messages = [{"role": "user", "content": "merhaba"}]
    assert counter.count_messages(messages) > counter.count("merhaba")
