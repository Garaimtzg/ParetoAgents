# ParetoAgents

Si en vez de usar siempre Opus repartimos el trabajo entre Sonnet y Haiku, ¿cuánto dinero y tiempo ahorramos y cuántas tareas dejamos de resolver? Se comparan 6 topologías (10 variantes) sobre tareas de SWE-bench Verified: reparto programado a mano frente a Claude Code decidiendo solo.

**Todo funciona con tu suscripción de Claude, sin API key y sin gastar dinero.** El código quita las API keys del entorno y aborta si Claude Code fuera a usar una. Los costes se miden en USD *equivalentes* de API.

- Definición completa: [`docs/definicion_proyecto.md`](docs/definicion_proyecto.md)
- Preregistro de hipótesis y análisis: [`docs/preregistro.md`](docs/preregistro.md)
- Registro de decisiones: [`docs/decisiones.md`](docs/decisiones.md)

## Estado

| Fase | Estado | Puerta |
| --- | --- | --- |
| 0 — Definición y preregistro | **Cerrada** (etiqueta `prereg-v1`) | No quedan decisiones abiertas |
| 1 — Scaffold e infraestructura | **Código listo**; falta pasar la puerta en tu máquina | Una tarea real de extremo a extremo en B1, evaluada y con filas en SQLite |
| 2 — Calibración de telemetría | Pendiente | Error < 1 % frente a los totales de Claude Code; 100 % de los mensajes atribuidos |
| 3 — Dataset | Pendiente | 25/25/25 con criterio reproducible |
| 4 — Topologías | Pendiente | 10 variantes, < 5 % de fallos de infraestructura en el piloto |
| 5 — Ejecución masiva | Pendiente | ≥ 98 % de ejecuciones válidas |
| 6 — Análisis y paper | Pendiente | Figuras y tablas reproducibles |

## Estructura

```
config/              Configuración congelada (fuente de verdad)
  experiment.yaml    Repeticiones, semillas, presupuestos, parámetros estadísticos
  variants.yaml      6 topologías × 2 tracks: roles, modelos, esfuerzos, límites
  pricing/           Tablas de precios con la fecha de consulta
docs/                Definición, preregistro y registro de decisiones
src/pareto_agents/   Código común: carga de configuración y cálculo de coste
scripts/             Utilidades (estimación de presupuesto, …)
tests/               Tests de configuración y de precios
dataset/             Fase 3: tasks.json con las 75 tareas y su nivel
sdk_track/           Fase 4: orquestadores Python por topología
cc_track/            Fase 4: perfiles .claude/agents/ y prompts del Track CC
runner/              Fase 1: contenedor aislado por ejecución y evaluador SWE-bench
telemetry/           Fases 1–2: esquema SQLite y parser de transcripciones de Claude Code
analysis/            Fase 6: tablas .tex, figuras y estadística
```

## Uso (en tu máquina)

Requisitos: Python ≥ 3.11, git, Claude Code con sesión iniciada en tu suscripción y, para evaluar, Docker en marcha.

1. Comprueba que Claude Code usa tu suscripción y no una API key (`authMethod` no debe ser de API key):

```bash
claude auth status
```

2. Instala el proyecto:

```bash
pip install -e '.[dev,swebench]'
```

```bash
pytest
```

3. Prueba de humo con una tarea de juguete y Haiku (consume muy poco uso):

```bash
./scripts/smoke_toy.sh
```

4. **Puerta de la Fase 1:** B1 (Opus, esfuerzo alto) sobre una tarea real. Consume una parte apreciable de tu límite, unos 2–3 USD equivalentes:

```bash
python -m pareto_agents run --variant B1 --instance django__django-11099
```

5. Evalúa el parche con los tests ocultos de SWE-bench (necesita Docker y descarga imágenes grandes la primera vez). Usa el `run_id` que imprime el paso anterior:

```bash
python -m pareto_agents evaluate --run-id <run_id>
```

```bash
python -m pareto_agents show
```

Otros comandos:

```bash
python scripts/estimate_budget.py
```
