# ParetoAgents

Si en vez de usar siempre Opus repartimos el trabajo entre Sonnet y Haiku, ¿cuánto dinero y tiempo ahorramos y cuántas tareas dejamos de resolver? Se comparan 6 topologías en 2 tracks (orquestación programada a mano con la API frente a Claude Code decidiendo solo) sobre 75 tareas de SWE-bench Verified.

- Definición completa: [`docs/definicion_proyecto.md`](docs/definicion_proyecto.md)
- Preregistro de hipótesis y análisis: [`docs/preregistro.md`](docs/preregistro.md)
- Registro de decisiones: [`docs/decisiones.md`](docs/decisiones.md)

## Estado

| Fase | Estado | Puerta |
| --- | --- | --- |
| 0 — Definición y preregistro | **Lista para firmar** (decisiones en `propuesta`) | No quedan decisiones abiertas |
| 1 — Scaffold e infraestructura | Pendiente | Una tarea de extremo a extremo en B1-SDK y B1-CC, con filas en SQLite |
| 2 — Calibración de telemetría | Pendiente | Error < 1 % frente a la factura; 100 % de los mensajes atribuidos |
| 3 — Dataset | Pendiente | 25/25/25 con criterio reproducible |
| 4 — Topologías | Pendiente | 12 variantes, < 5 % de fallos de infraestructura en el piloto |
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

## Uso

```bash
pip install -e '.[dev]'
```

```bash
pytest
```

```bash
python scripts/estimate_budget.py
```
