from clorfy_optimize.pipeline import Pipeline


def _msg(role, content):
    return {"role": role, "content": content}


def test_pipeline_with_profile():
    messages = [
        _msg("system", "talimat"),
        *[_msg("user", f"mesaj {i}") for i in range(20)],
    ]
    pipe = Pipeline("chat")
    result = pipe.run(messages)
    assert result.tokens_after <= result.tokens_before
    assert result.tokens_saved >= 0
    assert len(result.messages) < len(messages)


def test_pipeline_manual_chain():
    messages = [
        _msg("system", "bir"),
        _msg("system", "iki"),
        _msg("user", "tekrar"),
        _msg("user", "tekrar"),
        _msg("user", "farkli"),
    ]
    pipe = Pipeline().merge_system().deduplicate().prune(keep_last=2, budget_tokens=5000)
    result = pipe.run(messages)
    system_msgs = [m for m in result.messages if m["role"] == "system"]
    assert len(system_msgs) <= 1


def test_pipeline_custom_step():
    messages = [_msg("user", "test")]
    pipe = Pipeline().add_step("upper", lambda msgs: [{**m, "content": m["content"].upper()} for m in msgs])
    result = pipe.run(messages)
    assert result.messages[0]["content"] == "TEST"


def test_pipeline_empty_input():
    pipe = Pipeline("code")
    result = pipe.run([])
    assert result.messages == []
    assert result.tokens_before == 0
    assert result.tokens_after == 0


def test_pipeline_savings_percent():
    messages = [_msg("user", f"uzun mesaj {'dolgu ' * 50}") for _ in range(30)]
    pipe = Pipeline("chat")
    result = pipe.run(messages)
    assert result.savings_percent > 0
