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
        A["JSON NASA FIRMS (VIIRS/MODIS)"] --> B["ver_mapa_filtrado.py\n(Recorte Corrientes + Dilatación Física 1 iter ~1.6 km)"]
        B --> C["Serie de Matrices Binarias 256x256 (.npy)\n[T0, T1, ..., Tk]"]
    end

    subgraph FASE 2: Optimización Inversa Multitemporal
        C --> D["algoritmo_genetico.py\n(Población de Cromosomas Climáticos)"]
        D --> E["calcular_dimension_fractal.py\n(Box-Counting Directo D_sat)"]
        D --> F["automata_celular.py\n(Simulación Estocástica AC)"]
        F --> G["Fitness Multitemporal Híbrido\nPromedio(0.5*Fractal + 0.5*F1_Espacial)"]
        G --> D
    end

    subgraph FASE 3: Simulación Preventiva
        D --> H["Mejores Variables Microclimáticas\n(Viento, Dirección, Humedad, Combustible)"]
        C --> I["simulador_predictivo.py"]
        H --> I
        I --> J["Mapa de Riesgo Predictivo Multipanel (.png)"]
    end

    subgraph FASE 4: Transposición Cartográfica Territorial (Corrientes)
        I --> K["visualizador_corrientes.py\n(Georreferenciación Departamental)"]
        L["GeoJSON 25 Departamentos de Corrientes"] --> K
        K --> M["Mapa GIS Estático de Corrientes\noutput/mapa_corrientes_prediccion.png"]
        K --> N["Mapa Web Interactivo Folium Corrientes\noutput/mapa_corrientes_interactivo.html"]
        K --> O["Ranking de Departamentos Afectados"]
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

#### 3.5.1. Definición Formal del Paso de Simulación ($\Delta t$ y Discretización Espacio-Temporal)

Un **paso de simulación** (o iteración de reloj del Autómata Celular) es la unidad discreta fundamental de avance temporal y dinámico del frente de fuego en el modelo. Se define formalmente bajo tres dimensiones interconectadas:

1. **Equivalencia Temporal ($\Delta t$):**
   El sistema calibra la escala diaria mediante la constante `PASOS_POR_DIA = 30`. Por lo tanto, cada paso discreto representa exactamente:
   $$\Delta t = \frac{24\text{ horas}}{30\text{ pasos}} = 0.8\text{ horas} = 48\text{ minutos}$$
   Esto significa que cada ciclo de reloj del simulador modela la propagación acumulada del fuego a lo largo de un período de 48 minutos de tiempo físico real.

2. **Equivalencia Espacial y Velocidad Teórica del Frente:**
   Dado que la grilla de $256 \times 256$ sobre la provincia de Corrientes posee una resolución de celda de $\Delta x \approx 1.57\text{ km}$, el salto de ignición hacia una celda contigua de la vecindad de Moore en un único paso de simulación representa una tasa máxima de propagación lineal de:
   $$v_{\text{frente}} \approx \frac{1.57\text{ km}}{0.8\text{ h}} \approx 1.96\text{ km/h}$$
   Esta tasa es plenamente consistente con la velocidad observada de avance de frentes de fuego en pajonales, pastizales secos y malezales bajo vientos moderados a fuertes (15 a 40 km/h).

3. **Ciclo de Vida Algorítmico en 1 Paso ($t \to t + 1$):**
   En cada paso de simulación ocurren secuencialmente tres procesos estocásticos atómicos:
   - **Identificación del Frente Activo:** Mediante indexación vectorial (`np.where(grilla == 1)`), se localizan las celdas en combustión activa en el instante $t$.
   - **Consunción a Cenizas:** Dichas celdas activas consumen íntegramente su biomasa disponible y pasan de manera irreversible a cenizas inertes (`grilla = 2`), garantizando que no puedan volver a quemarse.
   - **Contagio Estocástico Anisótropo:** Cada celda que estuvo activa intenta propagar el fuego a sus 8 vecinos circundantes en Estado 0 (intactos). Para cada dirección espacial $(\Delta y, \Delta x)$, se calcula la probabilidad compuesta $P_{\text{ignición}} = \min(P_{\text{base}} \cdot f_{\text{viento}}, 0.95)$. Si una variable aleatoria uniforme $U(0, 1) < P_{\text{ignición}}$, la celda vecina se enciende pasando a Estado 1 para el paso $t+1$.

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
   - Archivos vectoriales voluminosos (`departamentos_corrientes.json`, $\sim 855\text{ KB}$) y matrices intermedias binarias (`.npy`) están excluidos de Git. `visualizador_corrientes.py` descarga, optimiza y almacena en caché local de forma transparente los recursos faltantes mediante mecanismos de resiliencia ante errores de red.

6. **Decisión 6: Visualización Cartográfica Provincial en 4 Paneles Multi-Horizonte (Corrientes @ 300 DPI):**
   - `visualizador_corrientes.py` estructura su salida estática en **cuatro paneles complementarios de alta resolución (300 DPI)** georreferenciados sobre los 25 departamentos de la provincia de Corrientes:
     - **Panel 1 (Foco Base Observado en $T_{\text{final}}$):** Muestra el foco satelital base consolidado al final del período de observación (azul noche `#2c3e50`), sin rojo de predicción, permitiendo visualizar la cicatriz real de partida.
     - **Panel 2 (Predicción Táctica a $+24\text{ Horas}$ / +30 ciclos):** Frente de avance táctico en ámbar (`#f39c12`) para cuadrillas y brigadistas en terreno.
     - **Panel 3 (Predicción Preventiva a $+48\text{ Horas}$ / +60 ciclos):** Expansión preventiva en naranja (`#e67e22`) para evacuación y maquinaria pesada.
     - **Panel 4 (Predicción Estratégica a $+72\text{ Horas}$ e Isócronas / +90 ciclos):** Expansión estratégica en rojo (`#e74c3c`) e isócronas sobre divisiones político-administrativas.

7. **Decisión 7: Enfoque Territorial Exclusivo en la Provincia de Corrientes:**
   - Para maximizar la fidelidad eco-física del modelo, el sistema delimita estrictamente su alcance geográfico a la provincia de Corrientes ($88.886\text{ km}^2$), descartando proyecciones a nivel nacional que diluían la resolución por píxel. La grilla $256 \times 256$ concentra toda su potencia en el macrosistema Iberá ($\approx 1.57\text{ km/píxel}$), permitiendo un análisis departamental de alta precisión para Defensa Civil provincial.

8. **Decisión 8: Estructura Limpia de Almacenamiento en `output/` (`npy/` y `siluetas/`):**
   - Para evitar la polución de la carpeta raíz `output/` con decenas de matrices intermedias, los productos generados se organizan de forma limpia:
     - `output/npy/`: Almacena todas las matrices binarias y continuas (`matriz_objetivo_limpia_*.npy`, `matriz_fractal_recorte_*.npy`).
     - `output/siluetas/`: Almacena las figuras PNG de las siluetas fractales limpias (`silueta_fractal_limpia_*.png`).
     - `output/`: Reserva el nivel superior exclusivamente para los productos finales de alto valor (mapas de riesgo predictivo, mapas GIS y visores interactivos de Corrientes, curvas de fitness y reportes CSV).

9. **Decisión 9: Punto de Partida de Expansión en las Celdas de Calor del Día Inicial ($T_0$):**
   - El autómata celular y el algoritmo genético toman invariablemente como estado inicial (`grilla_inicial`) la matriz binaria real de celdas activas observadas en el día de inicio $T_0$. A partir de estos focos reales, el autómata propaga el fuego paso a paso buscando reproducir la geometría observada en los días sucesivos ($T_1, \dots, T_k$), erradicando la antigua inicialización en un único punto baricéntrico arbitrario.

10. **Decisión 10: Centralización del Pipeline Satelital y Deprecación de Scripts Redundantes:**
    - Se consolidó todo el preprocesamiento de la base de datos de anomalías térmicas de la NASA (lectura GeoDataFrame, recorte espacial de Corrientes, rasterización binaria a $256 \times 256$, dilatación morfológica, filtrado de componentes conexos y exportación de matrices `.npy`) en un único módulo robusto, parametrizable y de alto rendimiento: `ver_mapa_filtrado.py`.

11. **Decisión 11: Dilatación Física Convectiva Calibrada (1 iteración, $r \approx 1.57\text{ km}$) y Preservación Multicluster:**
    - **Dilatación Física Realista (1 iteración, $r \approx 1.57\text{ km}$):** Se calibró la dilatación morfológica a 1 única iteración ($3 \times 3$, cruz compacta de 5 celdas por foco), modelando con rigor el radio primario de transporte de pavesas (*spotting*) en pastizales y compensando la discretización de la grilla sin sobredimensionar artificialmente las cicatrices ni puentear canales hídricos angostos del Iberá. La dimensión fractal resultante ($D \approx 1.26 - 1.40$) converge al rango canónico reportado en la literatura científica de incendios forestales.
    - **Preservación Integral Multi-Cluster sin Heurísticas Redundantes:** Se eliminó la antigua limitación del cluster único (`argmax`) que borraba focos en el resto de la provincia. Asimismo, se demostró que un filtro de corte de cluster conexo post-dilatación resultaba redundante (un *no-op* absoluto, pues todo punto dilatado supera las 5 celdas), simplificando el pipeline para que la dilatación física directa preserve el 100% de las observaciones térmicas validadas por NASA FIRMS.
    - **Dimensión Fractal Directa en Espacios Dispersos:** Se fundamentó matemáticamente el cálculo de Box-Counting directo sobre matrices activas dispersas en $\mathbb{R}^2$ sin forzar erosión morfológica perimétrica, evitando el colapso de frentes delgados y ahorrando más de 2.400 operaciones de erosión por corrida en el AG.

12. **Decisión 12: Heterogeneidad Espacial Biofísica y Capa Raster de Combustible (`capa_biomasa.py`):**
    - En simulaciones previas, el combustible vegetal se modelaba como un escalar global homogéneo ($c \in [0.1, 1.0]$) para todo el territorio correntino. Esto imposibilitaba que el autómata celular reconociera cuerpos de agua continentales (ríos, lagunas y esteros profundos del Iberá) como barreras cortafuego naturales infranqueables, ni capturara la aceleración del fuego en plantaciones forestales resinosas.
    - Para resolver esta limitación biofísica (Tarea T2.1), se desarrolló el módulo `capa_biomasa.py`, el cual descarga capas vectoriales oficiales del Instituto Geográfico Nacional (IGN) vía WFS (`EPSG:4326`) y las discretiza en una grilla de $256 \times 256$ clasificando el terreno en cuatro categorías biofísicas:
      1. *Cuerpos de agua y esteros profundos:* $C = 0.0$ (barrera cortafuego natural absoluta, $P_{\text{ignición}} = 0$).
      2. *Bañados y vegetación hidrófila / pajonales:* $C = 0.2$ (resistencia hídrica elevada).
      3. *Pastizales y sabanas:* $C = 0.6$ (matriz biofísica de propagación base).
      4. *Plantaciones forestales resinosas (pino/eucalipto):* $C = 1.0$ (máxima inflamabilidad y aceleración de copa).
      - *Límites exteriores / ríos limítrofes Paraná y Uruguay:* $C = 0.0$ (condición Dirichlet incombustible).
    - La rasterización optimizada con `shapely.contains_xy` evalúa los $65.536$ puntos en $21\text{ ms}$, persistiendo las matrices binarias en `data/mapa_combustible_256.npy` y `data/categorias_cobertura_256.npy`. Esto garantiza tiempos de carga instantáneos ($< 1\text{ ms}$) y preserva la capacidad de ejecución determinista y offline tanto en el Autómata Celular como en el Algoritmo Genético.

13. **Decisión 13: Reestructuración de la Métrica Espacial: Cobertura Eficiente ($F_1$-Dice) y Balance 50/50 con Dimensión Fractal:**
    - Se identificó que la métrica de IoU estricto píxel por píxel imponía una patología matemática de "doble penalización": al expandirse el frente simulado a lo largo de 30 pasos diarios para alcanzar los focos futuros de $T+1$, el área total simulada crecía agrandando el denominador (Unión) y aplastando el IoU a $\approx 0.19$, estancando el fitness híbrido en $\approx 0.570$ a pesar de cubrir exitosamente más del $96\%$ de los focos reales.
    - Se reemplazó el IoU por la **Cobertura Eficiente ($F_1$-Score / Coeficiente de Sørensen-Dice)**:
      $$\text{Score}_{\text{espacial}} = \frac{2 \cdot |M_{\text{real}} \cap M_{\text{sim}}|}{|M_{\text{real}}| + |M_{\text{sim}}|}$$
      Esta formulación premia directamente el alcance sobre los puntos de calor reales de la NASA ($\text{Recall}$) al tiempo que penaliza armónicamente la dispersión indiscriminada o desborde inútil ($\text{Precision}$).
    - Se ratificó el balance estricto **50/50** entre la Dimensión Fractal ($F_{\text{fractal}}$) y la Cobertura Espacial ($F_1$), logrando que el fitness alcance valores superiores a $0.80 - 0.85$ en soluciones convergentes. Para un análisis teórico, empírico y experimental exhaustivo, consultar el documento monográfico: [**`docs/Reestructuracion IoU.md`**](Reestructuracion%20IoU.md).

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
| **`ver_mapa_filtrado`** | [`ver_mapa_filtrado.py`](../ver_mapa_filtrado.py) | [Arquitectura del Módulo](files/ver_mapa_filtrado/ver_mapa_filtrado.md) | [Funciones de Ingestión](files/ver_mapa_filtrado/functions.md) | Ingestión satelital NASA FIRMS, recorte regional Corrientes, rasterización $256 \times 256$ y dilatación física calibrada (1 iteración, $r \approx 1.57\text{ km}$) con preservación integral multicluster. |
| **`calcular_dimension_fractal`** | [`calcular_dimension_fractal.py`](../calcular_dimension_fractal.py) | [Fundamentación Matemática](files/calcular_dimension_fractal/calcular_dimension_fractal.md) | [Funciones Fractales](files/calcular_dimension_fractal/functions.md) | Extracción de perímetros con fallback defensivo, Box-Counting logarítmico y cálculo directo de la Dimensión Fractal ($D$) para frentes dispersos (T1.5). |
| **`capa_biomasa`** | [`capa_biomasa.py`](../capa_biomasa.py) | [Heterogeneidad Espacial](files/capa_biomasa/capa_biomasa.md) | [Funciones de Biomasa](files/capa_biomasa/functions.md) | Capa raster de biomasa y cobertura real IGN (T2.1), 4 categorías biofísicas ($C \in [0.0, 1.0]$), barreras naturales de agua y mapa cartográfico. |
| **`automata_celular`** | [`automata_celular.py`](../automata_celular.py) | [Dinámica de Propagación](files/automata_celular/automata_celular.md) | [Funciones del Autómata](files/automata_celular/functions.md) | Simulación estocástica 2D en vecindad de Moore, ecuaciones físicas de viento/humedad/combustible espacializado y evolución multietapa continua. |
| **`algoritmo_genetico`** | [`algoritmo_genetico.py`](../algoritmo_genetico.py) | [Optimización Inversa](files/algoritmo_genetico/algoritmo_genetico.md) | [Funciones Genéticas](files/algoritmo_genetico/functions.md) | Algoritmo bioinspirado multiobjetivo (Fitness híbrido $0.5\,\text{Fractal} + 0.5\,\text{F}_1\text{-Dice}$), operadores genéticos y paralelismo multi-core. |
| **`simulador_predictivo`** | [`simulador_predictivo.py`](../simulador_predictivo.py) | [Orquestación Predictiva](files/simulador_predictivo/simulador_predictivo.md) | [Funciones Predictivas](files/simulador_predictivo/functions.md) | Proyección preventiva multi-horizonte (+24h, +48h, +72h), codificación de riesgo isócrono y generación de figuras analíticas. |
| **`visualizador_corrientes`** | [`visualizador_corrientes.py`](../visualizador_corrientes.py) | [Motor GIS Corrientes](files/visualizador_corrientes/visualizador_corrientes.md) | [Funciones Cartográficas](files/visualizador_corrientes/functions.md) | Cartografía departamental, uniones espaciales (`sjoin`), Data URIs Base64, mapas estáticos multipanel (300 DPI) y visor Folium. |
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
| 8 | [`descargar_capas_ign_si_faltan`](files/capa_biomasa/functions.md#descargar_capas_ign_si_faltan) | [`capa_biomasa.py`](files/capa_biomasa/capa_biomasa.md) | Ninguno | `None` (descarga GeoJSONs IGN) | `capa_biomasa.py` |
| 9 | [`cargar_o_generar_mapa_combustible`](files/capa_biomasa/functions.md#cargar_o_generar_mapa_combustible) | [`capa_biomasa.py`](files/capa_biomasa/capa_biomasa.md) | `tamano=256, recalcular=False` | `(mapa_c, cat_c)` (`np.ndarray`) | `capa_biomasa.py` |
| 10 | [`obtener_mapa_combustible`](files/capa_biomasa/functions.md#obtener_mapa_combustible) | [`capa_biomasa.py`](files/capa_biomasa/capa_biomasa.md) | `tamano=256` | `np.ndarray` float ($C \in [0.0, 1.0]$) | `automata_celular.py`, `algoritmo_genetico.py` |
| 11 | [`generar_mapa_cobertura_grafico`](files/capa_biomasa/functions.md#generar_mapa_cobertura_grafico) | [`capa_biomasa.py`](files/capa_biomasa/capa_biomasa.md) | `tamano=256, ruta_salida` | `str` (ruta PNG 300 DPI) | `simulador_predictivo.py`, CLI |
| 12 | [`_avanzar_pasos_AC`](files/automata_celular/functions.md#_avanzar_pasos_AC) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `grilla, v, dir, hum, comb, steps, mapa_comb` | `np.ndarray` | `automata_celular.py`, `algoritmo_genetico.py` |
| 13 | [`simular_incendio_AC`](files/automata_celular/functions.md#simular_incendio_AC) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `v, dir, hum, comb, steps, grilla_ini, mapa_comb` | `(grilla, matriz_binaria)` | `automata_celular.py`, `algoritmo_genetico.py`, `simulador_predictivo.py` |
| 14 | [`simular_evolucion_multietapa`](files/automata_celular/functions.md#simular_evolucion_multietapa) | [`automata_celular.py`](files/automata_celular/automata_celular.md) | `v, dir, hum, comb, grilla_ini, pasos_dia, etapas, mapa_comb` | `(grilla, list[matrices])` | `automata_celular.py`, `simulador_predictivo.py` |
| 15 | [`cargar_datos_serie_temporal`](files/algoritmo_genetico/functions.md#cargar_datos_serie_temporal) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `entradas` | `list[dict]` | `algoritmo_genetico.py` |
| 16 | [`generar_individuo`](files/algoritmo_genetico/functions.md#generar_individuo) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | Ninguno | `[v, dir, hum, comb]` | `algoritmo_genetico.py` |
| 17 | [`evaluar_fitness_multitemporal`](files/algoritmo_genetico/functions.md#evaluar_fitness_multitemporal) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `individuo, datos_serie, pasos_por_dia, n_sims, mapa_comb` | `float` ($[0, 1]$) | `algoritmo_genetico.py` |
| 18 | [`_evaluar_individuo_worker`](files/algoritmo_genetico/functions.md#_evaluar_individuo_worker) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `args` | `(individuo, fitness)` | `algoritmo_genetico.py` (`Pool.imap`) |
| 19 | [`cruzar`](files/algoritmo_genetico/functions.md#cruzar) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `padre1, padre2` | `(hijo1, hijo2)` | `algoritmo_genetico.py` |
| 20 | [`mutar`](files/algoritmo_genetico/functions.md#mutar) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `individuo` | `individuo` | `algoritmo_genetico.py` |
| 21 | [`seleccion_torneo`](files/algoritmo_genetico/functions.md#seleccion_torneo) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `fitness_poblacion, k=3` | `individuo_ganador` | `algoritmo_genetico.py` |
| 22 | [`guardar_grafico_fitness`](files/algoritmo_genetico/functions.md#guardar_grafico_fitness) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `historial, ruta_salida` | `None` (guarda PNG) | `algoritmo_genetico.py` |
| 23 | [`guardar_csv_resultados`](files/algoritmo_genetico/functions.md#guardar_csv_resultados) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `historial, mejor_ind, mejor_fit` | `None` (guarda CSV) | `algoritmo_genetico.py` |
| 24 | [`ejecutar_algoritmo_genetico`](files/algoritmo_genetico/functions.md#ejecutar_algoritmo_genetico) | [`algoritmo_genetico.py`](files/algoritmo_genetico/algoritmo_genetico.md) | `entradas_matrices` | `mejor_individuo` | `main.py`, `algoritmo_genetico.py` |
| 25 | [`ejecutar_prediccion`](files/simulador_predictivo/functions.md#ejecutar_prediccion) | [`simulador_predictivo.py`](files/simulador_predictivo/simulador_predictivo.md) | `datos_entrada, variables, pasos_por_dia` | `mapa_riesgo` (`np.ndarray`) | `main.py`, `simulador_predictivo.py` |
| 26 | [`cargar_geometria_corrientes`](files/visualizador_corrientes/functions.md#cargar_geometria_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | Ninguno | `GeoDataFrame` | `visualizador_corrientes.py` |
| 27 | [`cargar_mascara_provincia`](files/visualizador_corrientes/functions.md#cargar_mascara_provincia) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `tamano=256` | `np.ndarray` (bool) | `visualizador_corrientes.py` |
| 28 | [`matriz_a_coordenadas`](files/visualizador_corrientes/functions.md#matriz_a_coordenadas) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `row, col, tamano, lat_bounds, lon_bounds` | `(lat, lon)` | `visualizador_corrientes.py` |
| 29 | [`identificar_departamentos_afectados`](files/visualizador_corrientes/functions.md#identificar_departamentos_afectados) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `matriz_fuego, gdf_corrientes, tamano, ...` | `list[dict]` (ranking) | `visualizador_corrientes.py` |
| 30 | [`_crear_data_uri_rgba`](files/visualizador_corrientes/functions.md#_crear_data_uri_rgba) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `matriz, color_rgb, alfa, mascara_prov` | `str` (Data URI Base64) | `visualizador_corrientes.py` |
| 31 | [`generar_mapa_estatico_corrientes`](files/visualizador_corrientes/functions.md#generar_mapa_estatico_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta PNG 4 paneles) | `visualizador_corrientes.py` |
| 32 | [`generar_mapa_interactivo_corrientes`](files/visualizador_corrientes/functions.md#generar_mapa_interactivo_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `str` (ruta HTML Folium) | `visualizador_corrientes.py` |
| 33 | [`generar_mapas_corrientes`](files/visualizador_corrientes/functions.md#generar_mapas_corrientes) | [`visualizador_corrientes.py`](files/visualizador_corrientes/visualizador_corrientes.md) | `m_ini, m_fut, m_riesgo, fechas, clima, pasos, ...` | `dict` (rutas y desglose) | `simulador_predictivo.py` |
| 34 | [`main`](files/main/functions.md#main) | [`main.py`](files/main/main.md) | Ninguno | `None` | `main.py` (Entrypoint CLI) |
| 35 | [`Bloques 1 a 4 (Script)`](files/procesar_incendio/functions.md) | [`procesar_incendio.py`](files/procesar_incendio/procesar_incendio.md) | Archivo JSON crudo, umbrales FRP | `incendios_dia_pico.csv` | Diagnóstico satelital exploratorio |

---

## 6. Guía de Ejecución Rápida y Salidas Generadas

1. **Ejecución estándar interactiva:**
   ```bash
   python main.py
   ```
2. **Ingreso de parámetros de prueba recomendados (Megaincendio de Corrientes 2022):**
   - **Fecha Inicial:** `2022-02-17`
   - **Fecha Final:** `2022-02-19` (o presionar Enter para calibrar automáticamente hacia el día siguiente)
3. **Archivos de salida generados en la carpeta `output/`:**
   - **🌿 `output/mapa_cobertura_combustible.png`:** Mapa cartográfico GIS de alta resolución (300 DPI) con las 4 categorías de biomasa y combustible de Corrientes (IGN Argentina, T2.1), con límites departamentales oficiales y desglose porcentual.
   - **📊 `output/mapa_riesgo_predictivo.png`:** Matriz comparativa de riesgo isócrono del simulador (4 paneles en alta resolución a 300 DPI: Foco Base Observado, Predicción +24h Táctica, Predicción +48h Preventiva y Predicción +72h Estratégica con código isócrono acumulativo).
   - **📍 `output/mapa_corrientes_prediccion.png`:** Mapa GIS de alta resolución (300 DPI) con 4 paneles horizontales georreferenciados sobre los 25 departamentos de Corrientes, con rótulos de texto protegidos por halo blanco (`path_effects`).
   - **🌐 `output/mapa_corrientes_interactivo.html`:** Mapa web interactivo en Folium de Corrientes con selector de capas (CartoDB Positron, OpenStreetMap y Satélite Esri World Imagery), división departamental oficial con tooltips interactivos, y capas raster conmutables independientes en Base64 para cada horizonte temporal (+24h, +48h, +72h e Isócronas).
   - **💾 `output/npy/matriz_objetivo_limpia_AAAA-MM-DD.npy`:** Subcarpeta de matrices binarias rasterizadas y filtradas de la base de la NASA.
   - **🖼️ `output/siluetas/silueta_fractal_limpia_AAAA-MM-DD.png`:** Subcarpeta de siluetas fractales continuas de los frentes de fuego procesados.



