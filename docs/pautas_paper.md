# Pautas para la Redacción del Paper Científico
## Modelado de Propagación de Incendios Forestales mediante Autómatas Celulares, Algoritmos Genéticos y Geometría Fractal

> **Formato objetivo:** Congreso nacional (CACIC / JAIIO / Argencon) · Doble columna · **6 páginas máximo**  
> **Idioma:** Castellano (o inglés si se apunta a revista internacional)  
> **Plantilla recomendada:** IEEE Conference Proceedings (disponible en Overleaf)

---

## 1. Distribución de Páginas Recomendada

| Sección | Páginas estimadas | Prioridad |
|:---|:---:|:---:|
| Título, Autores, Abstract, Palabras Clave | ~0.25 | Obligatoria |
| Introducción y Motivación | ~0.75 | Obligatoria |
| Marco Teórico | ~1.25 | Obligatoria |
| Metodología (AC + AG + Fitness) | ~1.50 | Obligatoria |
| Resultados y Discusión | ~1.25 | Obligatoria |
| Trabajos Relacionados | ~0.50 | Recomendada |
| Conclusión y Trabajos Futuros | ~0.30 | Obligatoria |
| Referencias | ~0.25 | Obligatoria |
| **Total** | **≈ 6.00** | |

> **Regla de oro:** Si alguna sección se extiende, recortar primero los Trabajos Relacionados y luego la Discusión. Nunca recortar Metodología ni Resultados.

---

## 2. Título

**Propuesta principal:**
> *Inferencia de Parámetros Atmosféricos en Incendios Forestales mediante Algoritmos Genéticos, Autómatas Celulares y Geometría Fractal*

**Propuesta alternativa (más técnica, si se apunta a revista):**
> *Inverse Parameter Estimation in Wildfire Spread Simulation via Genetic Algorithms and Fractal Dimension Fitness*

El título debe contener explícitamente las tres columnas metodológicas del trabajo: **AG**, **AC** y **Fractal**. Son los términos que los revisores usarán para indexar y buscar el paper.

---

## 3. Abstract (≈ 150–200 palabras)

El abstract debe responder exactamente cinco preguntas en ese orden:

1. **¿Cuál es el problema?** → Inferir condiciones microclimáticas en incendios activos a partir de datos satelitales.
2. **¿Por qué es difícil?** → Las estaciones meteorológicas son escasas; el problema es un sistema inverso no lineal.
3. **¿Qué proponen?** → Un AG que calibra un AC estocástico con biomasa heterogénea del IGN.
4. **¿Cómo evalúan?** → Función de aptitud híbrida 50/50 (Dimensión Fractal + Sørensen-Dice F1).
5. **¿Qué obtuvieron?** → fitness = 0.7827, viento WSW 6.41 km/h, humedad 23%, Corrientes febrero 2022.

**Lo que NO debe tener el abstract:** citas bibliográficas, siglas sin definir, ecuaciones.

---

## 4. Palabras Clave (5–7 términos)

```
algoritmos genéticos, autómata celular, dimensión fractal, incendios forestales,
optimización inversa, teledetección, Sørensen-Dice
```

Usar términos que aparezcan en los tesauros de IEEE o ACM para maximizar la indexación.

---

## 5. Introducción (~0.75 páginas)

### Qué debe contener:

**5.1 Motivación del problema (2–3 párrafos)**
- El megaincendio de Corrientes 2022: >1.042.514 ha quemadas, 12% del territorio provincial. Citar el informe técnico del INTA Corrientes [10].
- La brecha tecnológica: los modelos de simulación requieren parámetros meteorológicos que en emergencias no están disponibles en tiempo real.
- La oportunidad satelital: NASA FIRMS/VIIRS provee detecciones de focos activos cada 12h con 375 m de resolución, habilitando una formulación inversa del problema.

**5.2 Formulación del problema inverso (1 párrafo)**
- Dado un intervalo de observaciones $O_{t_0}, O_{t_1}$, encontrar el vector $\vec{\theta}^* = (v, \phi, h, c_f)$ tal que la simulación reproduzca la dinámica observada.
- Mencionar que es un problema de optimización en espacio continuo de dimensión 4, no convexo y ruidoso por la estocasticidad del simulador.

**5.3 Contribuciones del trabajo (lista de 3 ítems)**

Presentarlas explícitamente como contribuciones científicas. Ejemplo:
> (i) integración de una capa de biomasa heterogénea oficial (IGN WFS) como condición de borde espacialmente variable del autómata; (ii) sustitución del IoU por el coeficiente de Sørensen-Dice como métrica evolutiva para evitar el colapso del gradiente en siluetas fractales; (iii) validación cuantitativa de los parámetros inferidos contra registros meteorológicos históricos del INTA Corrientes.

**5.4 Estructura del paper (1 oración)**
- "El resto del paper se organiza de la siguiente manera: la Sección II presenta el marco teórico..."

---

## 6. Marco Teórico (~1.25 páginas)

Esta es la sección más importante para no descuidar. Debe establecer la base conceptual que justifica cada decisión de diseño.

### 6.1 Sensores Satelitales de Fuego Activo: VIIRS 375 m (~0.25 pág.)

- **Qué mencionar:** El sensor VIIRS (Visible Infrared Imaging Radiometer Suite) a bordo del satélite Suomi-NPP detecta anomalías térmicas mediante bandas infrarrojas de onda media (3.74 µm) y larga (11.45 µm). Su resolución de 375 m por píxel lo hace superior al histórico MODIS (1 km) para delimitar frentes delgados y focos secundarios.
- **Por qué importa en el paper:** Justifica la decisión de usar FIRMS como ground truth y fija la escala espacial de referencia del modelo.
- **Cita obligatoria:** Schroeder et al. (2014), *Remote Sensing of Environment*.

### 6.2 Autómatas Celulares para Incendios (~0.30 pág.)

- **Qué mencionar:** Un AC es un sistema dinámico discreto definido por una 4-upla ⟨Ω, Σ, N, f⟩. Los AC para incendios forestales fueron formalizados por Alexandridis et al. (2008) siguiendo el modelo estocástico de tres estados (intacto → ardiendo → quemado) con vecindad de Moore y factor de viento exponencial.
- **Cuál es la decisión de diseño propia:** La incorporación de la capa raster del IGN como mapa de combustible heterogéneo celda a celda, que distingue cuatro categorías biofísicas funcionales de la ecorregión correntina.
- **Citas:** Alexandridis et al. (2008), Muñoz Castedo (2010).
- **NO repetir aquí** la fórmula completa del AC (va en Metodología). Solo describirla cualitativamente.

### 6.3 Geometría Fractal y Dimensión Box-Counting (~0.30 pág.)

- **Qué mencionar:** Los frentes activos de incendio en pastizales exhiben autosimilitud estadística y una dimensión fractal $D_f \in (1, 2)$ que cuantifica la rugosidad perimétrica. Mandelbrot (1982) formalizó el concepto. El box-counting es el método numérico estándar para estimarla en imágenes raster.
- **Por qué importa en el paper:** La dimensión fractal captura la morfología global del frente (forma, ramificación, digitaciones) que las métricas de superposición pixel-a-pixel no pueden capturar. Un frente circular con la misma área que el real tendría $D_f \approx 1.95$ pero sería morfológicamente incorrecto.
- **Dato propio a incluir:** Los frentes observados en Corrientes 2022 exhiben $D_f \in [1.25, 1.45]$, coherente con frentes dendríticos de pastizal seco.
- **Citas:** Mandelbrot (1982), Ariza (2007).

### 6.4 Métricas de Superposición Espacial: IoU vs. Sørensen-Dice (~0.25 pág.)

Esta es la contribución metodológica más novedosa y hay que presentarla con rigor.

- **Definir ambas formalmente:**
  - $\text{IoU} = \frac{|S \cap O|}{|S \cup O|} = \frac{TP}{TP + FP + FN}$  
  - $\text{Dice} = \frac{2|S \cap O|}{|S| + |O|} = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$
- **Relación de equivalencia:** Son monotónicamente equivalentes ($\text{IoU} = \frac{\text{Dice}}{2 - \text{Dice}}$), por lo que optimizar Dice implica optimizar IoU.
- **Por qué Dice en el fitness:** En siluetas delgadas y dispersas, el denominador de la unión del IoU crece cuadráticamente ante pequeños desvíos del frente, colapsando el gradiente selectivo hacia valores nulos (~0.02–0.05). Dice mantiene un gradiente suave y progresivo apto para la selección evolutiva.
- **Implicación para el paper:** Se usa Dice en el fitness interno (optimización) y se reportan **ambos** (IoU y Dice) en la tabla de resultados para mantener comparabilidad con la literatura.
- **Citas:** Sørensen (1948), Jaccard (1912).

### 6.5 Algoritmos Genéticos para Calibración Inversa (~0.15 pág.)

- **Qué mencionar:** Los AG (Goldberg, 1989) son metaheurísticas de búsqueda global que evolucionan una población de soluciones mediante selección, cruzamiento y mutación. Son aptos para problemas no convexos, ruidosos y de espacio continuo como el problema inverso de calibración del AC.
- **Antecedente directo:** Denham et al. (2012) propusieron un AG dinámico para calibración de simuladores de fuego bajo incertidumbre observacional. Este trabajo extiende ese paradigma incorporando la dimensión fractal como regularizador morfológico y el coeficiente de Dice como función objetivo.
- **Citas:** Goldberg (1989), Denham et al. (2012).

---

## 7. Metodología (~1.50 páginas)

Presentar en orden de pipeline de ejecución (no de implementación).

### 7.1 Adquisición y Preprocesamiento Satelital

1. Fuente de datos: archivo histórico FIRMS/VIIRS (`fire_archive_SV-C2_788988.json`).
2. Filtro geográfico a la ventana de Corrientes: Lat [-30.8°, -27.2°], Lon [-59.8°, -55.6°].
3. Rasterización en grilla 256×256 (≈1.56 km/celda).
4. Dilatación morfológica: 1 iteración con elemento 3×3 (r ≈ 1.6 km físicos). Justificar brevemente por qué 1 iteración y no 2 (Ver docs/DOCUMENTACION_COMPLETA_PROYECTO.md §3.6).
5. Preservación multicluster: se conservan todos los focos validados por NASA, sin descartar componentes conexas menores.

### 7.2 Capa de Biomasa Heterogénea (IGN WFS)

- Tabla de las 4 categorías con sus coeficientes $M_{\text{comb}}$.
- Explicar la distinción entre $M_{\text{comb}}(x,y)$ (espacial, fijo, del IGN) y $c_f$ (temporal, global, gen del AG): el primero modela la estructura de la vegetación; el segundo modela el estado hídrico acumulado del ecosistema en el período de sequía.

### 7.3 Modelo del Autómata Celular

- Definición formal de los 3 estados y la vecindad de Moore.
- Ecuación de probabilidad de ignición **completa** con todos los factores.
- Discretización temporal: Δt = 48 min → 30 pasos/día.
- Saturación en p ≤ 0.95 (justificar brevemente).

### 7.4 Función de Aptitud Híbrida 50/50

- Ecuación del fitness.
- Justificación del 50/50: la dimensión fractal captura la forma; Dice captura la posición. Sin uno de los dos, el AG converge a soluciones deformadas o desplazadas.
- Evaluación con M=5 réplicas Monte Carlo (por qué: neutralizar ruido estocástico del AC).

### 7.5 Configuración del Algoritmo Genético

Presentar como tabla (ocupa menos espacio que texto corrido):

| Parámetro | Valor |
|:---|:---:|
| Tamaño población | 32 |
| Generaciones | 40 |
| Selección | Torneo k=3 |
| Cruce | Aritmético intermedio |
| Prob. mutación | 0.10 |
| Elitismo | 4 individuos |
| Réplicas Monte Carlo | 5 |
| Paralelismo | ProcessPoolExecutor |

---

## 8. Resultados y Discusión (~1.25 páginas)

### 8.1 Caso de Estudio

- Período: 17–18 de febrero de 2022 (pico de la crisis).
- Focos observados: 1.383 (día 17) → 2.785 (día 18).
- Dimensión fractal observada: $D_{17} = 1.2587$, $D_{18} = 1.4041$ (aumento indica ramificación activa).

### 8.2 Convergencia del AG

- **Figura obligatoria:** Curva de fitness vs. generación (ya existe en `output/curva_fitness.png`).
- Comentar las tres fases: exploración inicial, refinamiento fino, estabilización elitista.
- Fitness óptimo alcanzado: **0.7827** en generación 29.

### 8.3 Parámetros Inferidos

Presentar como tabla y comentar la coherencia física:

| Parámetro | Valor inferido | Validación física |
|:---|:---:|:---|
| Velocidad viento | 6.41 km/h | Consistente con vientos superficiales de madrugada |
| Dirección viento | 243.32° (WSW) | Flujo oeste-sudoeste documentado por INTA |
| Humedad relativa | 23.03% | Déficit hídrico extremo de La Niña (< 25%) |
| Factor combustible | 0.291 | Biomasa de pastizal seco de final de verano |

### 8.4 Proyección Predictiva

- **Figura obligatoria:** Mapa isócrono +24h/+48h/+72h (ya existe en `output/mapa_riesgo_predictivo.png`).
- Departamentos en alerta: Ituzaingó, Concepción, San Luis del Palmar, San Martín.
- Cobertura proyectada +24h: 3.653 celdas (≈ 8.900 km²).

### 8.5 Discusión

Mencionar al menos dos limitaciones honestas:
1. El viento se modela como **uniforme y constante** en todo el dominio para un día completo. En la realidad rota durante el ciclo diurno.
2. La topografía no está incorporada (SRTM pendiente como T2.3).

---

## 9. Trabajos Relacionados (~0.50 páginas)

Organizar por afinidad metodológica, no cronológicamente:

- **Autómatas Celulares para Incendios:** Alexandridis et al. (2008), Muñoz Castedo (2010).
- **Calibración Inversa con AG:** Denham et al. (2012), Méndez Garabetti (2022).
- **Teledetección Satelital:** Schroeder et al. (2014), Son et al. (2024).
- **Geometría Fractal en Fuego:** Ariza (2007).

> **Nota:** Los trabajos relacionados van DESPUÉS de los resultados en congresos de informática (CACIC/JAIIO), no antes. En revistas de ingeniería suelen ir en la Introducción o inmediatamente después.

---

## 10. Conclusión y Trabajos Futuros (~0.30 páginas)

### Conclusión (3–4 oraciones)

Debe responder: ¿Se resolvió el problema planteado en la Introducción? Respuesta objetiva basada en métricas.

**Borrador sugerido:**
> Se presentó un sistema de optimización inversa que integra algoritmos genéticos, autómatas celulares con biomasa heterogénea del IGN y geometría fractal para inferir condiciones microclimáticas en incendios forestales activos a escala provincial. Evaluado sobre el megaincendio de Corrientes 2022, el sistema alcanzó un fitness de 0.7827 infiriendo parámetros plenamente consistentes con los registros del INTA. La adopción del coeficiente de Sørensen-Dice en paridad con la dimensión fractal demostró ser clave para mantener el gradiente evolutivo en siluetas morfológicamente complejas.

### Trabajos Futuros (lista de 3 ítems, máximo)

1. Mecanismo de saltación de pavesas (Spotting) con distribución de Weibull.
2. Optimización multiobjetivo NSGA-II para obtener el frente de Pareto Fractal–Dice.
3. Forzamiento meteorológico dinámico con reanálisis ERA5-Land (rotación diurna del viento).

---

## 11. Referencias Obligatorias

Las siguientes **9 referencias son obligatorias** para el paper. Sin ellas, los revisores observarán ausencias críticas:

| # | Cita | Por qué es obligatoria |
|:---:|:---|:---|
| [1] | Schroeder et al. (2014). *Remote Sensing of Environment*, 143, 85–96. | Producto VIIRS 375m (ground truth). |
| [2] | Alexandridis et al. (2008). *Applied Mathematics and Computation*, 204, 191–201. | Modelo AC canónico de incendios. |
| [3] | Denham et al. (2012). *Journal of Computational Science*, 3(5), 398–404. | Antecedente directo de AG para calibración de fuego. |
| [4] | Goldberg (1989). *Genetic Algorithms in Search, Optimization, and Machine Learning*. Addison-Wesley. | Fundamento de AG. |
| [5] | Mandelbrot (1982). *The Fractal Geometry of Nature*. W.H. Freeman. | Fundamento de la dimensión fractal. |
| [6] | Sørensen (1948). *Biologiske Skrifter*, 5, 1–34. | Definición original del coeficiente Dice. |
| [7] | Jaccard (1912). *New Phytologist*, 11(2), 37–50. | Definición original del IoU. |
| [8] | Méndez Garabetti (2022). Tesis Doctoral, UNLP. | Antecedente en reducción de incertidumbre con AG. |
| [9] | Son et al. (2024). *Remote Sensing*, 16(14), 2667. | Validación de VIIRS para delimitar incendios. |
| [10] | INTA Corrientes (2022). Informe Técnico N°5. | Datos observacionales del caso de estudio. |

> **Evitar citar:** Wikipedia, ScienceDirect Topics, páginas web sin DOI, informes sin autor institucional claro.

---

## 12. Checklist Final Antes de Enviar

- [ ] El abstract menciona explícitamente los resultados numéricos (fitness = 0.7827).
- [ ] La fórmula del AC incluye $M_{\text{comb}}(x,y)$ (biomasa del IGN).
- [ ] La función de fitness usa **Dice**, no IoU. Texto, ecuación y figuras son consistentes.
- [ ] La Tabla de resultados reporta **tanto IoU como Dice** para comparabilidad.
- [ ] Las Figuras tienen epígrafe completo (número, descripción, fuente si aplica).
- [ ] Las referencias [1]–[10] están todas citadas en el texto.
- [ ] No hay citas a Wikipedia ni a páginas web sin DOI.
- [ ] El nombre de Lewis Fry **Richardson** está escrito correctamente (con 'd').
- [ ] Todos los acentos diacríticos están presentes en el texto en castellano.
- [ ] El documento tiene **6 páginas exactas** al compilar en la plantilla IEEE.

