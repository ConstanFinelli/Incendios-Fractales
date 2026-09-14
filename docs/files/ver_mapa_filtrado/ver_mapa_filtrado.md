# Documentación: `ver_mapa_filtrado.py`

## 1. Propósito General del Módulo

`ver_mapa_filtrado.py` es el motor de ingestión geoespacial, rasterización discreta y procesamiento morfológico del sistema. Su misión fundamental es transformar coordenadas continuas de focos satelitales (latitud, longitud) provistas por los sensores espaciales de la NASA en matrices binarias discretas de $256 \times 256$ celdas, aplicando operaciones morfológicas avanzadas para unificar frentes de fuego activos y eliminar el ruido instrumental de anomalías térmicas aisladas.

---

## 2. Rol en la Arquitectura del Sistema

Este módulo es el pilar de la **Fase 1** (Preprocesamiento Satelital):

- Provee la interfaz de carga diferida (_Lazy Loading_) para datasets pesados de la NASA mediante GeoPandas y Shapely.
- Aplica el recorte geográfico (_spatial bounding box_) restringido a los límites de la Provincia de Corrientes.
- Transforma los datos vectoriales puntuales en rejillas matriciales calibradas espacialmente.
- Realiza el filtrado morfológico de dilatación y la extracción del componente conexo principal, generando las matrices de verdad de terreno (_ground truth_) que alimentan tanto al algoritmo genético como a la verificación fractal.

```
  [JSON Satelital NASA]
            │
            ▼
    Lazy Loading (GeoPandas)
            │
            ▼
   Filtro Bounding Box Corrientes [-30.8 a -27.2 Lat, -59.8 a -55.6 Lon]
            │
            ▼
   Rasterización Discreta 256x256 (matriz_fractal_recorte_*.npy)
            │
            ▼
   Dilatación Física de Pavesas (1 iteración, ~1.6 km) (matriz_fractal_recorte_continua_*.npy)
            │
            ▼
   Preservación Integral Multicluster (matriz_objetivo_limpia_*.npy)
            │
            ▼
   [Matriz Limpia para AG y Simulación] + [Silueta Gráfica PNG]
```

---

## 3. Entradas y Salidas

### Entradas:

- **Base de datos espacial:** `./DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json`.
- **Límites geográficos (Bounding Box Corrientes):**
  - $\text{Latitud} \in [-30.8^\circ, -27.2^\circ]$
  - $\text{Longitud} \in [-59.8^\circ, -55.6^\circ]$
- **Parámetros temporales:** Fecha única o intervalo de fechas `[fecha_inicio, fecha_fin]`.

### Salidas (generadas en `output/`):

- `output/npy/matriz_fractal_recorte_<fecha>.npy`: Matriz cruda $256 \times 256$ de puntos de calor detectados.
- `output/npy/matriz_fractal_recorte_continua_<fecha>.npy`: Matriz tras 1 ciclo de dilatación morfológica física (~1.6 km).
- `output/npy/matriz_objetivo_limpia_<fecha>.npy`: Matriz multicluster con frentes de fuego activos preservados al 100%.
- `output/siluetas/silueta_fractal_limpia_<fecha>.png`: Renderizado monocromático de alta resolución a 300 DPI con `origin='lower'`.

---

## 4. Dependencias y Librerías

- **Librerías estándar:** `os`, `sys`.
- **Manipulación de datos y geometrías:** `pandas`, `geopandas`, `shapely.geometry.Point`.
- **Cálculo matricial e imágenes:** `numpy`, `scipy.ndimage.binary_dilation`.
- **Visualización:** `matplotlib.pyplot`.

---

## 5. Fundamentos Matemáticos y Metodológicos

### 1. Mapeo Proyectivo Espacio Continuo $\to$ Espacio Discreto:

Dado un punto satelital $(\text{lat}_i, \text{lon}_i)$, sus índices de matriz $(r_i, c_i)$ en una grilla de dimensión $N = 256$ se calculan como:
$$r_i = \left\lfloor \frac{\text{lat}_i - \text{LAT\_MIN}}{\text{LAT\_MAX} - \text{LAT\_MIN}} \times (N - 1) \right\rfloor$$
$$c_i = \left\lfloor \frac{\text{lon}_i - \text{LON\_MIN}}{\text{LON\_MAX} - \text{LON\_MIN}} \times (N - 1) \right\rfloor$$
Ambos índices se truncan con `np.clip` al rango $[0, N-1]$.

### 2. Dilatación Morfológica Física Calibrada:

Para representar físicamente el radio de dispersión térmica y salto de pavesas primarias (_short-range spotting_) entre frentes cercanos, se aplica una dilatación binaria iterativa con un elemento estructurante de vecindad $3 \times 3$ acotada a **1 iteración** (`ITERACIONES_DILATACION = 1`):
$$A \oplus B = \bigcup_{b \in B} A_b$$
Esto genera un radio de influencia de $\approx 1.57\text{ km}$ (cruz simétrica de 5 celdas por foco), evitando sobredimensionar artificialmente el área de quema o puentear canales hídricos de la capa de biomasa de Corrientes.

### 3. Preservación Integral Multi-Cluster:

Se erradicó la antigua limitación del cluster único (`argmax`) que borraba frentes activos en otras regiones de la provincia. Asimismo, tras comprobarse que todo punto dilatado supera las 5 celdas (lo que volvía redundante cualquier corte de masa crítica conexa post-dilatación), la matriz dilatada se adopta directamente como verdad de terreno, garantizando que el **100% de las observaciones satelitales validadas por la NASA** estén disponibles para la optimización inversa y la proyección predictiva.
