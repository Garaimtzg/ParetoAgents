"""Lanza `claude -p` SIEMPRE con la suscripción de Claude (nunca con API key).

Garantías (decisión D-012):
1. Se quitan del entorno ANTHROPIC_API_KEY y ANTHROPIC_AUTH_TOKEN antes de lanzar.
2. Si el evento `init` informa de un `apiKeySource` distinto de "none" (es decir,
   Claude Code iba a cobrar a una API key), el proceso se mata antes de la primera
   llamada al modelo y la ejecución queda como `auth_refused`.
3. No se usa `--bare`, porque ese modo exige API key.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

BLOCKED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


class AuthRefused(RuntimeError):
    """Claude Code iba a usar una API key: se aborta para no gastar dinero."""


@dataclass
class ClaudeResult:
    session_id: str | None = None
    claude_version: str | None = None
    api_key_source: str | None = None
    result: dict = field(default_factory=dict)  # último evento `result`
    exit_code: int | None = None
    timed_out: bool = False
    wall_s: float = 0.0
    stderr: str = ""


def subscription_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    for k in BLOCKED_ENV:
        env.pop(k, None)
    return env


def build_command(
    prompt: str,
    *,
    model: str,
    effort: str,
    max_turns: int,
    max_budget_usd: float,
    allowed_tools: list[str],
    disallowed_tools: list[str] = (),
    agents: dict | None = None,
    claude_bin: str = "claude",
) -> list[str]:
    cmd = [
        claude_bin, "-p", prompt,
        "--model", model,
        "--effort", effort,
        "--max-turns", str(max_turns),
        "--max-budget-usd", str(max_budget_usd),
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "project",
        "--allowedTools", *allowed_tools,
    ]
    if disallowed_tools:
        cmd += ["--disallowedTools", *disallowed_tools]
    if agents:
        cmd += ["--agents", json.dumps(agents)]
    return cmd


def run(cmd: list[str], cwd: Path, timeout_s: float, log_path: Path | None = None) -> ClaudeResult:
    res = ClaudeResult()
    t0 = time.monotonic()
    log = open(log_path, "w") if log_path else None
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=subscription_env(), text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            if log:
                log.write(line)
            if time.monotonic() - t0 > timeout_s:
                res.timed_out = True
                proc.kill()
                break
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "system" and e.get("subtype") == "init":
                res.session_id = e.get("session_id")
                res.claude_version = e.get("claude_code_version")
                res.api_key_source = e.get("apiKeySource")
                if res.api_key_source not in (None, "none"):
                    proc.kill()
                    raise AuthRefused(
                        f"Claude Code iba a usar una API key ({res.api_key_source}). "
                        "Abortado antes de la primera llamada: este proyecto usa solo la suscripción."
                    )
            elif e.get("type") == "result":
                res.result = e
                res.session_id = e.get("session_id", res.session_id)
        try:
            proc.wait(timeout=max(1.0, timeout_s - (time.monotonic() - t0)))
        except subprocess.TimeoutExpired:
            res.timed_out = True
            proc.kill()
            proc.wait()
    finally:
        if log:
            log.close()
        res.stderr = proc.stderr.read() if proc.stderr else ""  # type: ignore[union-attr]
        res.exit_code = proc.returncode
        res.wall_s = time.monotonic() - t0
    return res
