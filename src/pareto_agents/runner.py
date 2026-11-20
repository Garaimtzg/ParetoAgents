"""Ejecuta una variante sobre una tarea y guarda el resultado en SQLite.

Fase 1: solo las variantes de un único modelo (B1, B2). El resto llega en la Fase 4.
"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import claude_cli, db, transcripts, workspace
from .config import REPO_ROOT, load_experiment, load_variants, load_yaml
from .pricing import PriceTable

TASK_PROMPT = """\
You are working in a git checkout of the Python repository `{repo}`.
Resolve the following GitHub issue by editing the source code in the current directory.

<issue>
{problem_statement}
</issue>

Rules:
- Make the minimal change that fixes the issue. Do not modify existing tests.
- You cannot run the code or the tests: reason from the source.
- When you are done, reply with a one-paragraph summary of the change.
"""

# Herramientas comunes: leer y editar, más git de solo lectura. Sin ejecución de código.
BASE_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)", "Bash(git show:*)",
]
SUBAGENT_TOOLS = ["Agent", "Task"]  # nombres de la herramienta de subagentes


def _variant(variant_id: str):
    for v in load_variants():
        if v.id == variant_id:
            return v
    raise KeyError(f"variante desconocida: {variant_id}")


def run_variant(
    variant_id: str,
    instance: dict,
    *,
    db_path: str | Path = db.DEFAULT_DB,
    repetition: int = 0,
    model_override: str | None = None,
    repo_url: str | None = None,
    keep_workspace: bool = False,
) -> str:
    v = _variant(variant_id)
    if len(v.roles) != 1:
        raise NotImplementedError(f"{variant_id}: las topologías con varios roles llegan en la Fase 4")
    role = v.roles[0]
    exp = load_experiment()
    limits = load_yaml(exp["variants_file"])["limits"]
    prices = PriceTable.load(REPO_ROOT / exp["pricing_file"])
    model = model_override or role.model

    run_id = f"{variant_id}__{instance['instance_id']}__r{repetition}__{uuid.uuid4().hex[:8]}"
    conn = db.connect(db_path)
    db.insert_run(
        conn, run_id=run_id, variant=v.id, topology=v.topology, track=v.track,
        instance_id=instance["instance_id"], repetition=repetition, smoke=int(bool(model_override)),
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    logs = REPO_ROOT / "runs" / run_id
    logs.mkdir(parents=True, exist_ok=True)
    work = workspace.prepare(instance["repo"], instance["base_commit"], repo_url)
    status = "infra_error"
    try:
        cmd = claude_cli.build_command(
            TASK_PROMPT.format(**instance),
            model=model,
            effort=role.effort,
            max_turns=limits["max_turns_orchestrator"],
            max_budget_usd=exp["budget_usd"]["per_run_cap"],
            allowed_tools=BASE_TOOLS,
            disallowed_tools=SUBAGENT_TOOLS,  # B1/B2: trabajan solos
        )
        try:
            res = claude_cli.run(cmd, work, limits["wall_clock_timeout_s"], logs / "stream.jsonl")
        except claude_cli.AuthRefused:
            db.update_run(conn, run_id, status="auth_refused",
                          ended_at=datetime.now(timezone.utc).isoformat())
            raise

        r = res.result
        if res.timed_out:
            status = "timeout"
        elif r.get("subtype") == "error_max_budget_usd":
            status = "budget"
        elif r and not r.get("is_error"):
            status = "completed"
        elif r:
            status = "model_error"

        calls = []
        if res.session_id:
            sess = transcripts.find_session_file(res.session_id)
            calls = transcripts.session_calls(sess, prices, role.role, res.session_id)
            db.insert_calls(conn, run_id, calls)
            if r.get("modelUsage"):
                diffs = transcripts.reconcile(calls, r["modelUsage"])
                (logs / "reconcile.json").write_text(json.dumps(diffs, indent=2))

        db.update_run(
            conn, run_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            wall_s=res.wall_s,
            claude_version=res.claude_version,
            session_ids=json.dumps([res.session_id] if res.session_id else []),
            status=status,
            num_turns=r.get("num_turns"),
            cost_reported_usd=r.get("total_cost_usd"),
            cost_computed_usd=sum(c["cost_usd"] for c in calls),
            patch=workspace.diff(work),
        )
        (logs / "stderr.txt").write_text(res.stderr)
    finally:
        if not keep_workspace:
            shutil.rmtree(work, ignore_errors=True)
    return run_id
