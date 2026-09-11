# Funciones de `capa_biomasa.py`

## 1. Funciones Definidas en este Archivo

<a id="descargar_capas_ign_si_faltan"></a>
### `descargar_capas_ign_si_faltan()`
- **Firma:** `def descargar_capas_ign_si_faltan():`
- **Descripción:** Verifica la presencia en la carpeta local `data/` de los tres archivos GeoJSON vectoriales oficiales del Instituto Geográfico Nacional (IGN) correspondientes a aguas continentales perennes, vegetación hidrófila y plantaciones arbóreas. En caso de ausencia de alguno de ellos, efectúa la consulta y descarga vía WFS (`EPSG:4326`) recortando la petición a la *bounding box* de Corrientes (`[-59.8, -31.5, -55.5, -27.0]`), empleando un contexto SSL permisivo para los geoservicios públicos de la República Argentina.
- **Parámetros:** Ninguno.
- **Retorno:** `None`. Descarga y guarda en disco `ign_aguas_perenne.geojson`, `ign_vegetacion_hidrofila.geojson` y `ign_plantaciones_forestales.geojson`.

---

<a id="cargar_o_generar_mapa_combustible"></a>
### `cargar_o_generar_mapa_combustible(tamano=256, recalcular=False)`
- **Firma:** `def cargar_o_generar_mapa_combustible(tamano=256, recalcular=False):`
- **Descripción:** Carga desde caché en disco (`data/mapa_combustible_256.npy` y `data/categorias_cobertura_256.npy`) o en memoria RAM las matrices discretizadas de combustible y coberturas. Si no existen o si `recalcular=True`, invoca la descarga de capas IGN, carga la máscara provincial de Corrientes y rasteriza a alta velocidad mediante `shapely.contains_xy` sobre una malla 2D de $256 \times 256$ puntos ($65,536$ celdas) las tres capas vectoriales superponiéndolas con jerarquía estricta:
  1. Cobertura base dentro de la provincia: Pastizales y sabanas (Cat 3, $C = 0.6$).
  2. Plantaciones forestales: Pino y eucalipto (Cat 4, $C = 1.0$).
  3. Bañados y vegetación hidrófila: Pajonales y juncales (Cat 2, $C = 0.2$).
  4. Cuerpos de agua continentales y esteros profundos (Cat 1, $C = 0.0$, máxima prioridad / incombustible).
  5. Exterior provincial y ríos limítrofes Paraná y Uruguay: Dirichlet incombustible (Cat 0, $C = 0.0$).
  Persiste ambas matrices en formato binario NumPy `.npy` para accesos instantáneos ($< 1\text{ ms}$) en futuras corridas.
- **Parámetros:**
  - `tamano` (int, opcional): Resolución espacial cuadrada de la grilla. Por defecto `256`.
  - `recalcular` (bool, opcional): Si es `True`, ignora el caché local y fuerza la regeneración geométrica completa. Por defecto `False`.
- **Retorno:** Tupla `(mapa_combustible, categorias_cobertura)`:
  - `mapa_combustible` (`numpy.ndarray` 2D float): Matriz con valores de combustible $C \in [0.0, 1.0]$.
  - `categorias_cobertura` (`numpy.ndarray` 2D int): Matriz con etiquetas categóricas enteras $\{0, 1, 2, 3, 4\}$.

---

<a id="obtener_mapa_combustible"></a>
### `obtener_mapa_combustible(tamano=256)`
- **Firma:** `def obtener_mapa_combustible(tamano=256):`
- **Descripción:** Función de acceso rápido de solo lectura diseñada para el Autómata Celular (`automata_celular.py`) y el Algoritmo Genético (`algoritmo_genetico.py`). Llama a `cargar_o_generar_mapa_combustible` y devuelve exclusivamente la matriz continua 2D de coeficientes de combustible ($C \in [0.0, 1.0]$).
- **Parámetros:**
  - `tamano` (int, opcional): Dimensión espacial de la grilla cuadrada. Por defecto `256`.
- **Retorno:** `numpy.ndarray` 2D de tipo float con la matriz de combustible espacializado.

---

<a id="generar_mapa_cobertura_grafico"></a>
### `generar_mapa_cobertura_grafico(tamano=256, ruta_salida="output/mapa_cobertura_combustible.png")`
- **Firma:** `def generar_mapa_cobertura_grafico(tamano=256, ruta_salida="output/mapa_cobertura_combustible.png"):`
- **Descripción:** Construye una visualización cartográfica científica de alta resolución ($300\text{ DPI}$) sobre la provincia de Corrientes. Superpone la grilla de coberturas biofísicas de biomasa clasificada con los límites departamentales vectoriales oficiales, rotulación de nombres con halo blanco protector, grilla de coordenadas en grados geográficos (latitud/longitud) y una leyenda explicativa con la proporción porcentual y cantidad exacta de celdas de cada categoría de combustible.
- **Parámetros:**
  - `tamano` (int, opcional): Resolución de la grilla a graficar. Por defecto `256`.
  - `ruta_salida` (str, opcional): Ruta del archivo PNG de destino. Por defecto `"output/mapa_cobertura_combustible.png"`.
- **Retorno:** `str`: Ruta al archivo generado.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

- `cargar_mascara_provincia` (desde `visualizador_corrientes.py`): Invocada de forma diferida en `cargar_o_generar_mapa_combustible` como respaldo en caso de que la máscara provincial `data/mascara_corrientes_256.npy` aún no haya sido serializada en disco.
