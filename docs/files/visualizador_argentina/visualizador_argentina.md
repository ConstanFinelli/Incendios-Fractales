# Documentación: `visualizador_argentina.py`

## 1. Propósito General del Módulo
`visualizador_argentina.py` es el subsistema de **Sistemas de Información Geográfica (GIS) y Cartografía Espacial a Escala Nacional**. Su cometido es contextualizar geográficamente los incendios de Corrientes dentro del territorio de la República Argentina completa ($[-55.5^\circ, -21.5^\circ] \text{ Latitud Sur}$ y $[-74.0^\circ, -53.0^\circ] \text{ Longitud Oeste}$).

Permite a tomadores de decisiones de organismos nacionales (como el Sistema Nacional del Manejo del Fuego, Defensa Civil y Parques Nacionales) dimensionar la magnitud geográfica y estratégica de los escenarios a +24h, +48h y +72h respecto al resto del país.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo opera en la **Fase 3** (Cartografía y Comunicación):
- Procesa las geometrías de las 24 provincias argentinas, aplicando simplificación topológica vectorial para garantizar renderizado ágil en web y publicaciones.
- Consume la máscara provincial provista por `visualizador_corrientes.py` para asegurar que las capas raster conserven coherencia geométrica en los límites fluviales.
- Genera el mapa estático GIS nacional de 4 paneles a 300 DPI y el mapa interactivo web en Folium con cobertura de todo el cono sur.

```
       [Matrices de Simulación 24h / 48h / 72h]
                         │
                         ▼
             visualizador_argentina.py
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
 Geometrías Provinciales           Capas Raster Autónomas
 (24 Provincias Simplificadas)    (Filtro de visualizador_corrientes)
        │                                 │
        └────────────────┬────────────────┘
                         ▼
      ┌──────────────────┴──────────────────┐
      ▼                                     ▼
[Mapa GIS Nacional 4 Paneles]       [Mapa Web Folium Nacional]
 mapa_argentina_prediccion.png       mapa_argentina_interactivo.html
```

---

## 3. Entradas y Salidas
### Entradas:
- `matriz_inicial`, `matriz_final`: Matrices satelitales de partida.
- `matriz_futura`: Diccionario con las proyecciones `{'24h': ..., '48h': ..., '72h': ...}`.
- `mapa_riesgo`: Matriz isócrona $\{0, 1, 2, 3, 4\}$.
- `mejores_variables`: Variables microclimáticas inferidas.

### Salidas (generadas en `output/`):
- `output/mapa_argentina_prediccion.png`: Cartografía estática nacional en 4 paneles a 300 DPI que ilustra la propagación del fuego sobre Corrientes en relación con el territorio argentino completo.
- `output/mapa_argentina_interactivo.html`: Mapa interactivo en Folium con control de capas, navegación nacional y regional, y tooltips de todas las provincias argentinas.

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `os`, `json`, `io`, `base64`.
- **Análisis espacial y vectoriales:** `geopandas`, `pandas`.
- **Cálculo matricial y tratamiento de imágenes:** `numpy`, `PIL.Image`.
- **Visualización cartográfica estática:** `matplotlib.pyplot`, `matplotlib.patches`, `matplotlib.patheffects`, `matplotlib.colors.ListedColormap`.
- **Visualización cartográfica interactiva:** `folium`, `folium.raster_layers`, `folium.plugins`.
- **Módulos locales del proyecto:**
  - `visualizador_corrientes` (`cargar_mascara_provincia`).

---

## 5. Fundamentos Cartográficos y de Diseño

### 1. Simplificación Topológica Vectorial:
Para desplegar las 24 provincias argentinas sin sobrecargar la memoria ni ralentizar el renderizado en Folium o Matplotlib, la función `cargar_geometria_argentina` descarga los departamentos oficiales, realiza una disolución por provincia (`dissolve(by='provincia')`) y aplica el algoritmo de Douglas-Peucker (`simplify(tolerance=0.01, preserve_topology=True)`). Esto reduce el peso del GeoJSON en más de un $80\%$ preservando la fidelidad topológica de los límites interprovinciales.

### 2. Multi-Escala y Orientación de Paneles:
El mapa estático nacional presenta 4 paneles donde cada uno abarca la silueta completa de Argentina continental, con una retícula de meridianos y paralelos, permitiendo contrastar de forma directa el avance del incendio en la cuenca del Litoral frente a la totalidad del territorio soberano.

