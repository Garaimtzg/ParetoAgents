# ParetoAgents — Preregistro de hipótesis y análisis

**Versión:** 1.0 · **Fecha:** 2026-11-20 · **Estado:** congelado (`prereg-v1`)

Este documento congela, **antes de ver ningún resultado**, qué se va a medir, cómo y con qué criterios se aceptan o rechazan las hipótesis. Complementa a [`definicion_proyecto.md`](definicion_proyecto.md). Los valores numéricos viven en [`config/experiment.yaml`](../config/experiment.yaml) y [`config/variants.yaml`](../config/variants.yaml); si este texto y la configuración no coinciden, manda la configuración y se corrige el texto.

Cualquier cambio posterior se apunta en [`decisiones.md`](decisiones.md) con fecha, motivo y si se hizo antes o después de ver datos. Los análisis no previstos aquí se publicarán, pero etiquetados como **exploratorios**.

> **Firma.** Cuando el responsable dé por buenas las decisiones D-001 a D-009 de `decisiones.md`, se cambia el estado a "congelado", se crea la etiqueta git `prereg-v1` y, opcionalmente, se deposita en OSF.

---

## 1. Variantes (12)

6 topologías × 2 tracks. Todos los esfuerzos se fijan de forma explícita (Opus 5.5 y Haiku 5.5 usan `medium` por defecto y Sonnet 5.5 `high`; dejarlo por defecto cambiaría la comparación sin que se note).

| Topología | Rol | Modelo | Esfuerzo | Notas |
| --- | --- | --- | --- | --- |
| **B1** | solo | Opus 5.5 | high | Sin subagentes en CC |
| **B2** | solo | Sonnet 5.5 | high | Sin subagentes en CC |
| **A1** | planner | Opus 5.5 | high | |
| | coder | Sonnet 5.5 | medium | Lee solo los archivos que cita el plan (SDK) |
| **A2** | planner | Opus 5.5 | high | |
| | coder | Sonnet 5.5 | medium | En paralelo con test_writer |
| | test_writer | Haiku 5.5 | low | Tests, tipos, código de relleno |
| **A3** | explorer | Haiku 5.5 | low | En CC, subagente propio con modelo fijado (no el Explore integrado) |
| | planner | Opus 5.5 | high | Solo ve el resumen del explorador |
| | coder | Sonnet 5.5 | medium | |
| **A4** | solo | Sonnet 5.5 | medium | |
| | escalation | Opus 5.5 | high | Máx. 1 escalada. Disparador: fallan las comprobaciones **visibles** del agente |

**Track SDK:** un programa Python sigue exactamente los pasos de cada fila. **Track CC:** Claude Code headless (`claude -p`) con los mismos roles definidos como subagentes en `.claude/agents/`; el modelo principal decide cuándo delegar.

**Límites comunes:** 100 pasos para el principal, 50 por invocación de subagente, 60 min de reloj y 10 USD por ejecución.

**Por qué "medium" para los ejecutores:** la definición dice "bajo/medio". Se elige `medium` porque Sonnet 5.5 recalibró los niveles y en tareas agénticas de código `low` arriesga que A1/A2 fallen por el ejecutor y no por la topología. `low` queda como posible análisis de sensibilidad, **exploratorio**.

**Regla de A4 (importante):** el disparador de la escalada nunca son los tests ocultos de SWE-bench: eso filtraría la respuesta. Escala cuando fallan los tests que el propio agente ejecuta dentro del contenedor (los del repositorio o los que él mismo escribe), o cuando Sonnet declara que no ha podido resolver la tarea.

## 2. Datos

- 75 tareas de SWE-bench Verified: 25 de nivel 1, 25 de nivel 2 y 25 de nivel 3, equilibradas por repositorio.
- **Regla de nivel** (sobre el parche oficial, sin contar archivos de test), aplicada en la Fase 3:
  - Nivel 1: 1–2 archivos y ≤ 30 líneas cambiadas.
  - Nivel 2: 3–6 archivos, o 1–2 archivos con > 30 líneas.
  - Nivel 3: ≥ 7 archivos, o ≥ 3 archivos con ≥ 150 líneas.
  - Si un nivel tiene menos de 25 candidatas, se aplica la mitigación de riesgos (§5 de la definición) y se apunta en `decisiones.md`. Los umbrales de líneas se pueden ajustar **una sola vez**, en la Fase 3 y mirando solo los parches (nunca resultados de modelos).
- Las 5 tareas del piloto (Fases 2 y 4) se excluyen de las 75 del análisis.

## 3. Ejecución

- **Ronda principal:** 12 × 75 = 900 ejecuciones, en orden aleatorio (semilla 20261120), máx. 4 a la vez.
- **Repeticiones:** subconjunto estratificado de 15 tareas (5 por nivel, semilla 20261120), 2 repeticiones más para las 12 variantes (360 ejecuciones). Sirven para medir la variabilidad de una misma tarea y no se mezclan con la ronda principal en los contrastes de las hipótesis.
- **Caché:** entre dos ejecuciones de la misma tarea pasan al menos 10 min (el TTL es 5 min). Se marcan como "contaminadas" las ejecuciones cuya primera llamada ya trae `cache_read > 0`.
- **Fallos de infraestructura** (contenedor no arranca, error 5xx o de red persistente, error del evaluador): se reintentan hasta 2 veces. **Fallos del modelo** (no resuelve, agota pasos, agota tiempo, supera el tope de 10 USD, rompe tests que pasaban): no se reintentan y cuentan como tarea no resuelta, con todo su coste.
- **Validez:** una ejecución es válida si termina con un veredicto del evaluador. Puerta de la Fase 5: ≥ 98 % válidas.

## 4. Métricas

Todo coste se calcula con `pareto_agents.pricing` a partir de los tokens y de la tabla de precios con fecha. El coste que muestra Claude Code solo sirve para comprobar que cuadra.

| Métrica | Definición operativa |
| --- | --- |
| Resuelta | Pasan todos los tests FAIL_TO_PASS y PASS_TO_PASS de SWE-bench |
| Pass@1 | Resueltas / 75 (ronda principal) |
| Coste por ejecución | Suma de todas las llamadas de la ejecución (todos los roles) |
| **Coste por tarea resuelta** (principal) | Σ coste de las 75 ejecuciones / nº de resueltas |
| Impuesto de autonomía | Coste medio CC / coste medio SDK de la misma topología |
| Coste de coordinación | Tokens de los mensajes de delegación + resúmenes devueltos + relecturas de archivos que ya había leído el orquestador, pasados a USD |
| Haiku > 100K | % de llamadas a Haiku con prompt > 100.000 tokens (entrada + caché) |
| Tiempo | Segundos de reloj desde el arranque del agente hasta el parche final (sin contar el contenedor ni el evaluador) |

## 5. Hipótesis y criterios de decisión

α = 0,05. Corrección de Holm dentro de cada familia de contrastes. IC por bootstrap por tarea (10.000 remuestreos, semilla 20261120).

**H1 — Repartir sale más barato.** Familia: {A1, A2} × {SDK, CC} frente a B1 del mismo track (4 contrastes).
- (a) Coste por tarea resuelta menor que B1: el IC 95 % del cociente A/B1 queda entero por debajo de 1.
- (b) No inferioridad en Pass@1 global: el límite inferior del IC 95 % de la diferencia pareada (A − B1) es > −10 puntos.
- (c) Criterio descriptivo de la definición: diferencia puntual ≥ −5 puntos en los niveles 1 y 2. Se informa, pero no decide (ver §8).
- H1 se apoya para una variante si se cumplen (a) y (b).

**H2 — Los ayudantes protegen al jefe.** Solo Track CC. Para A1, A2 y A3: los tokens de prompt de Opus por tarea (entrada + caché) son menores que los de B1-CC. Wilcoxon de rangos con signo pareado por tarea, unilateral, con Holm sobre 3 contrastes.

**H3 — Empezar de cero tiene un precio.** Para cada invocación de subagente se calcula `relectura` = tokens de archivos que el subagente lee y el orquestador ya había leído en esa ejecución. Predicción: correlación de Spearman positiva (ρ > 0, p < 0,05) entre la relectura por tarea y el sobrecoste (coste de A − coste de B1 en esa tarea), en las variantes CC con subagentes. Además, se informa qué parte de las delegaciones nombran archivos concretos; la comparación "con rutas" frente a "sin rutas" es **exploratoria**, porque no se controla.

**H4 — La trampa de Haiku.** En A2 y A3 (ambos tracks), nivel 3: (a) más del 20 % de las llamadas a Haiku superan 100K; y (b) el sobrecoste del tramo caro (coste real − coste con tarifa ≤ 100K) es ≥ 10 % del gasto en Haiku. Descriptiva, con IC bootstrap.

**H5 — La autonomía cuesta.** Para cada una de las 6 topologías: coste por ejecución de CC > SDK. Wilcoxon pareado por tarea, unilateral, con Holm sobre 6 contrastes. También se informa el cociente con su IC.

**RQ3 y RQ5** son descriptivas: Pass@1 por nivel y topología con IC de Wilson; tiempo de A2 frente a A1 (Wilcoxon pareado, bilateral) en cada track.

## 6. Análisis

- Pass@1 pareado: McNemar exacto. Coste y tiempo: Wilcoxon de rangos con signo. Cocientes y diferencias: bootstrap por tarea.
- Frontera de Pareto: Pass@1 frente a coste por tarea resuelta, con las 12 variantes y sus IC.
- **Sensibilidad** (se informan, no deciden): (i) excluir ejecuciones con caché contaminada; (ii) excluir las que tocan el tope de 10 USD; (iii) variabilidad entre repeticiones en el subconjunto de 15 tareas.
- Taxonomía de fallos: clasificación automática (agota pasos, agota tiempo o presupuesto, parche no aplica, tests rotos) más revisión manual de una muestra aleatoria de 40 fallos, con categorías fijas: plan erróneo, implementación defectuosa del subagente, conflicto de interfaz entre subagentes, agotamiento de `maxTurns` y otros.

## 7. Presupuesto y paradas

- Estimación a priori ([`scripts/estimate_budget.py`](../scripts/estimate_budget.py)): ~1,9 USD de media por ejecución y **~2.600 USD** en total (1.335 ejecuciones). Los perfiles de tokens son supuestos y la Fase 2 los sustituye por medidas.
- **Tope de campaña: 4.000 USD.** Tope por ejecución: 10 USD. Tope del piloto de la Fase 2: 150 USD.
- **Regla de parada:** si tras la Fase 2 la estimación recalculada supera el tope, se recorta en este orden, sin mirar resultados: (1) repeticiones de 2 a 1, (2) subconjunto de 15 a 9 tareas, (3) se consulta antes de recortar variantes. Durante la Fase 5, si el gasto acumulado supera 1,25 × lo estimado para ese punto, se pausa y se revisa.

## 8. Potencia estadística (limitación conocida)

Con 75 tareas pareadas y un 15–20 % de pares discordantes, el IC 95 % de una diferencia de Pass@1 mide unos ±9–10 puntos; con los 25 de cada nivel, unos ±16. **Por eso un margen de 5 puntos no se puede demostrar estadísticamente con este tamaño.** Por eso el margen formal es de 10 puntos sobre las 75 tareas y el de 5 puntos por nivel queda como criterio descriptivo. Si se quisiera demostrar el margen de 5 puntos, harían falta del orden de 300 o más tareas por comparación, y eso queda fuera del presupuesto.
