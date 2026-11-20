# Registro de decisiones

Cada decisión lleva fecha y estado y dice si se tomó **antes** o **después** de ver datos de modelos. Estados: `propuesta` (pendiente de que el responsable la confirme), `aceptada` o `sustituida por D-xxx`.

La Fase 0 termina cuando D-001 a D-009 pasan a `aceptada`. **Aceptadas el 2026-11-20 → Fase 0 cerrada (`prereg-v1`).**

| ID | Fecha | Decisión | Estado | ¿Datos vistos? |
| --- | --- | --- | --- | --- |
| D-001 | 2026-11-20 | Se mantienen **12 variantes** (6 topologías × 2 tracks). | aceptada | No |
| D-002 | 2026-11-20 | Esfuerzos: Opus `high` en todos sus roles; Sonnet `high` en B2 y `medium` como ejecutor; Haiku `low`. | aceptada | No |
| D-003 | 2026-11-20 | Equivalencia con B1: margen formal de **10 puntos** de Pass@1 global; **5 puntos** por nivel como criterio descriptivo. | aceptada | No |
| D-004 | 2026-11-20 | Repeticiones: 1 ronda completa + 2 repeticiones de un subconjunto estratificado de 15 tareas. | aceptada | No |
| D-005 | 2026-11-20 | Presupuesto: tope de campaña de **4.000 USD**, 10 USD por ejecución y 150 USD para el piloto. | aceptada | No |
| D-006 | 2026-11-20 | Publicación: preprint en arXiv con código y datos abiertos; la revista o congreso se decide en la Fase 6. | aceptada | No |
| D-007 | 2026-11-20 | A4 escala con las comprobaciones visibles del agente, nunca con los tests ocultos. Máximo 1 escalada. | aceptada | No |
| D-008 | 2026-11-20 | Límites comunes: 100 pasos para el principal, 50 por subagente, 60 min y `max_tokens` 64K con streaming. | aceptada | No |
| D-009 | 2026-11-20 | Regla de nivel basada en archivos y líneas del parche oficial (preregistro §2), ajustable una sola vez en la Fase 3. | aceptada | No |
| D-010 | 2026-11-20 | Precios confirmados en la web de Anthropic: la lectura de caché de Sonnet 5.5 cuesta **0,10 USD** (no 0,20); Haiku 5.5 > 100K cobra 0,625 USD (escritura 5 min) y 1,00 USD (escritura 1 h). | aceptada | No |
| D-011 | 2026-11-20 | Todas las ejecuciones (los dos tracks) se pagan con una **API key** de un workspace propio de la Console, nunca con la suscripción de Claude. | aceptada | No |

## Motivos

**D-001 — 12 variantes.** El "10" de la propuesta original no corresponde a ninguna combinación del diseño. Quitar una topología rompería la comparación pareada SDK frente a CC, que es justo la RQ2. El coste añadido de las 2 variantes extra es de unos 300 USD.

**D-002 — Esfuerzos.** La definición dice "bajo/medio" para los ejecutores. Se elige `medium` para que, si A1 o A2 fallan, sea por la topología y no por un ejecutor con poco esfuerzo. En Opus 5.5 el pensamiento no se puede desactivar: el esfuerzo es el único control, y por eso se fija siempre de forma explícita.

**D-003 — Margen.** Con n = 75 no se puede demostrar un margen de 5 puntos (ver preregistro §8). Se mantiene como criterio descriptivo para no perder la intención de la H1.

**D-004 — Repeticiones.** Repetir todo multiplica el coste por 3 (unos 5.000 USD más). 15 tareas × 3 ejecuciones bastan para estimar la variabilidad dentro de una tarea y ponerla en el margen de error.

**D-005 — Presupuesto.** La estimación a priori es de unos 2.600 USD (`scripts/estimate_budget.py`) y el tope deja un 50 % de margen para el error de esa estimación. Los 10 USD por ejecución son unas 4 veces el coste esperado de B1.

**D-007 — A4.** Usar los tests ocultos como señal de escalada sería una fuga de información: A4 parecería mejor de lo que es.

**D-010 — Precios.** Resuelve dos puntos que la definición dejaba "por confirmar". Queda guardado en `config/pricing/2026-11-20.yaml`. Además: en Haiku, el límite de 100K cuenta también las lecturas y escrituras de caché, y si se supera, la petición entera, salida incluida, paga la tarifa cara.

**D-011 — API key.** (1) La puerta de la Fase 2 exige cuadrar el coste con la factura, y la suscripción no factura por token. (2) Los límites de uso de la suscripción cortarían la campaña a medias. (3) Los dos tracks se pagan igual. Se usa un workspace propio de la Console con un límite de gasto de 4.000 USD, así la factura solo contiene el experimento. El runner se niega a arrancar sin `ANTHROPIC_API_KEY`, y la Fase 1 comprueba que `claude -p` cobra a esa clave y no a la sesión de la suscripción.

## Pendiente de verificar en fases posteriores (no bloquea la Fase 0)

- **Fase 1:** versión exacta de Claude Code que se congela, y cómo se desactivan los subagentes en B1/B2-CC (bloquear la herramienta de subagentes con `--disallowedTools`).
- **Fase 2:** si Claude Code permite fijar el esfuerzo por subagente. Si no, se documenta como asimetría entre tracks (riesgo ya listado en la definición).
- **Fase 2:** la cifra de 0,10 USD se contrasta además con la factura del piloto.
