# Funciones de `simulador_predictivo.py`

## 1. Funciones Definidas en este Archivo

<a id="ejecutar_prediccion"></a>

### `ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA)`

- **Firma:** `def ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA):`
- **Descripción:** Función principal y orquestadora de la Fase 3:
  1. Desempaqueta las variables óptimas `(viento_vel, viento_dir, humedad, combustible)`.
  2. Determina el formato de `datos_entrada`. Identifica la última fecha observada (`fecha_final`) y carga los focos activos instantáneos del último día observado mediante `cargar_datos_serie_temporal(...)`.
  3. Ejecuta la simulación temporal continua en 3 etapas sucesivas de $30$ ciclos cada una mediante `simular_evolucion_multietapa`, obteniendo las matrices binarias de $+24\text{h}$, $+48\text{h}$ y $+72\text{h}$.
  4. Calcula el recuento de celdas de avance neto para cada horizonte temporal.
  5. Construye la matriz de riesgo isócrono (`mapa_riesgo`) asignando los valores discretos $0$ (intacta), $1$ (base), $2$ (+24h), $3$ (+48h) y $4$ (+72h).
  6. Genera y guarda la figura comparativa multipanel `output/mapa_riesgo_predictivo.png` con 4 paneles horizontales.
  7. Invoca con manejo robusto de excepciones a `generar_mapas_corrientes` de `visualizador_corrientes.py` y genera el mapa de susceptibilidad biofísica mediante `generar_mapa_cobertura_grafico` de `capa_biomasa.py`.
- **Parámetros:**
  - `datos_entrada` (list, np.ndarray o str): Serie temporal o matriz directa.
  - `mejores_variables` (tuple o list): `(viento_vel, viento_dir, humedad, combustible)`.
  - `pasos_por_dia` (int, opcional): Pasos del autómata celular equivalentes a 1 día ($30$).
- **Retorno:** `numpy.ndarray` 2D con la matriz de riesgo isócrono final calculada.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

### Provenientes de `algoritmo_genetico.py`:

- **`cargar_datos_serie_temporal`**:
  - _Ubicación de la definición:_ [`docs/files/algoritmo_genetico/functions.md`](../algoritmo_genetico/functions.md).
  - _Rol en `simulador_predictivo.py`:_ Carga estructurada de la serie temporal y extracción del frente activo de partida.

### Provenientes de `automata_celular.py`:

- **`simular_evolucion_multietapa`**:
  - _Ubicación de la definición:_ [`docs/files/automata_celular/functions.md`](../automata_celular/functions.md).
  - _Rol en `simulador_predictivo.py`:_ Ejecuta la propagación secuencial y continua del autómata celular en 3 etapas sucesivas (de 30 pasos cada una) partiendo de la matriz base del último día.

### Provenientes de `capa_biomasa.py`:

- **`obtener_mapa_combustible`** y **`generar_mapa_cobertura_grafico`**:
  - _Ubicación de la definición:_ [`docs/files/capa_biomasa/functions.md`](../capa_biomasa/functions.md).
  - _Rol en `simulador_predictivo.py`:_ Suministra la matriz raster de combustible real de Corrientes y exporta la cartografía biofísica.

### Provenientes de `visualizador_corrientes.py`:

- **`generar_mapas_corrientes`**:
  - _Ubicación de la definición:_ [`docs/files/visualizador_corrientes/functions.md`](../visualizador_corrientes/functions.md).
  - _Rol en `simulador_predictivo.py`:_ Proyecta la predicción sobre el polígono y los 25 departamentos de la Provincia de Corrientes, generando tanto el mapa estático PNG en 4 paneles como el mapa web interactivo en Folium y el informe de impacto departamental.
