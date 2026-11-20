"""Estimación A PRIORI del coste de la campaña (Fase 0).

Los perfiles de tokens son supuestos razonados, no medidas: la Fase 2 los
sustituye por los del piloto de 5 tareas. Sirve para fijar el tope de gasto
del preregistro y para tener una referencia contra la que comparar el piloto.

Uso:  python scripts/estimate_budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pareto_agents.config import REPO_ROOT, load_experiment, load_variants  # noqa: E402
from pareto_agents.pricing import PriceTable, Usage  # noqa: E402

K = 1_000

# Perfil por (topología, rol): (nº llamadas, prompt medio por llamada, fracción
# del prompt que es lectura de caché, tokens escritos en caché por llamada, salida por llamada).
# Supuesto base: un agente de SWE-bench da ~40 pasos con un contexto medio de ~60K.
PROFILES = {
    ("B1", "solo"): (40, 60 * K, 0.90, 4 * K, 1.0 * K),
    ("B2", "solo"): (45, 60 * K, 0.90, 4 * K, 1.0 * K),
    ("A1", "planner"): (15, 40 * K, 0.85, 4 * K, 1.5 * K),
    ("A1", "coder"): (25, 35 * K, 0.90, 3 * K, 0.8 * K),
    ("A2", "planner"): (15, 40 * K, 0.85, 4 * K, 1.5 * K),
    ("A2", "coder"): (20, 35 * K, 0.90, 3 * K, 0.8 * K),
    ("A2", "test_writer"): (20, 45 * K, 0.90, 3 * K, 0.8 * K),
    ("A3", "explorer"): (25, 50 * K, 0.90, 3 * K, 0.6 * K),
    ("A3", "planner"): (6, 25 * K, 0.60, 6 * K, 2.0 * K),
    ("A3", "coder"): (25, 35 * K, 0.90, 3 * K, 0.8 * K),
    ("A4", "solo"): (45, 60 * K, 0.90, 4 * K, 1.0 * K),
    ("A4", "escalation"): (8, 70 * K, 0.30, 50 * K, 1.5 * K),  # solo en ~40 % de tareas
}
ESCALATION_RATE = 0.40
CC_OVERHEAD = 1.30  # Claude Code añade su system prompt, herramientas y delegación


def run_cost(prices: PriceTable, variant) -> float:
    total = 0.0
    for role in variant.roles:
        calls, prompt, read_frac, written, out = PROFILES[(variant.topology, role.role)]
        cache_read = int(prompt * read_frac)
        cache_write = min(written, prompt - cache_read)
        usage = Usage(
            input_tokens=prompt - cache_read - cache_write,
            cache_creation_5m_tokens=cache_write,
            cache_read_tokens=cache_read,
            output_tokens=int(out),
        )
        cost = calls * prices.cost(role.model, usage).total
        if role.role == "escalation":
            cost *= ESCALATION_RATE
        total += cost
    return total * (CC_OVERHEAD if variant.track == "cc" else 1.0)


def main() -> None:
    exp = load_experiment()
    prices = PriceTable.load(REPO_ROOT / exp["pricing_file"])
    variants = load_variants()

    per_run = {v.id: run_cost(prices, v) for v in variants}
    mean = sum(per_run.values()) / len(per_run)

    n_tasks = exp["dataset"]["tasks_per_level"] * len(exp["dataset"]["levels"])
    rep = exp["repetitions"]
    n_subset = rep["subset_tasks_per_level"] * len(exp["dataset"]["levels"])
    pilot_runs = 3 * exp["dataset"]["pilot_tasks"] + len(variants) * exp["dataset"]["pilot_tasks"]

    runs = {
        "Piloto Fase 2 (B1-SDK, B1-CC, A1-CC × 5)": 3 * exp["dataset"]["pilot_tasks"],
        "Humo Fase 4 (12 variantes × 5)": len(variants) * exp["dataset"]["pilot_tasks"],
        "Ronda principal (12 × 75)": len(variants) * n_tasks * rep["main_round"],
        "Repeticiones (12 × 15 × 2)": len(variants) * n_subset * rep["extra_repetitions"],
    }
    assert sum(list(runs.values())[:2]) == pilot_runs

    print("Coste estimado por ejecución (USD, a priori):")
    for vid, c in sorted(per_run.items()):
        print(f"  {vid:7s} {c:6.2f}")
    print(f"  media   {mean:6.2f}\n")

    grand = 0.0
    for label, n in runs.items():
        c = n * mean
        grand += c
        print(f"{label:45s} {n:5d} ejecuciones  ~{c:8.0f} USD")
    retry_factor = 1.05  # reintentos de infraestructura
    print(f"{'Total (+5 % reintentos de infraestructura)':45s} {'':19s}~{grand * retry_factor:8.0f} USD")
    print(f"Tope preregistrado de campaña: {exp['budget_usd']['campaign_cap']} USD")


if __name__ == "__main__":
    main()
