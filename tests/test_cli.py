import json

from click.testing import CliRunner

from clorfy_optimize.cli import app


def test_analyze_command_reports_savings(tmp_path):
    messages_file = tmp_path / "messages.json"
    messages = [{"role": "user", "content": f"mesaj {i} " * 20} for i in range(20)]
    messages_file.write_text(json.dumps(messages), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["analyze", str(messages_file), "--profile", "chat"])

    assert result.exit_code == 0
    assert "Tasarruf" in result.output


def test_profiles_command_lists_all_profiles():
    runner = CliRunner()
    result = runner.invoke(app, ["profiles"])

    assert result.exit_code == 0
    assert "code" in result.output
    assert "chat" in result.output
    assert "plan" in result.output
