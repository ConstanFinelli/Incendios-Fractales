# Funciones de `visualizador_corrientes.py`

## 1. Funciones Definidas en este Archivo

<a id="cargar_geometria_corrientes"></a>
### `cargar_geometria_corrientes()`
- **Firma:** `def cargar_geometria_corrientes():`
- **Descripción:** Carga el `geopandas.GeoDataFrame` con los límites vectoriales de los 25 departamentos de la Provincia de Corrientes. Si el archivo local `data/departamentos_corrientes.json` no existe, lo descarga automáticamente desde el repositorio cartográfico oficial de Argentina y lo persiste localmente en disco.
- **Parámetros:** Ninguno.
- **Retorno:** `geopandas.GeoDataFrame` con geometrías poligonales departamentales, o `None` en caso de error de conexión.

---

<a id="cargar_mascara_provincia"></a>
### `cargar_mascara_provincia(tamano=256)`
- **Firma:** `def cargar_mascara_provincia(tamano=256):`
- **Descripción:** Obtiene o calcula una máscara binaria 2D (`numpy.ndarray` de booleanos) que indica con precisión qué celdas de la grilla caen dentro del contorno geográfico de Corrientes. Si el archivo precalculado `data/mascara_corrientes_256.npy` existe en disco, lo lee de inmediato. En caso contrario, realiza una operación espacial de unión (`unary_union`) sobre los departamentos, construye una malla regular con `meshgrid` y evalúa el predicado espacial `.within(corrientes_geom)`, guardando el resultado en disco para acelerar ejecuciones posteriores.
- **Parámetros:**
  - `tamano` (int, opcional): Dimensión cuadrada de la matriz. Por defecto `256`.
- **Retorno:** `numpy.ndarray` 2D booleano de $256 \times 256$.

---

<a id="matriz_a_coordenadas"></a>
### `matriz_a_coordenadas(row, col, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX)`
- **Firma:** `def matriz_a_coordenadas(row, col, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX):`
- **Descripción:** Realiza la interpolación lineal para convertir índices de fila y columna de la matriz discreta a coordenadas geográficas continuas en grados decimales (latitud sur y longitud oeste).
- **Parámetros:**
  - `row`, `col` (int o float): Índices de celda.
  - `tamano` (int, opcional): Dimensión de la grilla ($256$).
  - `lat_min`, `lat_max`, `lon_min`, `lon_max` (float, opcional): Bounding box geográfico.
- **Retorno:** Tupla `(lat, lon)`.

---

<a id="identificar_departamentos_afectados"></a>
### `identificar_departamentos_afectados(matriz_fuego, gdf_corrientes=None, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX)`
- **Firma:** `def identificar_departamentos_afectados(matriz_fuego, gdf_corrientes=None, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX):`
- **Descripción:** Cruza espacialmente las celdas encendidas de una matriz de fuego binaria contra la capa poligonal de departamentos de Corrientes mediante un `sjoin` (spatial join) vectorial de puntos. Contabiliza cuántas celdas de fuego caen en cada departamento y calcula el porcentaje de participación sobre el total del frente.
- **Parámetros:**
  - `matriz_fuego` (`numpy.ndarray` 2D): Matriz binaria a evaluar (típicamente el avance incremental de un horizonte temporal).
  - `gdf_corrientes` (GeoDataFrame, opcional): Geometrías departamentales. Si es `None`, invoca `cargar_geometria_corrientes()`.
  - `tamano`, límites de latitud/longitud: Configuración espacial.
- **Retorno:** `list` de diccionarios ordenada descendentemente por cantidad de celdas afectadas:
  ```python
  [{'departamento': 'Concepción', 'celdas': 45, 'porcentaje': 28.5}, ...]
  ```

---

<a id="_crear_data_uri_rgba"></a>
### `_crear_data_uri_rgba(matriz, color_rgb=(231, 76, 60), alfa=220, aplicar_mascara_provincia=True)`
- **Firma:** `def _crear_data_uri_rgba(matriz, color_rgb=(231, 76, 60), alfa=220, aplicar_mascara_provincia=True):`
- **Descripción:** Transforma una matriz binaria en una imagen RGBA codificada en base64 Data URI lista para incrustarse en capas `ImageOverlay` de Folium. Invierte verticalmente el arreglo (`np.flipud`) para compensar la convención de visualización cartográfica norte-arriba de los mapas web y aplica opcionalmente la máscara provincial.
- **Parámetros:**
  - `matriz` (`numpy.ndarray` 2D): Matriz binaria de fuego.
  - `color_rgb` (tuple, opcional): Color de la capa en formato RGB (0-255).
  - `alfa` (int, opcional): Nivel de opacidad (0-255). Por defecto `220`.
  - `aplicar_mascara_provincia` (bool, opcional): Si es `True`, anula los píxeles fuera de Corrientes.
- **Retorno:** `str` conteniendo la cadena `'data:image/png;base64,...'`.

---

<a id="generar_mapa_estatico_corrientes"></a>
### `generar_mapa_estatico_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, ruta_salida="output/mapa_corrientes_prediccion.png", matriz_final=None)`
- **Firma:** `def generar_mapa_estatico_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Genera el mapa cartográfico oficial de la provincia en una figura multipanel de 4 ejes horizontales en alta resolución (300 DPI):
  - **Panel 1:** Foco Base Observado en Corrientes (`fecha_final`).
  - **Panel 2:** Predicción a +24 Horas (Avance Táctico).
  - **Panel 3:** Predicción a +48 Horas (Avance Preventivo).
  - **Panel 4:** Predicción a +72 Horas y Riesgo Isócrono (Avance Estratégico).
  Superpone límites departamentales discontinuos, polígono provincial exterior y etiquetas con halo blanco legible (`pe.withStroke`).
- **Parámetros:** Matrices de simulación, fechas del intervalo, variables climáticas y ruta de salida.
- **Retorno:** `str` con la ruta de la imagen generada.

---

<a id="generar_mapa_interactivo_corrientes"></a>
### `generar_mapa_interactivo_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, ruta_salida="output/mapa_corrientes_interactivo.html", matriz_final=None)`
- **Firma:** `def generar_mapa_interactivo_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Construye una aplicación web interactiva en Folium que incluye:
  - 3 capas base (CartoDB Positron, OpenStreetMap, Esri Satélite).
  - Capas raster individuales georreferenciadas (Data URI) para el Foco Base, +24h, +48h, +72h y Avance Total Acumulado.
  - Capa vectorial con los 25 departamentos de Corrientes con tooltips interactivos (nombre y cabecera).
  - MiniMap de navegación y leyenda flotante con las variables climáticas inferidas.
- **Parámetros:** Matrices de entrada, metadatos temporales y ruta de salida HTML.
- **Retorno:** `str` con la ruta del archivo HTML interactivo generado.

---

<a id="generar_mapas_corrientes"></a>
### `generar_mapas_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, fecha_inicial="T0", fecha_final="T_final", mejores_variables=None, pasos_futuros=90, matriz_final=None)`
- **Firma:** `def generar_mapas_corrientes(matriz_inicial, matriz_futura, mapa_riesgo, ...):`
- **Descripción:** Función orquestadora del módulo provincial. Desglosa los avances de fuego por horizonte (+24h, +48h, +72h), ejecuta el análisis territorial departamental (`identificar_departamentos_afectados`), imprime los reportes de ranking en consola y coordina la generación de los mapas estático y web interactivo.
- **Parámetros:** Mismos argumentos que las funciones de renderizado.
- **Retorno:** `dict` estructurado:
  ```python
  {
      'mapa_estatico': str,
      'mapa_interactivo': str,
      'departamentos_afectados': {
          '24h': list,
          '48h': list,
          '72h': list
      }
  }
  ```

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

*Este archivo no importa funciones de otros módulos del proyecto.* Actúa como productor de cartografía provincial y proveedor de la función utilitaria `cargar_mascara_provincia` para otros módulos.

