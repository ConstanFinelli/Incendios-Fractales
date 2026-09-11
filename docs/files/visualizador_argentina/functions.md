# Funciones de `visualizador_argentina.py`

## 1. Funciones Definidas en este Archivo

### `cargar_geometria_argentina()`
- **Firma:** `def cargar_geometria_argentina():`
- **Descripción:** Obtiene y procesa la capa vectorial de las 24 provincias de la República Argentina. Si el GeoJSON local `data/provincias_argentina.json` ya existe, lo carga directamente. Si no existe, descarga el GeoJSON oficial de departamentos de Argentina, los disuelve por provincia con GeoPandas, aplica una simplificación topológica con tolerancia de $0.01^\circ$ para optimizar el rendimiento y almacena la capa simplificada en caché local.
- **Parámetros:** Ninguno.
- **Retorno:** `geopandas.GeoDataFrame` con las 24 geometrías provinciales de Argentina, o `None` en caso de error.

---

### `_crear_data_uri_rgba_argentina(matriz, color_rgb=(231, 76, 60), alfa=220)`
- **Firma:** `def _crear_data_uri_rgba_argentina(matriz, color_rgb=(231, 76, 60), alfa=220):`
- **Descripción:** Convierte una matriz binaria de propagación ($256 \times 256$) en una imagen RGBA en memoria codificada como Data URI en base64 compatible con Folium. Aplica la máscara provincial de Corrientes para evitar desbordamientos sobre los ríos limítrofes y voltea verticalmente la matriz (`np.flipud`) para adaptar el sistema de coordenadas cartesianas al sistema geográfico WGS84 de Folium.
- **Parámetros:**
  - `matriz` (`numpy.ndarray` 2D): Matriz binaria a convertir.
  - `color_rgb` (tuple, opcional): Tupla RGB (0-255).
  - `alfa` (int, opcional): Transparencia del canal alfa. Por defecto `220`.
- **Retorno:** `str` conteniendo `'data:image/png;base64,...'`.

---

### `generar_mapa_estatico_argentina(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, ruta_salida="output/mapa_argentina_prediccion.png", matriz_final=None)`
- **Firma:** `def generar_mapa_estatico_argentina(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Genera un mapa GIS de alta definición (300 DPI) estructurado en 4 paneles horizontales que representan todo el territorio continental de la República Argentina:
  - **Panel 1:** Foco Base Observado en la República Argentina (`fecha_final`).
  - **Panel 2:** Predicción a +24 Horas (Nivel Táctico).
  - **Panel 3:** Predicción a +48 Horas (Nivel Preventivo).
  - **Panel 4:** Predicción a +72 Horas y Riesgo Isócrono (Nivel Estratégico).
  Superpone la división interprovincial argentina y destaca la silueta y ubicación geográfica de la Provincia de Corrientes.
- **Parámetros:** Matrices de entrada, horizonte de predicción, variables climáticas y ruta de salida.
- **Retorno:** `str` con la ruta del archivo PNG exportado.

---

### `generar_mapa_interactivo_argentina(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, ruta_salida="output/mapa_argentina_interactivo.html", matriz_final=None)`
- **Firma:** `def generar_mapa_interactivo_argentina(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Construye una aplicación web interactiva en Folium a escala nacional con:
  - Centrado geográfico nacional (Lat $-38.4^\circ$, Lon $-63.6^\circ$).
  - 3 capas base (CartoDB Positron, OpenStreetMap, Esri Satélite).
  - Capa vectorial GeoJSON de las 24 provincias de Argentina con tooltips informativos y contorno reforzado para Corrientes.
  - Capas raster individuales conmutables para la base observada, +24h, +48h y +72h.
  - Selector de capas y leyenda flotante informativa.
- **Parámetros:** Matrices de simulación, fechas del análisis y ruta de archivo HTML.
- **Retorno:** `str` con la ruta del archivo HTML guardado.

---

### `generar_mapas_argentina(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, matriz_final=None)`
- **Firma:** `def generar_mapas_argentina(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Función orquestadora a escala nacional. Imprime los límites geográficos en consola y coordina la ejecución de `generar_mapa_estatico_argentina` y `generar_mapa_interactivo_argentina`.
- **Parámetros:** Mismos argumentos que las funciones de renderizado.
- **Retorno:** `dict` con las rutas de los archivos generados:
  ```python
  {
      'mapa_estatico_argentina': str,
      'mapa_interactivo_argentina': str
  }
  ```

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

### Provenientes de `visualizador_corrientes.py`:
- **`cargar_mascara_provincia`** *(Importada dentro de `_crear_data_uri_rgba_argentina`)*:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/visualizador_corrientes/functions.md`](../visualizador_corrientes/functions.md).
  - *Rol en `visualizador_argentina.py`:* Proporciona la máscara binaria provincial para recortar los frentes rasterizados en el mapa nacional, asegurando que no desborden sobre provincias limítrofes o cauces fluviales antes de codificarlos en Data URI.

