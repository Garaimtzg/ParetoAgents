#!/usr/bin/env bash
# Prueba de humo barata: B1 sobre una tarea de juguete, con Haiku y tu suscripción.
# Consume muy poco límite de uso (~0,01 USD equivalentes). No necesita Docker ni Hugging Face.
set -euo pipefail
cd "$(dirname "$0")/.."

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git init -q "$TMP/toyrepo"
cat > "$TMP/toyrepo/calc.py" <<'EOF'
def average(xs):
    """Return the arithmetic mean of a list of numbers."""
    return sum(xs) / len(xs) + 1
EOF
git -C "$TMP/toyrepo" add .
git -C "$TMP/toyrepo" -c user.email=t@t -c user.name=t commit -qm base
BASE=$(git -C "$TMP/toyrepo" rev-parse HEAD)
cat > "$TMP/task.json" <<EOF
{"instance_id": "toy__calc-1", "repo": "toy/calc", "base_commit": "$BASE",
 "problem_statement": "average([2, 4]) returns 4 instead of 3. The mean is off by one."}
EOF

DB="$TMP/smoke.sqlite"
RUN=$(python -m pareto_agents --db "$DB" run --variant B1 --instance toy__calc-1 \
      --instance-file "$TMP/task.json" --repo-url "$TMP/toyrepo" --model-override claude-haiku-5-5)
python -m pareto_agents --db "$DB" show --run-id "$RUN"
echo "Cuadre de tokens con Claude Code ({} = exacto):"
cat "runs/$RUN/reconcile.json"; echo
