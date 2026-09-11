# Documentación Integral del Proyecto: Modelado Fractal y Predicción de Incendios mediante Algoritmos Genéticos

Este documento presenta una explicación completa, pedagógica y estructurada de todo el código y la arquitectura del sistema. Está diseñado para que cualquier persona que se incorpore al proyecto pueda comprender desde cero cómo surgió la investigación, cómo funciona cada módulo y el detalle exacto de todas las funciones implementadas.

---

## 1. Contexto, Origen y Motivación del Proyecto

### 1.1. La Problemática Real (Megaincendios de Corrientes 2022)

A principios de 2022, la provincia de Corrientes (Argentina) sufrió una catástrofe socioecológica en la que el fuego consumió más de un millón de hectáreas, afectando gravemente los Esteros del Iberá y zonas productivas.

Durante la catástrofe, los equipos de brigadistas tuvieron dificultades operativas para anticipar el avance del fuego debido a:

1. **Comportamiento no lineal y caótico:** El fuego no avanza como un círculo o elipse perfecto; interactúa con parches de vegetación seca, cuerpos de agua fragmentados y ráfagas de viento, formando patrones ramificados con **geometría fractal** (auto-similaridad y alta rugosidad perimetral).
2. **Falta de estaciones meteorológicas locales:** En el humedal, la estación climática más cercana puede estar a más de 50 km, impidiendo conocer el microclima exacto (velocidad y dirección real del viento en superficie, humedad del combustible) en el punto crítico del fuego.

### 1.2. La Solución Científica: Optimización Inversa

En lugar de intentar "adivinar" el clima para simular el fuego, el proyecto plantea el camino inverso (**Optimización Inversa**):

- Tomar las fotografías satelitales reales del incendio provistas por la NASA (sensores VIIRS/MODIS).
- Medir la **rugosidad geométrica (Dimensión Fractal $D$)** y la **forma espacial** de la mancha satelital.
- Usar un **Algoritmo Genético (AG)** para deducir qué combinación de viento, dirección, humedad y combustible fue la causante de que el fuego adoptara esa silueta fractal específica.
- Una vez inferidas las variables óptimas, alimentar un **Autómata Celular (AC)** para proyectar hacia el futuro y generar **Mapas de Riesgo Predictivos**.

---

## 2. Diagrama de Flujo y Pipeline del Sistema

```mermaid
flowchart TD
    subgraph FASE 1: Preprocesamiento Satelital
        A["JSON NASA FIRMS (VIIRS/MODIS)"] --> B["ver_mapa_filtrado.py\n(Recorte Corrientes + Dilatación Física 2 iter + Filtrado Multi-Cluster)"]
        B --> C["Serie de Matrices Binarias 256x256 (.npy)\n[T0, T1, ..., Tk]"]
    end

    subgraph FASE 2: Optimización Inversa Multitemporal
        C --> D["algoritmo_genetico.py\n(Población de Cromosomas Climáticos)"]
        D --> E["calcular_dimension_fractal.py\n(Box-Counting Directo D_sat)"]
        D --> F["automata_celular.py\n(Simulación Estocástica AC)"]
        F --> G["Fitness Multitemporal Híbrido\nPromedio(0.4*Fractal + 0.6*IoU)"]
        G --> D
    end

    subgraph FASE 3: Simulación Preventiva
        D --> H["Mejores Variables Microclimáticas\n(Viento, Dirección, Humedad, Combustible)"]
        C --> I["simulador_predictivo.py"]
        H --> I
        I --> J["Mapa de Riesgo Predictivo Multipanel (.png)"]
    end

    subgraph FASE 4: Transposición Cartográfica Territorial
        I --> K["visualizador_corrientes.py\n(Georreferenciación Departamental)"]
        L["GeoJSON 25 Departamentos de Corrientes"] --> K
        K --> M["Mapa GIS Estático de Corrientes\noutput/mapa_corrientes_prediccion.png"]
        K --> N["Mapa Web Interactivo Folium Corrientes\noutput/mapa_corrientes_interactivo.html"]
        K --> O["Ranking de Departamentos Afectados"]

        I --> P["visualizador_argentina.py\n(Contexto Nacional y Regional)"]
        Q["GeoJSON 24 Provincias de Argentina"] --> P
        P --> R["Mapa GIS Estático de Argentina\noutput/mapa_argentina_prediccion.png"]
        P --> S["Mapa Web Interactivo Folium Argentina\noutput/mapa_argentina_interactivo.html"]
    end
```

---

## 3. Convenciones Físicas, Matemáticas y de Modelado

Para que el modelo computacional sea fiel a las leyes de la física y a la ecología de los incendios forestales, el sistema adopta una serie de convenciones rigurosamente fundamentadas:

### 3.1. Dirección del Viento en Grados Sexagesimales (\(0^\circ - 360^\circ\))

- **Estándar Meteorológico (Rosa de los Vientos):** En las estaciones del INTA y sensores oficiales, la dirección del viento se mide en grados de azimut (\(0^\circ / 360^\circ = \text{Norte}\), \(90^\circ = \text{Este}\), \(180^\circ = \text{Sur}\), \(270^\circ = \text{Oeste}\)). Esto permite contrastar directamente las variables inferidas por el AG contra los registros climáticos históricos de febrero de 2022.
- **Espacio Continuo para el AG:** Permite al Algoritmo Genético afinar el ángulo con precisión decimal continua (ej. \(181.4^\circ\)) en lugar de limitarse a 4 u 8 puntos cardinales discretos.
- **Modelado Trigonométrico en el Autómata Celular:** Para cada celda vecina en la vecindad de Moore, se calcula el ángulo geométrico hacia ella (\(\theta*{\text{vecino}} = \text{arctan2}(-dy, dx)\)) y se evalúa la alineación con el viento mediante el coseno:
  $$\text{alineacion} = \cos(\theta*{\text{viento}} - \theta*{\text{vecino}})$$
  $$\text{Factor Viento} = e^{c \cdot v*{\text{viento}} \cdot \text{alineacion}}$$
  - A favor del viento (\(\Delta\theta = 0^\circ, \cos=1\)): Máxima aceleración y probabilidad (\(e^{+c \cdot v}\)).
  - Perpendicular (\(\Delta\theta = 90^\circ, \cos=0\)): Propagación lateral neutra (\(e^0 = 1\)).
  - En contra (\(\Delta\theta = 180^\circ, \cos=-1\)): Fuerte resistencia al avance (\(e^{-c \cdot v}\)).

---

### 3.2. Rango de Velocidad del Viento (\(0 - 50\text{ km/h}\))

- **Evidencia Meteorológica Real (Corrientes 2022):** En los registros históricos del INTA para enero-febrero de 2022, los vientos medios sostenidos oscilaron entre \(15\) y \(35\text{ km/h}\), mientras que las ráfagas máximas críticas alcanzaron picos de \(45\) a \(55\text{ km/h}\). Vientos sostenidos superiores a \(50\text{ km/h}\) corresponden a temporales severos (Escala Beaufort 7 a 8), sumamente atípicos en días secos y despejados sin tormenta. El rango \([0, 50]\) cubre el \(99.9\%\) de las condiciones reales del desastre.
- **Saturación Matemática en el Autómata Celular:** En la ecuación del AC, el factor del viento crece exponencialmente:
  $$\text{Factor Viento} = e^{0.05 \cdot v_{\text{viento}} \cdot \cos(\Delta\theta)}$$
  A \(v = 50\text{ km/h}\), el factor multiplicador a favor del viento es \(e^{2.5} \approx 12.18\times\), lo que satura la probabilidad de ignición al tope máximo permitido por el simulador (\(95\%\)). Permitir velocidades mayores (ej. \(80-100\text{ km/h}\)) crearía una "zona ciega" donde el AG no podría distinguir entre valores porque todos producirían exactamente el mismo avance saturado al \(95\%\), perdiendo gradiente de optimización.
- **Resolución Espacial y Estabilidad:** En una grilla de \(256 \times 256\) donde cada celda representa \(\sim 2-3\text{ km}\), una velocidad de \(50\text{ km/h}\) permite avanzar \(60-90\text{ km/día}\) en 30 pasos de simulación, coincidiendo con la tasa de expansión récord real y evitando que el frente escape o se desborde fuera de la matriz.

---

### 3.3. Rango de Humedad Relativa (\(10\% - 80\%\))

- **Límite Inferior (\(10\%\)):** Representa el escenario de sequía extrema y ola de calor crítica durante el fenómeno de _La Niña_ en Corrientes 2022. Humedades menores son físicamente inexistentes en el bioma de humedales y pastizales del litoral.
- **Límite Superior (\(80\%\) - Humedad de Extinción):** En ciencias forestales, cuando la humedad ambiente supera el \(75\%-80\%\), la vegetación absorbe tanta agua que la combustión no puede autosostenerse: **el fuego se extingue naturalmente**. Explorar humedades mayores en el AG sería inviable porque el fuego moriría en el primer paso.
- **Efecto Matemático:** El factor de sequedad en el AC se calcula como \((1.0 - \text{humedad}/100) \in [0.20, 0.90]\).

---

### 3.4. Rango de Combustible (\(0.1 - 1.0\)) y Distinción entre Nivel Local vs. Global

Es fundamental distinguir entre el combustible a nivel local (celda por celda) y el gen de combustible a nivel macro (Algoritmo Genético):

1. **Combustible Local (Celda puntual) — SÍ puede y debe llegar a 0:**
   - Cuando la vegetación de una celda se quema por completo, pasa a **Cenizas (Estado 2)**. Al convertirse en ceniza, su combustible local se agota (\(=0\)) y queda inerte para siempre.
   - Cuerpos de agua (ríos, lagunas del Iberá) o cortafuegos tienen combustible local \(=0\) y actúan como barreras infranqueables.
2. **Combustible Global (Gen del AG) — NO puede ser 0 (\(0.1 - 1.0\)):**
   - El gen del cromosoma representa la **densidad y tipo de biomasa macroscópica de todo el ecosistema de la región** (pastizales densos \(=1.0\), monte ralo \(=0.4\), etc.).
   - Si el gen fuera \(0.0\), significaría que en las 65.536 celdas del mapa no existe ni una sola brizna de pasto en ningún lado (un desierto estéril o mar abierto), en cuyo caso el incendio real detectado por el satélite nunca habría podido existir.
   - El piso de \(0.1\) asegura que siempre exista un mínimo de vegetación para evaluar la dinámica geométrica.

---

### 3.5. Estados de Celda en el Autómata Celular y el Rol de las Cenizas

El simulador implementa 3 estados físicos:

- **Estado 0:** Vegetación Intacta (Combustible disponible para quemar).
- **Estado 1:** Fuego Activo (Ardiendo y contagiando a vecinos intactos).
- **Estado 2:** Cenizas / Zona Quemada (Combustible agotado, celda inerte).

**¿Por qué las cenizas son críticas?**

1. **Evitan bucles infinitos:** Si una celda no pasara a ceniza y volviera a estado intacto (0), el fuego retrocedería y se re-quemaría sobre sí mismo indefinidamente.
2. **Forman el anillo o frente de fuego real:** El incendio avanza como una onda expansiva periférica (frente activo en los bordes, interior consumido e inerte).
3. **Continuidad multitemporal día a día:** Lo que se quemó el Día 1 pasa a ser ceniza inerte el Día 2; el fuego del Día 2 solo avanza sobre la vegetación verde que aún rodea el perímetro.
4. **Medición Fractal:** El área total afectada ($1+2$) permite extraer el perímetro exterior exacto de la cicatriz satelital mediante Box-Counting.

---

### 3.6. Delimitación Territorial, Georreferenciación y Resolución Espacial de Corrientes

Para conectar las simulaciones fractales teóricas con la gestión operativa y territorial del riesgo, el sistema define un sistema de georreferenciación estricto sobre la provincia de Corrientes:

- **Coordenadas de la Zona de Estudio (Bounding Box):**
  $$\text{LAT}_{\min} = -30.8^\circ, \quad \text{LAT}_{\max} = -27.2^\circ \quad (\text{Sur a Norte})$$
  $$\text{LON}_{\min} = -59.8^\circ, \quad \text{LON}_{\max} = -55.6^\circ \quad (\text{Oeste a Este})$$
  Esta delimitación geográfica encuadra de forma óptima los $88.886\text{ km}^2$ de la provincia de Corrientes, desde el límite con Entre Ríos en el sur hasta la frontera con Paraguay y Misiones en el norte, y desde el Río Paraná en el oeste hasta el Río Uruguay en el este.

- **Resolución Espacial de la Grilla ($256 \times 256$ píxeles):**
  - En el eje de latitud: $\Delta \text{lat} = \frac{3.6^\circ}{255} \approx 0.0141^\circ \approx 1.57\text{ km por celda}$.
  - En el eje de longitud: $\Delta \text{lon} = \frac{4.2^\circ}{255} \approx 0.0165^\circ \approx 1.61\text{ km por celda}$ (evaluado a la latitud media de $-29^\circ$).
  - **Área representada por cada píxel:** Aproximadamente $1.57 \times 1.61 \approx 2.53\text{ km}^2$ ($253\text{ hectáreas}$). Esta resolución es ideal porque captura tanto los grandes frentes de fuego como las lagunas y parches del macrosistema Iberá sin degradar el rendimiento del autómata celular.

- **Fórmulas de Transformación Espacial Bidireccional:**
  1. *De coordenadas geográficas (lat, lon) a índices de celda $(i, j)$:*
     $$i = \text{clip}\left(\left\lfloor \frac{\text{lat} - \text{LAT}_{\min}}{\text{LAT}_{\max} - \text{LAT}_{\min}} \cdot (N - 1) \right\rfloor, 0, N - 1\right) \quad (\text{Fila / Latitud})$$
     $$j = \text{clip}\left(\left\lfloor \frac{\text{lon} - \text{LON}_{\min}}{\text{LON}_{\max} - \text{LON}_{\min}} \cdot (N - 1) \right\rfloor, 0, N - 1\right) \quad (\text{Columna / Longitud})$$
  2. *De índices de celda $(i, j)$ a coordenadas geográficas (lat, lon):*
     $$\text{lat}(i) = \text{LAT}_{\min} + \frac{i}{N - 1} (\text{LAT}_{\max} - \text{LAT}_{\min})$$
     $$\text{lon}(j) = \text{LON}_{\min} + \frac{j}{N - 1} (\text{LON}_{\max} - \text{LON}_{\min})$$

- **Fundamentación Geográfica de la Máscara Provincial (`mascara_corrientes_256.npy`):**
  Corrientes es una provincia casi enteramente mesopotámica/fluvial, delimitada por dos ríos de escala continental: el Río Paraná (al norte y oeste) y el Río Uruguay (al este). El fuego forestal no puede propagarse físicamente sobre espejos de agua de varios kilómetros de ancho para alcanzar Santa Fe, Chaco, Paraguay o Brasil. Para evitar que el autómata celular proyecte frentes de fuego irreales sobre provincias vecinas, el sistema utiliza una máscara booleana 2D construida a partir de la unión poligonal (`unary_union`) de los 25 departamentos oficiales. Todo avance proyectado fuera de este perímetro fluvial se desestima de forma automática.

---

### 3.7. Principales Decisiones de Diseño, Arquitectura y Cartografía

El desarrollo del visualizador cartográfico y la integración del pipeline involucran una serie de decisiones clave:

1. **Decisión 1: Georreferenciación Bidireccional y Orientación de Matrices (`np.flipud`):**
   - En matrices NumPy, el índice `[0, 0]` corresponde convencionalmente a la esquina superior izquierda. Sin embargo, en el sistema de coordenadas cartográficas, la fila 0 representa el límite inferior ($\text{Sur}, \text{LAT}_{\min}$), y la fila 255 el límite superior ($\text{Norte}, \text{LAT}_{\max}$).
   - En Matplotlib, esto se resuelve nativamente utilizando `origin='lower'` con `extent=[LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]`.
   - En bibliotecas web como Leaflet/Folium, el formato de imagen espera que la fila 0 sea el extremo norte de la bounding box. Para corregir este desfase geométrico, `visualizador_corrientes.py` aplica `np.flipud` a las imágenes RGBA generadas, garantizando una alineación geográfica exacta sobre las imágenes satelitales del terreno.

2. **Decisión 2: Empaquetado Autónomo en Base64 Data URIs (Cero Enlaces Rotos):**
   - La práctica común de generar imágenes temporales en disco (ej. `_overlay.png`) y referenciarlas desde el HTML interactivo genera enlaces rotos cuando el archivo HTML se mueve de carpeta, se comparte con otros investigadores o se visualiza en entornos remotos.
   - Para erradicar este problema, el visualizador codifica las capas raster del fuego como Data URIs en Base64 (`data:image/png;base64,...`) e incrusta los datos directamente en el código de Leaflet. Esto genera un archivo [mapa_corrientes_interactivo.html](../output/mapa_corrientes_interactivo.html) 100% autocontenido y portátil.

3. **Decisión 3: Jerarquía Visual Multicapa (Z-Ordering) y Halo Blanco (`path_effects`):**
   - En mapas de calor o siluetas de fuego extensas, las capas raster suelen tapar las divisiones departamentales y los nombres de los municipios.
   - Para asegurar la máxima legibilidad, se estableció un orden de capas estricto:
     - `zorder=1`: Polígonos de fondo departamental (`#f7f9fa`).
     - `zorder=2`: Grilla cartográfica de paralelos y meridianos.
     - `zorder=3`: Capas raster de fuego georreferenciado (ámbar `#d35400`, carbón `#2c3e50`, carmesí `#e74c3c`).
     - `zorder=4`: Límites departamentales en línea de trazos (`#7f8c8d`, `linestyle='--'`).
     - `zorder=5`: Perímetro provincial consolidado (`#1a252f`, `linewidth=1.6`).
     - `zorder=6`: Nombres de departamentos en negrita con efecto de halo blanco (`pe.withStroke(linewidth=2.2, foreground='white')`).

4. **Decisión 4: Análisis de Impacto Espacial para Defensa Civil:**
   - Para que la investigación tenga impacto práctico inmediato en la toma de decisiones, la función `identificar_departamentos_afectados` realiza una unión espacial (`gpd.sjoin`) entre cada celda activa del frente simulado y los polígonos departamentales, generando en consola un ranking de departamentos bajo amenaza con porcentaje de afectación.

5. **Decisión 5: Repositorio Ultraliviano y Carga Perezosa en `.gitignore`:**
   - Archivos vectoriales voluminosos (`departamentos_corrientes.json`, $\sim 855\text{ KB}$; `provincias_argentina.json`, $\sim 555\text{ KB}$) y matrices intermedias binarias (`.npy`) están excluidos de Git. Tanto `visualizador_corrientes.py` como `visualizador_argentina.py` descargan, optimizan y almacenan en caché local de forma transparente los recursos faltantes mediante mecanismos de resiliencia ante errores de red.

6. **Decisión 6: Visualización Cartográfica Nacional y Provincial Homogénea en 4 Paneles Multi-Horizonte:**
   - Tanto `visualizador_corrientes.py` como `visualizador_argentina.py` estructuran su salida estática en **cuatro paneles complementarios de alta resolución (300 DPI)**, compartiendo idéntica escala y encuadre geográfico sin distorsión de enfoque:
     - **Panel 1 (Foco Base Observado en $T_{\text{final}}$):** Muestra el foco satelital base consolidado al final del período de observación (azul noche `#2c3e50`), sin rojo de predicción, permitiendo visualizar la cicatriz real de partida.
     - **Panel 2 (Predicción Táctica a $+24\text{ Horas}$ / +30 ciclos):** Frente de avance táctico en ámbar (`#f39c12`) para cuadrillas y brigadistas en terreno.
     - **Panel 3 (Predicción Preventiva a $+48\text{ Horas}$ / +60 ciclos):** Expansión preventiva en naranja (`#e67e22`) para evacuación y maquinaria pesada.
     - **Panel 4 (Predicción Estratégica a $+72\text{ Horas}$ e Isócronas / +90 ciclos):** Expansión estratégica en rojo (`#e74c3c`) e isócronas sobre divisiones político-administrativas.
   - De este modo, el usuario obtiene exactamente los mismos cuatro productos analíticos tanto a escala provincial como de todo el país, sin sesgos de zoom ni cambios de perspectiva entre paneles.

7. **Decisión 7: Optimización y Disolución Topológica del GeoJSON Nacional:**
   - El archivo vectorial oficial de departamentos de toda la Argentina (`departamentos-argentina.json`) supera los $13.7\text{ MB}$, lo cual provocaría una severa degradación en el tiempo de apertura y renderizado web en Folium y Matplotlib.
   - La función `cargar_geometria_argentina()` descarga la geometría, agrupa y disuelve los polígonos por provincia (`dissolve(by='provincia')`), y aplica una simplificación topológica controlada (`geometry.simplify(tolerance=0.01, preserve_topology=True)`). Esto reduce el tamaño a tan solo $555\text{ KB}$ (una reducción del $96\%$), cargando en menos de $0.04\text{ s}$.

8. **Decisión 8: Rotulación Provincial Vectorial con Halo Blanco Protector (`path_effects`):**
   - Para que los nombres de las provincias se lean con máxima nitidez sin importar si se superponen con líneas de grilla o con los polígonos de las provincias vecinas, se implementó rotulación por centroides con efecto halo blanco (`pe.withStroke(linewidth=2.0, foreground='white')`), destacando a Corrientes con estrella y tipografía diferenciada.

9. **Decisión 9: Inicialización del Frente Predictivo en la Línea de Fuego Activa Final (`matriz_final = np.load(ruta_final)`):**
   - Para proyectar la propagación futura (+24h, +48h, +72h), encender indiscriminadamente toda la huella histórica acumulada del incendio (ej. 30 días acumulados en una sola máscara) produciría un frente de ignición artificialmente masivo, detonando una explosión irreal de celdas en las primeras 24 horas (*flashover numérico* no físico).
   - En su lugar, el simulador predictivo toma como ignición inicial exclusivamente la matriz satelital del último día observado (`matriz_final = np.load(ruta_final)`), que representa la línea de fuego activa real en tiempo presente. El área acumulada consumida con anterioridad permanece registrada como terreno quemado ($0$ combustible activo disponible), logrando que la expansión entre +24h, +48h y +72h sea uniforme, continua y coherente con las tasas reales de propagación observadas en campo.

10. **Decisión 10: Centralización del Pipeline Satelital y Deprecación de Scripts Redundantes:**
    - Se eliminó el script prototipo preliminar `ver_mapa_incendio.py`, consolidando todo el preprocesamiento de la base de datos de anomalías térmicas de la NASA (lectura GeoDataFrame, recorte espacial de Corrientes, rasterización binaria a $256 \times 256$, dilatación morfológica, filtrado de componentes conexos y exportación de matrices `.npy`) en un único módulo robusto, parametrizable y de alto rendimiento: `ver_mapa_filtrado.py`.

11. **Decisión 11: Dilatación Física Convectiva, Filtrado Multi-Cluster y Box-Counting Directo:**
    - **Dilatación Física Realista (2 iteraciones, $r \approx 3.1\text{ km}$):** Se redujo la dilatación morfológica de 11 iteraciones ($\sim 17\text{ km}$) a 2 iteraciones, modelando con rigor el alcance convectivo de briznas incandescentes (*spotting*) y compensando el radio de muestreo del píxel VIIRS 375m sin distorsionar la geometría real.
    - **Filtrado Multi-Cluster por Masa Crítica ($k \ge 3$ celdas):** Se superó la limitación del cluster único (`argmax`) que borraba focos activos en otros puntos de la provincia. El nuevo algoritmo preserva todos los frentes simultáneos que superen 3 celdas conexas, suprimiendo únicamente el ruido de sensor (píxeles aislados de 1 o 2 celdas).
    - **Dimensión Fractal Directa en Espacios Dispersos:** Se fundamentó matemáticamente el cálculo de Box-Counting directo sobre matrices activas dispersas en $\mathbb{R}^2$ sin forzar erosión morfológica perimétrica, evitando el colapso de frentes delgados y ahorrando más de 2.400 operaciones de erosión por corrida en el AG.

---

### 3.8. Fundamentación Científica y Operativa de los Horizontes Predictivos (24h, 48h, 72h)

La extensión del sistema predictivo a los tres horizontes de **$+24\text{ horas}$ (30 pasos)**, **$+48\text{ horas}$ (60 pasos)** y **$+72\text{ horas}$ (90 pasos)** responde a una fundamentación rigurosa desde la física atmosférica, la gestión de catástrofes y la metodología de publicación científica:

#### 1. Comparativa de Propósitos Operativos y Niveles de Mando

| Horizonte Temporal | Pasos del AC | Propósito Operativo | Nivel de Mando / Usuarios Clave | Fidelidad Física y Fenomenológica |
| :--- | :--- | :--- | :--- | :--- |
| **$+24\text{ Horas}$** (Día 1) | $+30$ ciclos | **Táctico Inmediato** | Brigadistas, bomberos y jefes de cuadrilla en línea de fuego | **Máxima:** La persistencia atmosférica es muy alta. Predicción del frente con alta fidelidad espacial ($\text{IoU}$ máximo). |
| **$+48\text{ Horas}$** (Día 2) | $+60$ ciclos | **Preventivo y de Evacuación** | Defensa Civil, comités de crisis municipal, intendencias | **Media-Alta:** Ventana estándar para movilizar recursos de despliegue lento (cortafuegos con topadoras, evacuación preventiva de parajes y hacienda). |
| **$+72\text{ Horas}$** (Día 3) | $+90$ ciclos | **Estratégico Territorial** | Ministerios provinciales/nacionales, Parques Nacionales (Iberá) | **Envolvente Probabilística:** Alerta estratégica interdepartamental y logística de refuerzos antes de cambios sinópticos de masa de aire. |

#### 2. Justificación Física de la Estacionariedad y Persistencia Atmosférica

En la dinámica de la capa límite atmosférica durante olas de calor y sequías críticas (como la experimentada en Corrientes bajo el fenómeno *La Niña*):
- **Escala $\tau \le 24\text{ h}$ (Alta Estacionariedad):** Los campos de presión barométrica y los gradientes térmicos regionales presentan una correlación temporal $\rho > 0.85$. Las variables microclimáticas inferidas por el Algoritmo Genético $(\vec{\theta} = [v, \alpha, h, c])$ mantienen una validez casi estacionaria, lo que justifica la precisión determinista del frente de avance en este horizonte.
- **Escala $24\text{ h} < \tau \le 48\text{ h}$ (Variabilidad Diurna Convectiva):** Comienzan a incidir los ciclos diurnos de temperatura y brisas locales, aunque el vector macro-dominante de advección regional permanece estable. El autómata celular captura el crecimiento perimétrico acumulado con confiabilidad para la toma de decisiones defensivas.
- **Escala $48\text{ h} < \tau \le 72\text{ h}$ (Límite Sinóptico y Divergencia Caótica):** En escalas superiores a 3 días, la no linealidad atmosférica y el ingreso potencial de frentes fríos o perturbaciones de mesoescala introducen incertidumbre estocástica. Por ende, la predicción a 72 horas no debe interpretarse como una posición micrométrica determinista, sino como un **mapa de riesgo isócrono y envolvente de máxima expansión potencial**.

#### 3. Metodología de Validación Científica para Papers (*Blind Test / Backtesting*)

Para artículos en revistas científicas con referato (Q1/Q2) en el área de ciencias ambientales y computación aplicada, el esquema multi-horizonte permite implementar un riguroso protocolo de **Backtesting ciego**:
1. **Fase de Calibración / Entrenamiento ($T_0 \to T_k$):** El Algoritmo Genético se calibra exclusivamente con las matrices satelitales observadas entre el día inicial $T_0$ y el día base $T_k$ (ej. del 16 al 18 de febrero de 2022). El optimizador infiere el mejor cromosoma microclimático $\vec{\theta}^*$.
2. **Fase de Proyección Ciega (*Blind Prediction*):** A partir de la cicatriz satelital consolidada en $T_k$, el simulador predictivo encadena la propagación continua:
   $$M_{\text{base}} (T_k) \xrightarrow{+30\text{ pasos}} M_{24\text{h}} \xrightarrow{+30\text{ pasos}} M_{48\text{h}} \xrightarrow{+30\text{ pasos}} M_{72\text{h}}$$
3. **Contrastación Empírica Satelital Independiente:** Las matrices proyectadas ($M_{24\text{h}}, M_{48\text{h}}, M_{72\text{h}}$) se contrastan contra las observaciones satelitales reales de la NASA correspondientes a $T_{k+1}$, $T_{k+2}$ y $T_{k+3}$ (19, 20 y 21 de febrero), que nunca fueron mostradas al Algoritmo Genético.
4. **Métricas Formales de Rendimiento:**
   - **Índice de Jaccard ($\text{IoU}$):** $\text{IoU}_h = \frac{|M_h \cap M_{\text{real}, h}|}{|M_h \cup M_{\text{real}, h}|}$, evaluando el solapamiento espacial a 24h, 48h y 72h.
   - **Error de Dimensión Fractal:** $\Delta D_h = |D_{\text{real}, h} - D_{\text{pred}, h}|$, evaluando si el autómata celular replica fielmente la textura y rugosidad perimetral del frente.
   - **Acierto de Impacto Territorial Departamental:** Coincidencia entre el ranking de departamentos en alerta predicho por `identificar_departamentos_afectados` y los departamentos donde efectivamente se registraron nuevos focos satelitales en la realidad.

---

## 4. Estructura Modular y Documentación Técnica Detallada (docs/files/)

Con el objetivo de mantener una arquitectura de software limpia, desacoplada y de fácil mantenimiento, la documentación técnica detallada de cada módulo se encuentra organizada en subcarpetas dedicadas dentro del directorio [`docs/files/`](files/).

Cada módulo dispone de dos documentos especializados:
1. **`<modulo>.md`:** Explica la fundamentación teórica, decisiones de diseño, flujo de datos, librerías involucradas y arquitectura del archivo.
2. **`functions.md`:** Catálogo técnico exhaustivo con la firma completa de cada función o bloque de ejecución, parámetros de entrada, valores de retorno, efectos secundarios y casos de uso.

A continuación se indexan los 9 componentes del sistema:

| Módulo | Código Fuente | Documento de Arquitectura | Catálogo de Funciones | Responsabilidad Principal |
| :--- | :--- | :--- | :--- | :--- |
| **`ver_mapa_filtrado`** | [`ver_mapa_filtrado.py`](../ver_mapa_filtrado.py) | [Arquitectura del Módulo](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | [Funciones de Ingestión](files/ver_mapa_filtrado/functions.md) | Ingestión satelital NASA FIRMS, recorte regional, rasterización $256 \times 256$, dilatación física (2 iteraciones, $\sim 3.1\text{ km}$) y filtrado multi-cluster por masa crítica ($k \ge 3$ celdas). |
| **`calcular_dimension_fractal`** | [`calcular_dimension_fractal.py`](../calcular_dimension_fractal.py) | [Fundamentación Matemática](files/calcular_dimension_fractal/calcular_dimension_fractal.md) | [Funciones Fractales](files/calcular_dimension_fractal/functions.md) | Extracción de perímetros con fallback defensivo, Box-Counting logarítmico y cálculo directo de la Dimensión Fractal ($D$) para frentes dispersos. |
| **`automata_celular`** | [`automata_celular.py`](../automata_celular.py) | [Dinámica de Propagación](files/automata_celular/automata_celular.md) | [Funciones del Autómata](files/automata_celular/functions.md) | Simulación estocástica 2D en vecindad de Moore, ecuaciones físicas de viento/humedad/combustible y evolución multietapa continua. |
| **`algoritmo_genetico`** | [`algoritmo_genetico.py`](../algoritmo_genetico.py) | [Optimización Inversa](files/algoritmo_genetico/algoritmo_genetico.md) | [Funciones Genéticas](files/algoritmo_genetico/functions.md) | Algoritmo bioinspirado multiobjetivo (Fitness híbrido $0.5\,\text{Fractal} + 0.5\,\text{IoU}$), operadores genéticos y paralelismo multi-core. |
| **`simulador_predictivo`** | [`simulador_predictivo.py`](../simulador_predictivo.py) | [Orquestación Predictiva](files/simulador_predictivo/simulador_predictivo.md) | [Funciones Predictivas](files/simulador_predictivo/functions.md) | Proyección preventiva multi-horizonte (+24h, +48h, +72h), codificación de riesgo isócrono y generación de figuras analíticas. |
| **`visualizador_corrientes`** | [`visualizador_corrientes.py`](../visualizador_corrientes.py) | [Motor GIS Corrientes](files/visualizador_corrientes/visualizador_corrientes.md) | [Funciones Cartográficas](files/visualizador_corrientes/functions.md) | Cartografía departamental, uniones espaciales (`sjoin`), Data URIs Base64, mapas estáticos multipanel (300 DPI) y visor Folium. |
| **`visualizador_argentina`** | [`visualizador_argentina.py`](../visualizador_argentina.py) | [Motor GIS Nacional](files/visualizador_argentina/visualizador_argentina.md) | [Funciones Nacionales](files/visualizador_argentina/functions.md) | Contexto nacional/regional, simplificación topológica vectorial provincial, mapas estáticos y visor interactivo Folium de Argentina. |
| **`procesar_incendio`** | [`procesar_incendio.py`](../procesar_incendio.py) | [Auditoría Satelital](files/procesar_incendio/procesar_incendio.md) | [Bloques de Ejecución](files/procesar_incendio/functions.md) | Script procedural de análisis preliminar VIIRS, detección del día pico del desastre y exportación tabular CSV. |
| **`main`** | [`main.py`](../main.py) | [Pipeline del Sistema](files/main/main.md) | [Función Main](files/main/functions.md) | Entrypoint interactivo CLI, validación de fechas de usuario y orquestación integral de las cuatro fases del sistema. |

---

## 5. Tabla Resumen de Funciones

La siguiente tabla resume todas las funciones y componentes de procesamiento del sistema. Cada función dispone de un **hipervínculo directo a su especificación técnica completa** en [`docs/files/`](files/):

| # | Función | Archivo | Parámetros Clave | Retorno | Utilizado en |
| :-- | :--- | :--- | :--- | :--- | :--- |
| 1 | [`obtener_df_completo`](files/ver_mapa_filtrado/functions.md#obtener_df_completo) | [`ver_mapa_filtrado.py`](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | Ninguno (usa caché global) | `geopandas.GeoDataFrame` | `ver_mapa_filtrado.py` |
| 2 | [`procesar_una_fecha`](files/ver_mapa_filtrado/functions.md#procesar_una_fecha) | [`ver_mapa_filtrado.py`](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | `fecha, df_fuente, verbose` | Ruta `.npy` / `None` | `ver_mapa_filtrado.py`, `main.py` |
| 3 | [`procesar_rango_fechas`](files/ver_mapa_filtrado/functions.md#procesar_rango_fechas) | [`ver_mapa_filtrado.py`](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | `fecha_inicio, fecha_fin` | `list[(fecha, ruta)]` | `main.py` |
| 4 | [`procesar_fecha`](files/ver_mapa_filtrado/functions.md#procesar_fecha) | [`ver_mapa_filtrado.py`](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | `fecha_elegida` | Ruta `.npy` / `None` | `main.py`, CLI interactivo |
| 5 | [`extraer_perimetro`](files/calcular_dimension_fractal/functions.md#extraer_perimetro) | [`calcular_dimension_fractal.py`](files/calcular_dimension_fractal/calcular_dimension_fractal.md) | `matriz_binaria` | `np.ndarray` (borde morfológico con fallback) | `calcular_dimension_fractal.py` |
| 6 | [`calcular_box_counting`](files/calcular_dimension_fractal/functions.md#calcular_box_counting) | [`calcular_dimension_fractal.py`](files/calcular_dimension_fractal/calcular_dimension_fractal.md) | `matriz_perimetro` | `(D, x, y, sizes, counts)` | `calcular_dimension_fractal.py`, `algoritmo_genetico.py` |
| 7 | [`calcular_dimension_fractal_directa`](files/calcular_dimension_fractal/functions.md#calcular_dimension_fractal_directa) | [`calcular_dimension_fractal.py`](files/calcular_dimension_fractal/calcular_dimension_fractal.md) | `matriz_binaria` | `float` ($D \in [1.0, 2.0]$) | `algoritmo_genetico.py`, evaluación rápida |
| 8 | [`_avanzar_pasos_AC`](files/automata_celular/functions.md#_avanzar_pasos_AC) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `grilla, v, dir, hum, comb, steps` | `np.ndarray` | `automata_celular.py`, `algoritmo_genetico.py` |
| 9 | [`simular_incendio_AC`](files/automata_celular/functions.md#simular_incendio_AC) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `v, dir, hum, comb, steps, grilla_ini` | `(grilla, matriz_binaria)` | `automata_celular.py`, `algoritmo_genetico.py`, `simulador_predictivo.py` |
| 10 | [`simular_evolucion_multietapa`](files/automata_celular/functions.md#simular_evolucion_multietapa) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `v, dir, hum, comb, grilla_ini, pasos_dia, etapas` | `(grilla, list[matrices])` | `automata_celular.py`, `simulador_predictivo.py` |
| 11 | [`cargar_datos_serie_temporal`](files/algoritmo_genetico/functions.md#cargar_datos_serie_temporal) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `entradas` | `list[dict]` | `algoritmo_genetico.py` |
| 12 | [`generar_individuo`](files/algoritmo_genetico/functions.md#generar_individuo) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | Ninguno | `[v, dir, hum, comb]` | `algoritmo_genetico.py` |
| 13 | [`evaluar_fitness_multitemporal`](files/algoritmo_genetico/functions.md#evaluar_fitness_multitemporal) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `individuo, datos_serie, pasos_por_dia, n_sims` | `float` ($[0, 1]$) | `algoritmo_genetico.py` |
| 14 | [`_evaluar_individuo_worker`](files/algoritmo_genetico/functions.md#_evaluar_individuo_worker) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `args` | `(individuo, fitness)` | `algoritmo_genetico.py` (`Pool.imap`) |
| 15 | [`cruzar`](files/algoritmo_genetico/functions.md#cruzar) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `padre1, padre2` | `(hijo1, hijo2)` | `algoritmo_genetico.py` |
| 16 | [`mutar`](files/algoritmo_genetico/functions.md#mutar) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `individuo` | `individuo` | `algoritmo_genetico.py` |
| 17 | [`seleccion_torneo`](files/algoritmo_genetico/functions.md#seleccion_torneo) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `fitness_poblacion, k=3` | `individuo_ganador` | `algoritmo_genetico.py` |
| 18 | [`guardar_grafico_fitness`](files/algoritmo_genetico/functions.md#guardar_grafico_fitness) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `historial, ruta_salida` | `None` (guarda PNG) | `algoritmo_genetico.py` |
| 19 | [`guardar_csv_resultados`](files/algoritmo_genetico/functions.md#guardar_csv_resultados) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `historial, mejor_ind, mejor_fit` | `None` (guarda CSV) | `algoritmo_genetico.py` |
| 20 | [`ejecutar_algoritmo_genetico`](files/algoritmo_genetico/functions.md#ejecutar_algoritmo_genetico) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `entradas_matrices` | `mejor_individuo` | `main.py`, `algoritmo_genetico.py` |
| 21 | [`ejecutar_prediccion`](files/simulador_predictivo/functions.md#ejecutar_prediccion) | [`simulador_predictivo.py`](files/simulador_predictivo/simulador_predictivo.md) | `datos_entrada, variables, pasos_por_dia` | `mapa_riesgo` (`np.ndarray`) | `main.py`, `simulador_predictivo.py` |
| 22 | [`cargar_geometria_corrientes`](files/visualizador_corrientes/functions.md#cargar_geometria_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | Ninguno | `GeoDataFrame` | `visualizador_corrientes.py` |
| 23 | [`cargar_mascara_provincia`](files/visualizador_corrientes/functions.md#cargar_mascara_provincia) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `tamano=256` | `np.ndarray` (bool) | `visualizador_corrientes.py` |
| 24 | [`matriz_a_coordenadas`](files/visualizador_corrientes/functions.md#matriz_a_coordenadas) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `row, col, tamano, lat_bounds, lon_bounds` | `(lat, lon)` | `visualizador_corrientes.py` |
| 25 | [`identificar_departamentos_afectados`](files/visualizador_corrientes/functions.md#identificar_departamentos_afectados) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `matriz_fuego, gdf_corrientes, tamano, ...` | `list[dict]` (ranking) | `visualizador_corrientes.py` |
| 26 | [`_crear_data_uri_rgba`](files/visualizador_corrientes/functions.md#_crear_data_uri_rgba) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `matriz, color_rgb, alfa, mascara_prov` | `str` (Data URI Base64) | `visualizador_corrientes.py` |
| 27 | [`generar_mapa_estatico_corrientes`](files/visualizador_corrientes/functions.md#generar_mapa_estatico_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta PNG 4 paneles) | `visualizador_corrientes.py` |
| 28 | [`generar_mapa_interactivo_corrientes`](files/visualizador_corrientes/functions.md#generar_mapa_interactivo_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta HTML Folium) | `visualizador_corrientes.py` |
| 29 | [`generar_mapas_corrientes`](files/visualizador_corrientes/functions.md#generar_mapas_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `dict` (rutas y desglose) | `simulador_predictivo.py` |
| 30 | [`cargar_geometria_argentina`](files/visualizador_argentina/functions.md#cargar_geometria_argentina) | [`visualizador_argentina.py`](files/visualizador_argentina/visualizador_argentina.md) | Ninguno | `GeoDataFrame` | `visualizador_argentina.py` |
| 31 | [`_crear_data_uri_rgba_argentina`](files/visualizador_argentina/functions.md#_crear_data_uri_rgba_argentina) | [`visualizador_argentina.py`](files/visualizador_argentina/visualizador_argentina.md) | `matriz, color_rgb, alfa` | `str` (Data URI Base64) | `visualizador_argentina.py` |
| 32 | [`generar_mapa_estatico_argentina`](files/visualizador_argentina/functions.md#generar_mapa_estatico_argentina) | [`visualizador_argentina.py`](files/visualizador_argentina/visualizador_argentina.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta PNG 4 paneles) | `visualizador_argentina.py` |
| 33 | [`generar_mapa_interactivo_argentina`](files/visualizador_argentina/functions.md#generar_mapa_interactivo_argentina) | [`visualizador_argentina.py`](files/visualizador_argentina/visualizador_argentina.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta HTML Folium) | `visualizador_argentina.py` |
| 34 | [`generar_mapas_argentina`](files/visualizador_argentina/functions.md#generar_mapas_argentina) | [`visualizador_argentina.py`](files/visualizador_argentina/visualizador_argentina.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `dict` (rutas de mapas) | `simulador_predictivo.py` |
| 35 | [`main`](files/main/functions.md#main) | [`main.py`](files/main/main.md) | Ninguno | `None` | `main.py` (Entrypoint CLI) |
| 36 | [`Bloques 1 a 4 (Script)`](files/procesar_incendio/functions.md) | [`procesar_incendio.py`](files/procesar_incendio/procesar_incendio.md) | Archivo JSON crudo, umbrales FRP | `incendios_dia_pico.csv` | Diagnóstico satelital exploratorio |

---

## 6. Guía de Ejecución Rápida y Salidas Generadas

1. **Ejecución estándar interactiva:**
   ```bash
   python main.py
   ```
2. **Ingreso de parámetros de prueba recomendados (Megaincendio de Corrientes 2022):**
   - **Fecha Inicial:** `2022-02-17`
   - **Fecha Final:** `2022-02-19` (o presionar Enter para analizar solo el día inicial)
3. **Archivos de salida generados en la carpeta `output/`:**
   - **📊 `output/mapa_riesgo_predictivo.png`:** Matriz comparativa de riesgo isócrono del simulador (4 paneles en alta resolución a 300 DPI: Foco Base Observado, Predicción +24h Táctica, Predicción +48h Preventiva y Predicción +72h Estratégica con código isócrono acumulativo).
   - **📍 `output/mapa_corrientes_prediccion.png`:** Mapa GIS de alta resolución (300 DPI) con 4 paneles horizontales georreferenciados sobre los 25 departamentos de Corrientes, con rótulos de texto protegidos por halo blanco (`path_effects`).
   - **🌐 `output/mapa_corrientes_interactivo.html`:** Mapa web interactivo en Folium de Corrientes con selector de capas (CartoDB Positron, OpenStreetMap y Satélite Esri World Imagery), división departamental oficial con tooltips interactivos, y capas raster conmutables independientes en Base64 para cada horizonte temporal (+24h, +48h, +72h e Isócronas).
   - **🇦🇷 `output/mapa_argentina_prediccion.png`:** Mapa cartográfico GIS (300 DPI) con 4 paneles horizontales análogos a Corrientes sobre el territorio completo de la República Argentina, manteniendo la misma vista nacional sin distorsiones de escala ni encuadre.
   - **🌐 `output/mapa_argentina_interactivo.html`:** Mapa web interactivo en Folium de la República Argentina con división provincial oficial simplificada, capas satelitales, minimapa y leyenda climatológica flotante.
   - **💾 `output/matriz_objetivo_limpia_AAAA-MM-DD.npy`:** Matrices binarias rasterizadas y filtradas de la base de la NASA.
   - **🖼️ `output/silueta_fractal_limpia_AAAA-MM-DD.png`:** Siluetas fractales continuas del cuerpo principal de fuego.


