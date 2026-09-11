# Funciones de `ver_mapa_filtrado.py`

## 1. Funciones Definidas en este Archivo

<a id="obtener_df_completo"></a>
### `obtener_df_completo()`
- **Firma:** `def obtener_df_completo():`
- **Descripción:** Implementa un patrón de carga diferida (*lazy loading*) con caché en memoria mediante la variable global `_df_completo_cache`. Lee la base de datos completa de la NASA desde `./DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json`, construye objetos `shapely.geometry.Point` a partir de las coordenadas geográficas de cada registro y genera un `geopandas.GeoDataFrame` con sistema de referencia de coordenadas `EPSG:4326` (WGS84).
- **Parámetros:** Ninguno.
- **Retorno:** `geopandas.GeoDataFrame` con todos los focos satelitales registrados.

---

<a id="procesar_una_fecha"></a>
### `procesar_una_fecha(fecha, df_fuente=None, verbose=True)`
- **Firma:** `def procesar_una_fecha(fecha, df_fuente=None, verbose=True):`
- **Descripción:** Procesa integralmente los focos satelitales de un día determinado:
  1. Filtra los puntos correspondientes a la fecha solicitada.
  2. Aplica el filtro espacial del bounding box de Corrientes (`LAT_MIN, LAT_MAX, LON_MIN, LON_MAX`).
  3. Si no hay focos en la zona, retorna `None`.
  4. Rasteriza los puntos a una matriz binaria de $256 \times 256$ y la guarda como `output/matriz_fractal_recorte_{fecha}.npy`.
  5. Aplica 11 iteraciones de dilatación morfológica binaria (`scipy.ndimage.binary_dilation`) y la guarda como `output/matriz_fractal_recorte_continua_{fecha}.npy`.
  6. Segmenta los clusters conectados con `scipy.ndimage.label`, identifica el componente conexo con mayor número de celdas (el cuerpo principal del incendio) y descarta el ruido aislado.
  7. Guarda la matriz final resultante en `output/matriz_objetivo_limpia_{fecha}.npy`.
  8. Genera y guarda la figura en alta resolución `output/silueta_fractal_limpia_{fecha}.png` con orientación vertical correcta (`origin='lower'`).
- **Parámetros:**
  - `fecha` (str): Fecha a procesar en formato `AAAA-MM-DD`.
  - `df_fuente` (`geopandas.GeoDataFrame`, opcional): GeoDataFrame precargado para evitar lecturas redundantes a disco. Si es `None`, invoca `obtener_df_completo()`.
  - `verbose` (bool, opcional): Si es `True`, imprime mensajes de estado y telemetría en la consola. Por defecto `True`.
- **Retorno:** `str` con la ruta relativa del archivo `.npy` limpio generado (`'output/matriz_objetivo_limpia_<fecha>.npy'`), o `None` si la fecha no contiene focos dentro del área de estudio.

---

<a id="procesar_rango_fechas"></a>
### `procesar_rango_fechas(fecha_inicio, fecha_fin)`
- **Firma:** `def procesar_rango_fechas(fecha_inicio, fecha_fin):`
- **Descripción:** Automatiza el procesamiento por lotes para intervalos temporales de análisis. Carga la base satelital, extrae todas las fechas únicas disponibles comprendidas en el rango $[fecha\_inicio, fecha\_fin]$, las ordena cronológicamente y ejecuta `procesar_una_fecha` sobre cada una. Oprime y descarta automáticamente los días con cero focos en la región.
- **Parámetros:**
  - `fecha_inicio` (str): Fecha inicial en formato `AAAA-MM-DD`.
  - `fecha_fin` (str): Fecha final en formato `AAAA-MM-DD`.
- **Retorno:** `list` de tuplas `[(fecha, ruta_matriz_npy), ...]`, conteniendo únicamente los días válidos ordenados cronológicamente.

---

<a id="procesar_fecha"></a>
### `procesar_fecha(fecha_elegida=None)`
- **Firma:** `def procesar_fecha(fecha_elegida=None):`
- **Descripción:** Función de conveniencia interactiva orientada a la ejecución para un único día. Si no se le provee `fecha_elegida`, lista en pantalla la distribución de focos por fecha de la base de datos y le solicita al usuario por teclado que ingrese la fecha que desea procesar. Luego delega el cómputo en `procesar_una_fecha`.
- **Parámetros:**
  - `fecha_elegida` (str, opcional): Fecha a procesar. Por defecto `None`.
- **Retorno:** `str` con la ruta de la matriz procesada, o `None`.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

*Este archivo no importa funciones ni constantes de otros módulos del proyecto.* Funciona como productor primario y proveedor de datos dentro de la arquitectura.

