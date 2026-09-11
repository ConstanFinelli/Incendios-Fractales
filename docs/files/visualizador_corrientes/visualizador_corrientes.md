# Documentación: `visualizador_corrientes.py`

## 1. Propósito General del Módulo
`visualizador_corrientes.py` es el subsistema de **Sistemas de Información Geográfica (GIS) y Cartografía Espacial Provincial**. Su función principal es transponer las matrices de simulación matemática generadas por el autómata celular sobre las coordenadas geográficas reales del territorio de la Provincia de Corrientes, Argentina ($[-30.8^\circ, -27.2^\circ] \text{ Latitud Sur}$ y $[-59.8^\circ, -55.6^\circ] \text{ Longitud Oeste}$).

El módulo genera cartografía estática para publicaciones científicas (300 DPI) con división departamental y etiquetas tipográficas con halo protector, construye mapas web interactivos en Folium con capas conmutables e infraestructura Data URI autónoma, y calcula analíticas espaciales de impacto por departamento.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo actúa dentro de la **Fase 3** como el puente de visualización a escala provincial:
- Recibe las matrices predictivas (+24h, +48h, +72h) y la matriz de riesgo isócrono desde `simulador_predictivo.py`.
- Aplica una máscara poligonal binaria de contorno provincial (`data/mascara_corrientes_256.npy`) para evitar que el fuego desborde artificialmente hacia provincias vecinas (Chaco, Misiones, Santa Fe, Entre Ríos) o sobre países limítrofes (Paraguay, Uruguay).
- Realiza el análisis de riesgo territorial por departamento (`identificar_departamentos_afectados`).
- Exporta tanto la figura GIS multipanel para informes técnicos como el mapa interactivo HTML para monitoreo en navegadores web.

```
       [Matrices de Predicción 24h/48h/72h]
                        │
                        ▼
         visualizador_corrientes.py
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
 Máscara Provincial  Análisis por      Cartografía
 (Corte de límites)  Departamentos     Multicanal
                        │                │
                        ▼                ├─► mapa_corrientes_prediccion.png (GIS 4 Paneles)
                 Ranking de Impacto      │
                 (Táctico/Prev/Estrat)   └─► mapa_corrientes_interactivo.html (Web Folium)
```

---

## 3. Entradas y Salidas
### Entradas:
- `matriz_inicial`: Matriz satelital del primer día analizado.
- `matriz_final`: Matriz satelital del último día analizado (punto de partida base).
- `matriz_futura`: Diccionario `{'24h': m24, '48h': m48, '72h': m72}` o matriz única.
- `mapa_riesgo`: Matriz isócrona con valores $\{0, 1, 2, 3, 4\}$.
- `mejores_variables`: Tupla de parámetros microclimáticos inferidos.

### Salidas (generadas en `output/`):
- `output/mapa_corrientes_prediccion.png`: Cartografía estática en 4 paneles horizontales en alta resolución (300 DPI) con capas vectoriales departamentales superpuestas.
- `output/mapa_corrientes_interactivo.html`: Aplicación web interactiva en Folium con selector de capas raster individuales por horizonte, tooltips con datos departamentales y leyenda flotante.
- `ranking_24h`, `ranking_48h`, `ranking_72h`: Desglose impreso y retornado en diccionarios con el top de departamentos más amenazados en cada ventana temporal.

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `os`, `json`, `io`, `base64`.
- **Manipulación de datos espaciales:** `geopandas`, `pandas`, `shapely.geometry.Point`, `shapely.ops.unary_union`.
- **Cálculo matricial y tratamiento de imágenes:** `numpy`, `PIL.Image`.
- **Visualización estática:** `matplotlib.pyplot`, `matplotlib.patches`, `matplotlib.patheffects`, `matplotlib.colors.ListedColormap`.
- **Visualización interactiva web:** `folium`, `folium.raster_layers`, `folium.plugins`.

---

## 5. Fundamentos Cartográficos y de Diseño Visual

### 1. Máscara Provincial de Preservación de Límites:
El autómata celular opera sobre una matriz matemática cuadrada de $256 \times 256$ celdas sin noción de fronteras políticas ni fluviales. Para asegurar el rigor cartográfico, la función `cargar_mascara_provincia` proyecta una malla regular de puntos geográficos sobre el polígono unificado de Corrientes (`unary_union`) y genera una máscara booleana 2D. Todos los frentes de fuego simulados se filtran mediante:
$$\text{Fuego}_{\text{filtrado}} = \text{Matriz}_{\text{fuego}} \land \text{Máscara}_{\text{provincia}}$$

### 2. Estructura de los 4 Paneles GIS Estáticos:
La figura horizontal (resolución $28 \times 7.8$ pulgadas a 300 DPI) divide el análisis en 4 etapas nítidas:
1. **Panel 1 - Foco Base Observado ($T_{\text{final}}$):** Focos reales confirmados en color carbón consolidado (`#2c3e50`).
2. **Panel 2 - Predicción a +24 Horas:** Foco base en semitransparencia junto al nuevo avance táctico en color dorado/ámbar (`#f39c12`).
3. **Panel 3 - Predicción a +48 Horas:** Focos previos más el avance preventivo en color naranja cálido (`#e67e22`).
4. **Panel 4 - Predicción a +72 Horas y Mapa Isócrono:** Todas las isócronas desplegadas con el avance estratégico terminal en color rojo carmesí (`#e74c3c`).

### 3. Codificación Autónoma Data URI Base64:
Para garantizar que los archivos HTML interactivos de Folium funcionen de manera 100% portable y autónoma (sin depender de servidores web locales o rutas absolutas a archivos PNG en disco), la función `_crear_data_uri_rgba` convierte directamente las matrices de simulación en cadenas Data URI (`data:image/png;base64,...`) con orientación espacial corregida mediante `np.flipud` para coincidir con la convención geográfica de Folium (fila 0 = Norte).

