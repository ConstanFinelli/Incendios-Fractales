# Funciones de `validacion_walk_forward.py`

## 1. Funciones Definidas en este Archivo

### `ejecutar_validacion_walk_forward(fechas_calibracion=['2022-02-16', '2022-02-17'], fechas_prueba=['2022-02-18', '2022-02-19', '2022-02-20'], pasos_por_dia=30, mejores_variables=None)`

- **Firma:** `def ejecutar_validacion_walk_forward(fechas_calibracion=['2022-02-16', '2022-02-17'], fechas_prueba=['2022-02-18', '2022-02-19', '2022-02-20'], pasos_por_dia=PASOS_POR_DIA, mejores_variables=None):`
- **Descripción:** Orquesta y ejecuta el experimento científico de validación fuera de muestra (_Walk-Forward_) a 3 horizontes prospectivos (+24h, +48h y +72h):
  1. Preprocesa y rasteriza la serie completa de observaciones de la NASA en grillas de $256 \times 256$ en modo instantáneo puro.
  2. Ejecuta la optimización inversa mediante el Algoritmo Genético sobre la ventana de calibración (o recibe `mejores_variables` ya calculadas).
  3. Proyecta de manera continua la propagación en el Autómata Celular durante $30$ pasos por día para los horizontes $+24\text{h}$, $+48\text{h}$ y $+72\text{h}$ desde el frente activo base.
  4. Calcula la matriz de confusión espacial píxel a píxel contra las observaciones reales instantáneas de la NASA (Verdaderos Positivos VP, Falsos Positivos FP, Falsos Negativos FN) con máscara provincial.
  5. Computa las métricas formales: $F_1$-Dice ciego, IoU ciego (Jaccard), Cobertura ($\text{Recall}$), Pureza ($\text{Precision}$) y Error Fractal $\Delta D = |D_{\text{real}} - D_{\text{sim}}|$.
  6. Genera el gráfico diagnóstico multipanel de 9 cuadrantes (`output/walk_forward_comparativa_3dias.png`), la curva de progresión temporal (`output/walk_forward_metricas_progression.png`) y el archivo CSV tabular (`output/reporte_walk_forward_3dias.csv`).
- **Parámetros:**
  - `fechas_calibracion` (_list[str]_, opcional): Lista de fechas para entrenamiento/calibración (por defecto `['2022-02-16', '2022-02-17']`).
  - `fechas_prueba` (_list[str]_, opcional): Lista de fechas objetivo para evaluación ciega (por defecto `['2022-02-18', '2022-02-19', '2022-02-20']`).
  - `pasos_por_dia` (_int_, opcional): Pasos de simulación en el AC por cada período de 24 horas (30 pasos).
  - `mejores_variables` (_tuple_, opcional): Tupla `(viento_vel, viento_dir, humedad, combustible)` previamente calibrada.
- **Retorno:** `list[dict]` donde cada elemento contiene el resumen de métricas, matrices de confusión y capas raster de un horizonte evaluado.

---

## 2. Funciones Invocadas desde Otros Módulos

| Función Invocada                     | Módulo de Origen                | Archivo de Documentación                                                                       | Motivo de la Invocación                                                                                                        |
| :----------------------------------- | :------------------------------ | :--------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| `procesar_rango_fechas`              | `ver_mapa_filtrado.py`          | [`ver_mapa_filtrado.md`](../ver_mapa_filtrado/ver_mapa_filtrado.md)                            | Extracción y rasterización espacial $256 \times 256$ de las fechas satelitales NASA con filtrado automático de días sin focos. |
| `ejecutar_algoritmo_genetico`        | `algoritmo_genetico.py`         | [`algoritmo_genetico.md`](../algoritmo_genetico/algoritmo_genetico.md)                         | Inferencia inversa de parámetros microclimáticos óptimos sobre la ventana de entrenamiento.                                    |
| `cargar_datos_serie_temporal`        | `algoritmo_genetico.py`         | [`algoritmo_genetico.md`](../algoritmo_genetico/algoritmo_genetico.md)                         | Carga estructurada de matrices satelitales de frentes activos instantáneos.                                                    |
| `_avanzar_pasos_AC`                  | `automata_celular.py`           | [`automata_celular.md`](../automata_celular/automata_celular.md)                               | Motor de simulación para avanzar la grilla del autómata celular $N$ pasos hacia los horizontes futuros.                        |
| `calcular_dimension_fractal_directa` | `calcular_dimension_fractal.py` | [`calcular_dimension_fractal.md`](../calcular_dimension_fractal/calcular_dimension_fractal.md) | Cuantificación de la dimensión fractal directa ($D$) de las manchas satelitales reales y simuladas.                            |
| `obtener_mapa_combustible`           | `capa_biomasa.py`               | [`capa_biomasa.md`](../capa_biomasa/capa_biomasa.md)                                           | Carga de la matriz de susceptibilidad y heterogeneidad biofísica del terreno de Corrientes (IGN).                              |
| `cargar_geometria_corrientes`        | `visualizador_corrientes.py`    | [`visualizador_corrientes.md`](../visualizador_corrientes/visualizador_corrientes.md)          | Carga vectorial de geometrías departamentales de Corrientes para el renderizado cartográfico.                                  |
| `cargar_mascara_provincia`           | `visualizador_corrientes.py`    | [`visualizador_corrientes.md`](../visualizador_corrientes/visualizador_corrientes.md)          | Máscara raster poligonal para recortar con exactitud el contorno de la provincia de Corrientes.                                |
