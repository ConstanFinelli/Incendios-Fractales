# Funciones de `algoritmo_genetico.py`

## 1. Funciones Definidas en este Archivo

<a id="cargar_datos_serie_temporal"></a>
### `cargar_datos_serie_temporal(entradas)`
- **Firma:** `def cargar_datos_serie_temporal(entradas):`
- **Descripción:** Carga desde el disco una o varias matrices satelitales (`.npy`) generadas en la Fase 1. En el caso de una serie multitemporal, va consolidando la cicatriz histórica acumulada mediante una unión lógica y computa previamente la Dimensión Fractal real ($D_{\text{real}}$) de cada día evaluando directamente el frente activo mediante `calcular_dimension_fractal_directa` (T1.5), sin necesidad de erosión forzada.
- **Parámetros:**
  - `entradas` (str o list): Ruta de un único archivo `.npy` o lista de tuplas `[(fecha, ruta), ...]`.
- **Retorno:** `list` de diccionarios con la estructura:
  ```python
  [{
      'fecha': str,
      'ruta': str,
      'matriz': np.ndarray,
      'dimension_fractal': float
  }, ...]
  ```

---

<a id="generar_individuo"></a>
### `generar_individuo()`
- **Firma:** `def generar_individuo():`
- **Descripción:** Instancia un cromosoma aleatorio dentro de los rangos biofísicos admisibles para el incendio:
  - Viento: $[0, 50] \text{ km/h}$.
  - Dirección: $[0, 360^\circ]$.
  - Humedad: $[10\%, 80\%]$.
  - Combustible: $[0.1, 1.0]$.
- **Parámetros:** Ninguno.
- **Retorno:** `list` de 4 elementos float `[viento_vel, viento_dir, humedad, combustible]`.

---

<a id="evaluar_fitness_multitemporal"></a>
### `evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, num_simulaciones=NUM_SIMULACIONES, mapa_combustible=None)`
- **Firma:** `def evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, num_simulaciones=NUM_SIMULACIONES, mapa_combustible=None):`
- **Descripción:** Evalúa la calidad de un individuo en $num\_simulaciones$ réplicas Monte Carlo bajo el principio físico de expansión desde celdas iniciales, integrando la heterogeneidad espacial biofísica (T2.1):
  - **Punto de Partida Físico ($T_0$):** El autómata celular se inicializa siempre con **todas las celdas activas correspondientes a los puntos de calor del día de inicio**, sin forzar su colapso a un baricentro único.
  - **Evolución Multitemporal hacia los demás días:** Para cada transición temporal ($T_{k-1} \to T_k$), avanza la grilla continua `pasos_por_dia` pasos (30 ciclos) usando `_avanzar_pasos_AC` modulado por el mapa de combustible raster, expandiéndose hacia las demás zonas y midiendo la concordancia híbrida (50% Dimensión Fractal directa $D$ + 50% Cobertura Eficiente Espacial $F_1$-Dice) contra la foto satelital real del día $T_k$. Promedia las aptitudes de todas las etapas.
  - **Caso de 1 solo día:** Si se suministra una sola fecha, la simulación arranca igualmente desde todas las celdas de calor reales observadas en dicha fecha y avanza `pasos_por_dia` pasos, contrastando la preservación fractal y cobertura eficiente $F_1$-Dice.
- **Parámetros:**
  - `individuo` (list): Vector de 4 genes `[viento_vel, viento_dir, humedad, combustible]`.
  - `datos_serie` (list): Lista devuelta por `cargar_datos_serie_temporal`.
  - `pasos_por_dia` (int, opcional): Ciclos por día (30).
  - `num_simulaciones` (int, opcional): Réplicas Monte Carlo (5).
  - `mapa_combustible` (np.ndarray, opcional): Matriz 2D $[0.0, 1.0]$ con la susceptibilidad de combustible de Corrientes (IGN WFS).
- **Retorno:** `float` con el fitness promedio del individuo en el rango $[0.0, 1.0]$.

---

<a id="_evaluar_individuo_worker"></a>
### `_evaluar_individuo_worker(args)`
- **Firma:** `def _evaluar_individuo_worker(args):`
- **Descripción:** Función auxiliar de nivel superior (top-level) diseñada para ser serializable con `pickle` bajo Windows al utilizar `ProcessPoolExecutor`. Desempaqueta la tupla de argumentos y llama a `evaluar_fitness_multitemporal`.
- **Parámetros:**
  - `args` (tuple): Tupla de 4 o 5 elementos `(individuo, datos_serie, pasos_por_dia, num_simulaciones[, mapa_combustible])`.
- **Retorno:** Tupla `(individuo, fit)`.

---

<a id="cruzar"></a>
### `cruzar(padre1, padre2)`
- **Firma:** `def cruzar(padre1, padre2):`
- **Descripción:** Aplica el operador de recombinación o cruce en un punto aleatorio (`1-point crossover`) sobre los vectores cromosómicos de los progenitores.
- **Parámetros:**
  - `padre1`, `padre2` (list): Cromosomas de los progenitores.
- **Retorno:** Tupla `(hijo1, hijo2)` con los dos nuevos individuos descendientes.

---

<a id="mutar"></a>
### `mutar(individuo)`
- **Firma:** `def mutar(individuo):`
- **Descripción:** Con probabilidad `PROB_MUTACION` ($0.1$), selecciona aleatoriamente uno de los 4 genes del cromosoma y le asigna un nuevo valor continuo dentro de su rango físico permitido.
- **Parámetros:**
  - `individuo` (list): Cromosoma a mutar.
- **Retorno:** `list` con el individuo (mutado o inalterado).

---

<a id="seleccion_torneo"></a>
### `seleccion_torneo(fitness_poblacion, k=3)`
- **Firma:** `def seleccion_torneo(fitness_poblacion, k=3):`
- **Descripción:** Selecciona aleatoriamente una muestra de $k$ individuos de la población y retorna el cromosoma que ostenta el mayor valor de fitness.
- **Parámetros:**
  - `fitness_poblacion` (list): Lista de tuplas `(individuo, fitness)`.
  - `k` (int, opcional): Tamaño del torneo. Por defecto `3`.
- **Retorno:** `list` con el cromosoma ganador del torneo.

---

<a id="guardar_grafico_fitness"></a>
### `guardar_grafico_fitness(historial, ruta_salida='output/curva_fitness.png')`
- **Firma:** `def guardar_grafico_fitness(historial, ruta_salida='output/curva_fitness.png'):`
- **Descripción:** Genera un gráfico de líneas a 300 DPI que ilustra la curva de aprendizaje evolutivo a lo largo de las generaciones. Representa el récord global acumulado del mejor fitness (monótonamente no decreciente $\nearrow$ propio del elitismo) junto con el mejor fitness puntual medido en cada generación y el fitness promedio de la población.
- **Parámetros:**
  - `historial` (list): Lista de diccionarios de telemetría generacionales.
  - `ruta_salida` (str, opcional): Ruta del archivo PNG a exportar.
- **Retorno:** `None`.

---

<a id="guardar_csv_resultados"></a>
### `guardar_csv_resultados(historial, mejor_individuo, mejor_fitness)`
- **Firma:** `def guardar_csv_resultados(historial, mejor_individuo, mejor_fitness):`
- **Descripción:** Exporta dos archivos CSV estructurados:
  1. `output/historial_fitness.csv`: Detalle por generación del récord global acumulado (`Mejor_Fitness_Global`), el fitness de la generación (`Mejor_Fitness_Gen`), el promedio y los genes climáticos correspondientes al récord global.
  2. `output/resultados_optimizacion.csv`: Reporte final con los parámetros climáticos inferidos, el fitness alcanzado y las ponderaciones utilizadas (`Peso_Fractal_Utilizado`, `Peso_Espacial_F1_Utilizado` y `Peso_IoU_Utilizado`).
- **Parámetros:**
  - `historial` (list): Historial evolutivo completo.
  - `mejor_individuo` (list): Cromosoma del mejor espécimen global.
  - `mejor_fitness` (float): Puntaje de fitness del mejor espécimen.
- **Retorno:** `None`.

---

<a id="ejecutar_algoritmo_genetico"></a>
### `ejecutar_algoritmo_genetico(entradas_matrices)`
- **Firma:** `def ejecutar_algoritmo_genetico(entradas_matrices):`
- **Descripción:** Función orquestadora de la Fase 2. Inicializa el pool de procesos con `ProcessPoolExecutor` aprovechando todos los núcleos CPU disponibles ($N-1$), inicializa la población aleatoria de 32 individuos y ejecuta el bucle de $40$ generaciones. En cada generación evalúa en paralelo con 5 corridas Monte Carlo por individuo, aplica elitismo (top 4), realiza selección por torneo, cruce y mutación. Al concluir, exporta los reportes CSV y gráficos, retornando el mejor vector climático hallado.
- **Parámetros:**
  - `entradas_matrices`: Matriz única o serie multitemporal.
- **Retorno:** `list` con las 4 variables óptimas `[viento_vel, viento_dir, humedad, combustible]`, o `None` en caso de fallo.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

### Provenientes de `automata_celular.py`:
- **`simular_incendio_AC`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/automata_celular/functions.md`](../automata_celular/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Se invoca en la evaluación estática de un solo día para simular el incendio desde un centroide.
- **`_avanzar_pasos_AC`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/automata_celular/functions.md`](../automata_celular/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Se utiliza en la evaluación multitemporal para avanzar la grilla día a día (30 pasos por etapa diaria).

### Provenientes de `calcular_dimension_fractal.py`:
- **`extraer_perimetro`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/calcular_dimension_fractal/functions.md`](../calcular_dimension_fractal/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Extrae el contorno exterior tanto de la cicatriz satelital real como de la simulación del autómata celular.
- **`calcular_box_counting`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/calcular_dimension_fractal/functions.md`](../calcular_dimension_fractal/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Computa la dimensión fractal $D$ para comparar el grado de ramificación entre la realidad y la simulación.
- **`calcular_dimension_fractal_directa`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/calcular_dimension_fractal/functions.md`](../calcular_dimension_fractal/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Evalúa directamente la dimensión fractal $D$ sobre el frente activo multicluster sin necesidad de erosión morfológica intermedia (T1.5).

### Provenientes de `ver_mapa_filtrado.py`:
- **`procesar_rango_fechas`** *(Importado condicionalmente en `if __name__ == '__main__':`)*:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/ver_mapa_filtrado/functions.md`](../ver_mapa_filtrado/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Permite correr el algoritmo genético como un script independiente por línea de comandos pasando dos fechas como argumentos.

### Provenientes de `capa_biomasa.py`:
- **`obtener_mapa_combustible`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/capa_biomasa/functions.md`](../capa_biomasa/functions.md).
  - *Rol en `algoritmo_genetico.py`:* Carga o sintetiza la matriz 2D de susceptibilidad biofísica de Corrientes (IGN WFS) para inyectar heterogeneidad espacial en la evaluación paralela del autómata celular durante la optimización genética (T2.1).

