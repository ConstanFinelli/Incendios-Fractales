# Funciones de `simulador_predictivo.py`

## 1. Funciones Definidas en este Archivo

### `ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA)`
- **Firma:** `def ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA):`
- **Descripción:** Función principal y orquestadora de la Fase 3:
  1. Desempaqueta las variables óptimas `(viento_vel, viento_dir, humedad, combustible)`.
  2. Determina el formato de `datos_entrada`. Identifica la última fecha observada (`fecha_final`) y carga el frente de fuego activo de ese día (`matriz_final = np.load(ruta_final)`).
  3. Ejecuta la simulación temporal continua en 3 etapas sucesivas de $30$ ciclos cada una mediante `simular_evolucion_multietapa`, obteniendo las matrices binarias de $+24\text{h}$, $+48\text{h}$ y $+72\text{h}$.
  4. Calcula el recuento de celdas de avance neto para cada horizonte temporal.
  5. Construye la matriz de riesgo isócrono (`mapa_riesgo`) asignando los valores discretos $0$ (intacta), $1$ (base), $2$ (+24h), $3$ (+48h) y $4$ (+72h).
  6. Genera y guarda la figura comparativa multipanel `output/mapa_riesgo_predictivo.png` con 4 paneles horizontales.
  7. Invoca con manejo robusto de excepciones a `generar_mapas_corrientes` de `visualizador_corrientes.py`.
  8. Invoca con manejo robusto de excepciones a `generar_mapas_argentina` de `visualizador_argentina.py`.
- **Parámetros:**
  - `datos_entrada` (list, np.ndarray o str): Serie temporal o matriz directa.
  - `mejores_variables` (tuple o list): `(viento_vel, viento_dir, humedad, combustible)`.
  - `pasos_por_dia` (int, opcional): Pasos del autómata celular equivalentes a 1 día ($30$).
- **Retorno:** `numpy.ndarray` 2D con la matriz de riesgo isócrono final calculada.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

### Provenientes de `automata_celular.py`:
- **`simular_evolucion_multietapa`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/automata_celular/functions.md`](../automata_celular/functions.md).
  - *Rol en `simulador_predictivo.py`:* Ejecuta la propagación secuencial y continua del autómata celular en 3 etapas sucesivas (de 30 pasos cada una) partiendo de la matriz base del último día.

### Provenientes de `visualizador_corrientes.py`:
- **`generar_mapas_corrientes`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/visualizador_corrientes/functions.md`](../visualizador_corrientes/functions.md).
  - *Rol en `simulador_predictivo.py`:* Proyecta la predicción sobre el polígono y los 25 departamentos de la Provincia de Corrientes, generando tanto el mapa estático PNG en 4 paneles como el mapa web interactivo en Folium y el informe de impacto departamental.

### Provenientes de `visualizador_argentina.py`:
- **`generar_mapas_argentina`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/visualizador_argentina/functions.md`](../visualizador_argentina/functions.md).
  - *Rol en `simulador_predictivo.py`:* Proyecta la evolución del siniestro a escala nacional sobre el mapa completo de la República Argentina, generando el mapa estático PNG de 4 paneles y el mapa interactivo web de Folium.

