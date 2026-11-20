"""Carga de tareas de SWE-bench Verified (o de un JSON local para pruebas)."""

from __future__ import annotations

import json
from pathlib import Path

DATASET = "princeton-nlp/SWE-bench_Verified"
REQUIRED = ("instance_id", "repo", "base_commit", "problem_statement")


def load_instance(instance_id: str, instance_file: str | Path | None = None) -> dict:
    if instance_file:
        data = json.loads(Path(instance_file).read_text())
        items = data if isinstance(data, list) else [data]
    else:
        from datasets import load_dataset  # dependencia opcional: pip install -e '.[swebench]'

        items = load_dataset(DATASET, split="test").filter(lambda r: r["instance_id"] == instance_id)
    for item in items:
        if item["instance_id"] == instance_id:
            missing = [k for k in REQUIRED if k not in item]
            if missing:
                raise ValueError(f"{instance_id}: faltan campos {missing}")
            return dict(item)
    raise KeyError(f"tarea no encontrada: {instance_id}")
