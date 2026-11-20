import json
import stat

import pytest

from pareto_agents import claude_cli


def fake_claude(tmp_path, api_key_source: str):
    """Script que imita la salida stream-json de `claude -p` y anota su entorno."""
    script = tmp_path / "claude"
    events = [
        {"type": "system", "subtype": "init", "session_id": "s1",
         "apiKeySource": api_key_source, "claude_code_version": "9.9.9"},
        {"type": "result", "subtype": "success", "is_error": False, "session_id": "s1",
         "num_turns": 1, "total_cost_usd": 0.01},
    ]
    body = "\n".join(f"echo '{json.dumps(e)}'" for e in events)
    script.write_text(
        "#!/bin/sh\n"
        f'env > "{tmp_path}/env.txt"\n'
        f"{body}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def _cmd(bin_):
    return claude_cli.build_command(
        "hola", model="claude-haiku-5-5", effort="low", max_turns=5, max_budget_usd=1,
        allowed_tools=["Read"], disallowed_tools=["Agent"], claude_bin=bin_,
    )


def test_api_keys_are_stripped_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "tok-should-not-leak")
    res = claude_cli.run(_cmd(fake_claude(tmp_path, "none")), tmp_path, timeout_s=30)
    env = (tmp_path / "env.txt").read_text()
    assert "should-not-leak" not in env
    assert res.session_id == "s1" and res.claude_version == "9.9.9"
    assert res.result["subtype"] == "success"


def test_refuses_when_claude_would_bill_an_api_key(tmp_path):
    with pytest.raises(claude_cli.AuthRefused):
        claude_cli.run(_cmd(fake_claude(tmp_path, "ANTHROPIC_API_KEY")), tmp_path, timeout_s=30)


def test_command_never_uses_bare_mode():
    cmd = _cmd("claude")
    assert "--bare" not in cmd
    assert cmd[cmd.index("--effort") + 1] == "low"
    assert cmd[cmd.index("--disallowedTools") + 1] == "Agent"
