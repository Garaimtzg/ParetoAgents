"""Evalúa parches con el harness oficial de SWE-bench (requiere Docker en marcha).

pip install -e '.[swebench]'
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from . import db
from .config import REPO_ROOT
from .tasks import DATASET

EVAL_DIR = REPO_ROOT / "runs" / "eval"


def evaluate_run(run_id: str, db_path: str | Path = db.DEFAULT_DB) -> bool:
    conn = db.connect(db_path)
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        raise KeyError(run_id)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    model_name = row["variant"]
    eval_id = run_id.replace("/", "_")
    preds = EVAL_DIR / f"{eval_id}.jsonl"
    preds.write_text(json.dumps({
        "instance_id": row["instance_id"],
        "model_name_or_path": model_name,
        "model_patch": row["patch"] or "",
    }) + "\n")
    subprocess.run(
        [sys.executable, "-m", "swebench.harness.run_evaluation",
         "--dataset_name", DATASET,
         "--predictions_path", str(preds),
         "--instance_ids", row["instance_id"],
         "--max_workers", "1",
         "--run_id", eval_id],
        cwd=EVAL_DIR, check=True,
    )
    report_path = EVAL_DIR / f"{model_name}.{eval_id}.json"
    report = json.loads(report_path.read_text())
    resolved = row["instance_id"] in report.get("resolved_ids", [])
    db.update_run(conn, run_id, resolved=int(resolved), eval_report=json.dumps(report))
    return resolved
