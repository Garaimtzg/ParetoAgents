"""CLI: python -m pareto_agents {run,evaluate,show}"""

from __future__ import annotations

import argparse
import json

from . import db
from .tasks import load_instance


def main() -> None:
    p = argparse.ArgumentParser(prog="pareto_agents")
    p.add_argument("--db", default=str(db.DEFAULT_DB))
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="ejecuta una variante sobre una tarea (usa tu suscripción)")
    r.add_argument("--variant", required=True, help="p. ej. B1")
    r.add_argument("--instance", required=True, help="instance_id de SWE-bench")
    r.add_argument("--instance-file", help="JSON local con la tarea (pruebas)")
    r.add_argument("--repo-url", help="URL del repositorio si no es GitHub (pruebas)")
    r.add_argument("--repetition", type=int, default=0)
    r.add_argument("--model-override", help="SOLO pruebas: cambia el modelo y marca la ejecución como smoke")
    r.add_argument("--keep-workspace", action="store_true")

    e = sub.add_parser("evaluate", help="pasa el parche por el evaluador de SWE-bench (Docker)")
    e.add_argument("--run-id", required=True)

    s = sub.add_parser("show", help="resumen de ejecuciones y llamadas")
    s.add_argument("--run-id")

    a = p.parse_args()
    if a.cmd == "run":
        from .runner import run_variant

        inst = load_instance(a.instance, a.instance_file)
        run_id = run_variant(
            a.variant, inst, db_path=a.db, repetition=a.repetition,
            model_override=a.model_override, repo_url=a.repo_url, keep_workspace=a.keep_workspace,
        )
        print(run_id)
    elif a.cmd == "evaluate":
        from .evaluate import evaluate_run

        print("resuelta" if evaluate_run(a.run_id, a.db) else "no resuelta")
    elif a.cmd == "show":
        conn = db.connect(a.db)
        where, args = ("WHERE run_id = ?", (a.run_id,)) if a.run_id else ("", ())
        for row in conn.execute(
            f"""SELECT run_id, status, resolved, num_turns, round(wall_s,1) wall_s,
                       round(cost_computed_usd,4) cost_usd, round(cost_reported_usd,4) cost_cc_usd
                FROM runs {where} ORDER BY started_at""", args):
            print(json.dumps(dict(row)))
            for c in conn.execute(
                """SELECT role, model, count(*) calls, sum(prompt_tokens) prompt, sum(output_tokens) out,
                          round(sum(cost_usd),4) cost_usd
                   FROM calls WHERE run_id = ? GROUP BY role, model""", (row["run_id"],)):
                print("   ", json.dumps(dict(c)))


if __name__ == "__main__":
    main()
