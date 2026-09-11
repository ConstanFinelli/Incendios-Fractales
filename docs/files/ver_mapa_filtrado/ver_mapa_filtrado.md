# Documentación: `ver_mapa_filtrado.py`

## 1. Propósito General del Módulo
`ver_mapa_filtrado.py` es el motor de ingestión geoespacial, rasterización discreta y procesamiento morfológico del sistema. Su misión fundamental es transformar coordenadas continuas de focos satelitales (latitud, longitud) provistas por los sensores espaciales de la NASA en matrices binarias discretas de $256 \times 256$ celdas, aplicando operaciones morfológicas avanzadas para unificar frentes de fuego activos y eliminar el ruido instrumental de anomalías térmicas aisladas.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo es el pilar de la **Fase 1** (Preprocesamiento Satelital):
- Provee la interfaz de carga diferida (*Lazy Loading*) para datasets pesados de la NASA mediante GeoPandas y Shapely.
- Aplica el recorte geográfico (*spatial bounding box*) restringido a los límites de la Provincia de Corrientes.
- Transforma los datos vectoriales puntuales en rejillas matriciales calibradas espacialmente.
- Realiza el filtrado morfológico de dilatación y la extracción del componente conexo principal, generando las matrices de verdad de terreno (*ground truth*) que alimentan tanto al algoritmo genético como a la verificación fractal.

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
   Dilatación Morfológica (11 iteraciones) (matriz_fractal_recorte_continua_*.npy)
            │
            ▼
   Extracción de Componente Conexo Principal (matriz_objetivo_limpia_*.npy)
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
- `matriz_fractal_recorte_<fecha>.npy`: Matriz cruda $256 \times 256$ de puntos de calor detectados.
- `matriz_fractal_recorte_continua_<fecha>.npy`: Matriz tras 11 ciclos de dilatación morfológica.
- `matriz_objetivo_limpia_<fecha>.npy`: Matriz con el cuerpo principal de fuego unificado (ruido aislado eliminado).
- `silueta_fractal_limpia_<fecha>.png`: Renderizado monocromático de alta resolución a 300 DPI con `origin='lower'`.

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `os`, `sys`.
- **Manipulación de datos y geometrías:** `pandas`, `geopandas`, `shapely.geometry.Point`.
- **Cálculo matricial e imágenes:** `numpy`, `scipy.ndimage.binary_dilation`, `scipy.ndimage.label`.
- **Visualización:** `matplotlib.pyplot`.

---

## 5. Fundamentos Matemáticos y Metodológicos
### 1. Mapeo Proyectivo Espacio Continuo $\to$ Espacio Discreto:
Dado un punto satelital $(\text{lat}_i, \text{lon}_i)$, sus índices de matriz $(r_i, c_i)$ en una grilla de dimensión $N = 256$ se calculan como:
$$r_i = \left\lfloor \frac{\text{lat}_i - \text{LAT\_MIN}}{\text{LAT\_MAX} - \text{LAT\_MIN}} \times (N - 1) \right\rfloor$$
$$c_i = \left\lfloor \frac{\text{lon}_i - \text{LON\_MIN}}{\text{LON\_MAX} - \text{LON\_MIN}} \times (N - 1) \right\rfloor$$
Ambos índices se truncan con `np.clip` al rango $[0, N-1]$.

### 2. Dilatación Morfológica Binaria:
Para cerrar discontinuidades espaciales entre focos dispersos causados por el intervalo de muestreo satelital o nubosidad parcial, se aplica una dilatación binaria iterativa con un elemento estructurante de vecindad $3 \times 3$ durante 11 iteraciones:
$$A \oplus B = \bigcup_{b \in B} A_b$$

### 3. Extracción del Componente Conexo Principal:
Se utiliza la función `scipy.ndimage.label` con conectividad de 8 vecinos para segmentar los clusters de fuego en islas independientes. Se computa el tamaño de cada componente mediante `np.bincount` y se aísla únicamente el componente de máxima cardinalidad:
$$C_{\text{principal}} = \arg\max_{k \ge 1} |C_k|$$
Esto descarta quemas prescritas menores o anomalías térmicas industriales ajenas al gran incendio forestal modelado.

