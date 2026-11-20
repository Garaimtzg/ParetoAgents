"""Lee los registros de sesión de Claude Code y saca una fila por llamada al modelo.

Comprobado con Claude Code 2.1.329 (prueba del 2026-11-20):
- El hilo principal está en  <projects>/<dir>/<session_id>.jsonl
- Cada subagente está en     <projects>/<dir>/<session_id>/subagents/agent-<id>.jsonl
  con un <...>.meta.json al lado que indica `agentType` (el rol) y `model`.
- En estos archivos `usage.output_tokens` es el valor FINAL. En la salida stream-json,
  en cambio, los mensajes de subagente traen solo el recuento inicial: por eso no se usa.
- Un mensaje con varios bloques puede aparecer en varias líneas con el mismo id:
  se cuenta una sola vez.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .pricing import PriceTable, Usage


def projects_dir() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    return Path(base) / "projects"


def find_session_file(session_id: str, root: Path | None = None) -> Path:
    matches = list((root or projects_dir()).glob(f"*/{session_id}.jsonl"))
    if len(matches) != 1:
        raise FileNotFoundError(f"registro de la sesión {session_id}: {len(matches)} coincidencias")
    return matches[0]


def _assistant_usages(path: Path) -> dict[str, dict]:
    """message_id -> {model, usage}; la última línea de cada id manda."""
    out: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get("type") != "assistant":
            continue
        m = e.get("message") or {}
        if not m.get("id") or not m.get("usage") or m.get("model") == "<synthetic>":
            continue
        out[m["id"]] = {"model": m["model"], "usage": m["usage"]}
    return out


def _to_usage(u: dict) -> Usage:
    cc = u.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens")
    w1 = cc.get("ephemeral_1h_input_tokens")
    if w5 is None and w1 is None:  # formato antiguo: sin desglose → se asume 5 min
        w5, w1 = u.get("cache_creation_input_tokens", 0), 0
    return Usage(
        input_tokens=u.get("input_tokens", 0),
        cache_creation_5m_tokens=w5 or 0,
        cache_creation_1h_tokens=w1 or 0,
        cache_read_tokens=u.get("cache_read_input_tokens", 0),
        output_tokens=u.get("output_tokens", 0),
    )


def session_calls(
    session_file: Path, prices: PriceTable, main_role: str, session_id: str | None = None
) -> list[dict]:
    """Todas las llamadas de una sesión: hilo principal + subagentes."""
    session_id = session_id or session_file.stem
    sources: list[tuple[Path, str | None, str]] = [(session_file, None, main_role)]
    sub_dir = session_file.with_suffix("") / "subagents"
    for f in sorted(sub_dir.glob("agent-*.jsonl")) if sub_dir.is_dir() else []:
        agent_id = f.stem.removeprefix("agent-")
        meta_file = f.with_name(f"{f.stem}.meta.json")
        meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
        sources.append((f, agent_id, meta.get("agentType", "unknown_subagent")))

    calls = []
    for path, agent_id, role in sources:
        for message_id, rec in _assistant_usages(path).items():
            usage = _to_usage(rec["usage"])
            cost = prices.cost(rec["model"], usage)
            calls.append(
                {
                    "session_id": session_id,
                    "message_id": message_id,
                    "agent_id": agent_id,
                    "role": role,
                    "model": rec["model"],
                    "input_tokens": usage.input_tokens,
                    "cache_write_5m": usage.cache_creation_5m_tokens,
                    "cache_write_1h": usage.cache_creation_1h_tokens,
                    "cache_read": usage.cache_read_tokens,
                    "output_tokens": usage.output_tokens,
                    "prompt_tokens": usage.prompt_tokens,
                    "long_context_tier": int(cost.long_context_tier),
                    "cost_usd": cost.total,
                }
            )
    return calls


def reconcile(calls: list[dict], model_usage: dict) -> dict[str, dict[str, int]]:
    """Diferencia de tokens por modelo entre nuestras filas y el `modelUsage` de Claude Code.

    Devuelve {modelo: {campo: nuestro − suyo}}; vacío = cuadra exactamente.
    """
    fields = {
        "input_tokens": "inputTokens",
        "output_tokens": "outputTokens",
        "cache_read": "cacheReadInputTokens",
        "cache_write_5m": "cacheCreationEphemeral5mInputTokens",
        "cache_write_1h": "cacheCreationEphemeral1hInputTokens",
    }
    diffs: dict[str, dict[str, int]] = {}
    for model in {c["model"] for c in calls} | set(model_usage):
        ours = [c for c in calls if c["model"] == model]
        theirs = model_usage.get(model, {})
        d = {f: sum(c[f] for c in ours) - theirs.get(k, 0) for f, k in fields.items()}
        d = {k: v for k, v in d.items() if v}
        if d:
            diffs[model] = d
    return diffs
