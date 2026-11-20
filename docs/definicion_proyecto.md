# ParetoAgents — Definición del proyecto

Nov 20, 2026 · @Garai

## 1. Qué es ParetoAgents

ParetoAgents responde a una pregunta: si en vez de usar siempre el modelo más caro (Opus) para todo, repartimos el trabajo entre modelos más baratos (Sonnet y Haiku), ¿cuánto dinero y tiempo ahorramos, y cuántas tareas dejamos de resolver bien?

Hay dos maneras de montar ese reparto de trabajo, y el proyecto compara las dos con las mismas tareas:

- **Track SDK — reparto programado a mano:** escribimos un programa en Python que decide paso a paso qué modelo hace qué. Por ejemplo: "primero Opus escribe un plan; después se le pasa ese plan a Sonnet para que escriba el código". El reparto es siempre igual y lo controlamos nosotros: cuánto piensa cada modelo, qué información recibe y qué texto se reutiliza para pagar menos.
- **Track CC — Claude Code decide:** usamos Claude Code, la herramienta de Anthropic para programar, ejecutada desde un script. Le damos un equipo de ayudantes ya configurados (por ejemplo, uno con Sonnet que escribe código y otro con Haiku que escribe tests). El modelo principal decide por sí solo cuándo pasar trabajo a cada ayudante.

La razón para probarlo es el precio: Opus cobra 40 veces más que Haiku por cada texto que lee. Además, cuando un modelo vuelve a leer un texto que ya leyó hace poco (la "caché"), solo se paga entre un 5% y un 10% del precio normal. Si parte del trabajo se puede pasar a un modelo barato sin que fallen las pruebas, el ahorro es grande.

### Preguntas de investigación

1. **RQ1 — Mejor relación coste/resultado:** ¿qué forma de repartir el trabajo resuelve más tareas por cada dólar, sin quedarse muy por debajo de Opus trabajando solo?
2. **RQ2 — "Impuesto de autonomía":** con el mismo reparto, ¿sale más caro dejar que Claude Code decida (Track CC) que programarlo a mano (Track SDK)?
3. **RQ3 — Límite de Haiku:** ¿a partir de qué dificultad de tarea pasar trabajo a Haiku hace que fallen muchas tareas?
4. **RQ4 — Coste de coordinarse:** ¿cuánto se gasta solo en explicar a cada ayudante qué hacer, recibir sus resúmenes y que vuelva a leer archivos que el principal ya había leído?
5. **RQ5 — Tiempo:** ¿cuánto tiempo real se ahorra cuando varios ayudantes trabajan a la vez (A2) en lugar de uno detrás de otro (A1)?

### Glosario rápido

| Término | Qué significa |
| --- | --- |
| Opus, Sonnet, Haiku | Los tres modelos de Claude 5.5. Opus es el más capaz y caro; Haiku, el más barato y rápido; Sonnet está en medio. |
| Token / MTok | Un token es un trozo de palabra: es la unidad en la que se cobra el texto. MTok = un millón de tokens. |
| Entrada / salida | Entrada es el texto que el modelo lee; salida, el que escribe. La salida es 5 veces más cara. |
| Effort (esfuerzo) | Cuánto "piensa" el modelo antes de responder. Más esfuerzo suele dar mejores respuestas, pero gasta más tokens. |
| Caché | Si se envía otra vez un texto que el modelo leyó hace poco, se cobra mucho más barato. Guardarlo la primera vez cuesta un poco más. |
| Orquestador | El modelo principal: reparte el trabajo y junta los resultados. |
| Subagente (ayudante) | Un modelo al que el orquestador encarga una parte del trabajo. Empieza sin saber nada de lo anterior y devuelve solo un resumen. |
| Cold-start | El coste de que un ayudante empiece de cero y tenga que releer archivos que el orquestador ya conocía. |
| Headless (`claude -p`) | Ejecutar Claude Code desde un script, sin nadie delante, para poder lanzar cientos de tareas seguidas. |
| SWE-bench Verified | Colección pública de errores reales de proyectos Python de GitHub, cada uno con tests que comprueban si el arreglo funciona. |
| Pass@1 | Porcentaje de tareas resueltas al primer intento (pasan todos los tests). |
| Frontera de Pareto | Las opciones en las que no se puede gastar menos sin resolver menos tareas. Las demás son peores en todo. |
| Telemetría | Registro automático de cuántos tokens gasta cada modelo en cada tarea, para calcular el coste exacto. |

## 2. Alcance, tarifas e hipótesis

El proyecto cubre 6 topologías × 2 tracks = **12 variantes**, ejecutadas sobre 75 tareas de SWE-bench Verified. Queda fuera: otros proveedores de modelos, fine-tuning y tareas que no sean de código.

### Tarifas de referencia (USD por millón de tokens)

| Modelo | Entrada | Salida | Escritura caché 5 min | Escritura caché 1 h | Lectura caché |
| --- | --- | --- | --- | --- | --- |
| Opus 5.5 | 4,00 | 20,00 | 5,00 | 8,00 | 0,20 |
| Sonnet 5.5 | 2,00 | 10,00 | 2,50 | 4,00 | 0,10 |
| Haiku 5.5 (prompt ≤ 100K) | 0,10 | 0,50 | 0,125 | 0,20 | 0,01 |
| Haiku 5.5 (prompt > 100K) | 0,50 | 2,50 | por confirmar | por confirmar | 0,05 |

Fuente: [página de precios de Anthropic](https://platform.claude.com/docs/en/about-claude/pricing), consultada el 20/11/2026. Los precios se guardan en un archivo del proyecto con su fecha; si Anthropic los cambia durante el experimento, queda registrado. Otra web da 0,20 $ para la lectura de caché de Sonnet 5.5; hay que confirmarlo con la factura de la prueba piloto.

### Hipótesis

1. **H1 — Repartir sale más barato:** que Opus planifique y otros modelos programen (A1 y A2) cuesta menos por tarea resuelta que Opus solo (B1), y resuelve como mucho 5 puntos menos de tareas en los niveles fáciles y medios.
2. **H2 — Los ayudantes protegen al jefe:** en Claude Code, cuando un ayudante lee 40 archivos, el orquestador solo recibe su resumen. Así Opus lee menos texto y gasta menos que trabajando solo.
3. **H3 — Empezar de cero tiene un precio:** ese ahorro se pierde, o incluso se invierte, si el orquestador no le dice al ayudante qué archivos mirar y este tiene que buscar otra vez por todo el proyecto.
4. **H4 — La trampa de Haiku:** Haiku es baratísimo hasta 100.000 tokens de entrada, pero por encima cobra 5 veces más. En proyectos grandes, muchas llamadas a Haiku cruzarán ese límite y se comerán parte del ahorro.
5. **H5 — La autonomía cuesta:** con el mismo reparto, dejar que Claude Code decida sale más caro que programarlo a mano, porque Claude Code añade instrucciones propias y a veces delega de más o de menos.

## 3. Diseño experimental

Cada topología se implementa en los dos tracks para obtener comparaciones pareadas sobre las mismas 75 tareas.

### 3.1 Matriz de topologías

| ID | Nombre | Quién dirige | Quién ejecuta | Cómo funciona |
| --- | --- | --- | --- | --- |
| B1 | Referencia cara | Opus (esfuerzo alto) | Nadie más | Opus hace toda la tarea solo. Marca el máximo de calidad esperable. |
| B2 | Referencia media | Sonnet (esfuerzo alto) | Nadie más | Sonnet hace toda la tarea solo. |
| A1 | Planifica y ejecuta | Opus (esfuerzo alto) | Sonnet (esfuerzo bajo/medio) | Opus escribe un plan detallado; Sonnet lo convierte en código leyendo solo los archivos que dice el plan. |
| A2 | Trabajo en paralelo | Opus (esfuerzo alto) | Sonnet para lo importante; Haiku para lo repetitivo | Opus divide la tarea. Sonnet hace la lógica difícil y, a la vez, Haiku hace tests, tipos y código de relleno. |
| A3 | Explorar barato | Haiku busca → Opus planifica | Sonnet edita | Haiku recorre el proyecto y saca solo lo relevante; Opus planifica con ese resumen; Sonnet hace los cambios. |
| A4 | Escalar si falla | Sonnet (esfuerzo medio) | Opus solo si hace falta | Sonnet intenta la tarea. Si los tests fallan, se pasa el error a Opus para que lo arregle. |

En el Track SDK, cada fila es un programa que sigue exactamente esos pasos. En el Track CC, se configuran los mismos ayudantes en Claude Code y es el modelo principal quien decide cuándo llamarlos.

### 3.2 Configuración del Track CC

Cada ayudante de Claude Code se define en un archivo de texto corto (en la carpeta `.claude/agents/`) que dice su nombre, para qué sirve, qué modelo usa, qué herramientas puede usar y cuántos pasos puede dar como máximo. Tres reglas para que la comparación sea justa:

- Se usa la misma versión de Claude Code durante todo el experimento.
- En B1 y B2 se desactiva la posibilidad de llamar a ayudantes, para que de verdad trabajen solos.
- En A3 se fija qué modelo usa el ayudante explorador, en vez de dejar el que Claude Code ponga por defecto.

### 3.3 Dataset

75 tareas de SWE-bench Verified en tres bloques de 25:

- **Nivel 1 (aislado):** bug localizado en 1–2 archivos.
- **Nivel 2 (multiarchivo):** funcionalidad + tests en 3–6 archivos.
- **Nivel 3 (arquitectónico):** refactorizaciones transversales, concurrencia o cambios de interfaz.

El nivel de cada tarea se decide con una regla fija (cuántos archivos y líneas cambia la solución oficial), no a ojo. Todas las ejecuciones parten de las mismas condiciones: un entorno limpio y aislado (contenedor Docker) por tarea, el mismo límite de pasos y los mismos tests ocultos para comprobar si la tarea está resuelta y si se ha roto algo que antes funcionaba.

### 3.4 Telemetría unificada

Para comparar costes de forma justa, los dos tracks apuntan lo que gastan en la misma base de datos y con el mismo formato. Por cada llamada a un modelo se guarda: qué tarea era, qué variante, qué papel tenía el modelo (jefe, ayudante de código, ayudante de tests, explorador…) y cuántos tokens leyó, escribió y reutilizó de la caché.

- **Track SDK:** como el programa es nuestro, cada respuesta de la API ya trae el recuento de tokens y se guarda directamente.
- **Track CC:** Claude Code guarda un registro de todo lo que pasa en la sesión. Un script lo lee y separa qué gastó el modelo principal y qué gastó cada ayudante (cada mensaje indica quién lo generó).
- **Mismo cálculo para los dos:** el coste en dólares lo calculamos nosotros mismos a partir de los tokens y la tabla de precios. La cifra de coste que da Claude Code solo se usa para comprobar que cuadra.

### 3.5 Métricas

| Métrica | Qué mide | Responde a |
| --- | --- | --- |
| Coste medio por tarea (USD) | Cuánto cuesta cada tarea, separado por modelo y por tipo de gasto | RQ1, RQ4 |
| Pass@1 | Qué porcentaje de tareas se resuelve | RQ1, RQ3 |
| Coste por tarea resuelta (USD) | Gasto total dividido entre tareas resueltas. Es la métrica principal: castiga lo barato que falla mucho | RQ1 |
| Impuesto de autonomía | Cuánto más cuesta la misma variante en Claude Code que programada a mano | RQ2 |
| Coste de coordinación | Parte del gasto que se va en dar instrucciones, recibir resúmenes y releer archivos | RQ4 |
| % de llamadas a Haiku por encima de 100K | Cuántas veces Haiku pasa a la tarifa cara | H4 |
| Tiempo total (segundos) | Cuánto tarda cada tarea de principio a fin | RQ5 |

### 3.6 Figuras del paper

1. **Frontera de Pareto dual:** Pass@1 frente a coste por tarea resuelta, las 12 variantes con marcador distinto por track.
2. **Anatomía del gasto:** barras apiladas por planificación, ejecución, lecturas de caché y coordinación.
3. **Curva de ruptura por complejidad:** Pass@1 por nivel 1/2/3 y topología.
4. **Taxonomía de fallos:** plan erróneo de Opus, implementación defectuosa del subagente, conflicto de interfaz entre subagentes paralelos y agotamiento de `maxTurns`.

### 3.7 Análisis estadístico

Como todas las variantes hacen exactamente las mismas tareas, se comparan tarea a tarea, lo que permite detectar diferencias reales con menos datos. Se usarán pruebas estadísticas pensadas para eso (McNemar para "resuelta sí/no" y Wilcoxon para coste y tiempo) y cada resultado irá con un margen de error.

## 4. Plan por fases

El proyecto avanza en siete fases; cada una termina en una puerta con un criterio verificable, y no se gasta en la ejecución masiva hasta que la telemetría cuadra con la facturación real. Las duraciones son orientativas, para una persona a tiempo parcial.

&#91;embedded content: Fases del proyecto · 7 fases con su puerta de salida\]

La Fase 2 es la puerta crítica: sin una atribución de costes que cuadre con la factura, las 900 ejecuciones de la Fase 5 no producen resultados publicables.

### Fase 0 — Definición y preregistro (1 semana)

Congelar preguntas, hipótesis, variantes y umbrales antes de ver ningún resultado.

- [ ] Cerrar la lista de 12 variantes y cuánto esfuerzo usa cada modelo en cada una
- [ ] Decidir cuántas tareas menos que B1 se aceptan como "igual de bueno" (p. ej. 5 puntos)
- [ ] Decidir cuántas veces se repite cada tarea
- [ ] Fijar el presupuesto total y un límite de gasto por ejecución

**Entregable:** este documento + preregistro de hipótesis y análisis. **Puerta:** no quedan decisiones abiertas de la sección 5.

### Fase 1 — Scaffold e infraestructura (2 semanas)

Montar el repositorio `pareto-agents/` con cuatro partes: las tareas y sus entornos, el código del Track SDK, la configuración del Track CC y el registro de gasto (base de datos + tabla de precios).

- [ ] Runner que levanta un contenedor limpio por ejecución, sin red salvo la API de Anthropic
- [ ] Evaluador de tests ocultos de SWE-bench integrado
- [ ] Esquema SQLite y tabla de tarifas versionada

**Entregable:** repositorio ejecutable. **Puerta:** una tarea corre de extremo a extremo en B1-SDK y en B1-CC y deja sus filas en SQLite.

### Fase 2 — Calibración de telemetría (piloto de 5 tareas, 1–2 semanas)

Ejecutar B1-SDK y B1-CC, y después A1-CC, sobre 5 tareas.

- [ ] Script que lee el registro de Claude Code y separa el gasto del modelo principal y de cada ayudante
- [ ] Calcular el coste y compararlo con lo que cobra Anthropic en la consola
- [ ] Confirmar el precio de lectura de caché de Sonnet 5.5
- [ ] Estimar cuánto costará el experimento completo a partir de estas 5 tareas

**Entregable:** informe de calibración + estimación de presupuesto. **Puerta:** el coste recalculado cuadra con la facturación (error < 1%) y el 100% de los mensajes de subagente queda atribuido a un rol.

### Fase 3 — Selección del dataset (en paralelo con la Fase 4)

- [ ] Aplicar el criterio objetivo de nivel sobre los parches de referencia
- [ ] Elegir 25 tareas por nivel, equilibradas por repositorio
- [ ] Documentar las tareas descartadas y el motivo

**Entregable:** `dataset/tasks.json` con 75 tareas y su nivel. **Puerta:** 25/25/25 con criterio reproducible.

### Fase 4 — Implementación de topologías (2–3 semanas)

- [ ] Orquestadores SDK de B2, A1, A2, A3 y A4 con contratos JSON entre roles
- [ ] Perfiles `.claude/agents/*.md` por arquitectura y prompts de tarea comunes
- [ ] Prueba de humo de las 12 variantes sobre las 5 tareas del piloto

**Entregable:** 12 variantes ejecutables. **Puerta:** las 12 completan el piloto con menos de un 5% de fallos de infraestructura.

### Fase 5 — Ejecución masiva controlada (1–2 semanas)

12 variantes × 75 tareas = 900 ejecuciones por ronda. Se lanzan en orden aleatorio, pocas a la vez y con un límite de gasto por ejecución para que ninguna se quede en bucle gastando dinero.

- [ ] Lanzar por lotes y vigilar el gasto acumulado frente a la estimación de la Fase 2
- [ ] Reintentar solo los fallos de infraestructura, nunca los fallos del modelo

**Entregable:** base SQLite completa. **Puerta:** al menos el 98% de las ejecuciones son válidas.

### Fase 6 — Análisis y paper (2–3 semanas)

- [ ] Script pandas + matplotlib que genera las tablas `.tex` y las 4 figuras vectoriales
- [ ] Tests estadísticos pareados e intervalos bootstrap
- [ ] Clasificación de fallos (automática + revisión manual de una muestra)
- [ ] Redacción del paper y publicación del repositorio y los datos

**Entregable:** borrador del paper con figuras y tablas reproducibles desde la base de datos.

## 5. Riesgos y decisiones abiertas

El mayor riesgo es metodológico, no técnico: si la caché, la variabilidad o el dataset no se controlan, las diferencias entre variantes no serán interpretables.

### Riesgos

| Riesgo | Qué pasaría | Cómo evitarlo |
| --- | --- | --- |
| La caché de Anthropic no se puede borrar a voluntad | Una tarea podría salir más barata porque otra anterior dejó texto en caché | Ejecutar en orden aleatorio, dejar pasar tiempo entre tareas parecidas y marcar las ejecuciones que empiecen ya con caché |
| SWE-bench tiene pocas tareas realmente grandes (Nivel 3) | El bloque difícil quedaría flojo | Revisarlo al elegir tareas; si faltan, completar con otra fuente y decirlo en el paper |
| Los modelos no responden igual dos veces | Una diferencia pequeña podría ser casualidad | Repetir parte de las tareas y dar márgenes de error |
| Los modelos podrían haber visto estas tareas al entrenarse | Todas las variantes resolverían más de lo normal | Afecta a todas por igual; se menciona como limitación |
| Cambia la versión de Claude Code o los precios a mitad | Resultados no comparables | Fijar la versión y guardar los precios con fecha |
| En Claude Code quizá no se pueda fijar el esfuerzo de cada ayudante | Los dos tracks no estarían en igualdad | Comprobarlo en la Fase 2 y explicarlo si no se puede |
| Claude Code se ejecuta sin pedir permisos | Podría tocar cosas fuera del experimento | Ejecutarlo solo dentro de un entorno aislado sin acceso a internet salvo a Anthropic |
| El experimento cuesta más de lo previsto | Habría que pararlo a medias | Estimar el coste con la prueba piloto y poner límites de gasto |

### Decisiones abiertas

- [ ] La propuesta original habla de 10 variantes, pero 6 topologías × 2 tracks son 12. Decidir si se mantienen las 12 o se quita una topología.
- [ ] Umbral de Pass@1 que se considera "equivalente" a B1.
- [ ] Número de repeticiones y si se aplican a todas las tareas o a un subconjunto.
- [ ] Presupuesto total máximo de la campaña.
- [ ] Revista, congreso o formato de publicación objetivo.

### Fuentes

- [Precios de la API de Claude — Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)
