# Documentación: `algoritmo_genetico.py`

## 1. Propósito General del Módulo
`algoritmo_genetico.py` implementa el núcleo de **Optimización Inversa Multitemporal por Computación Evolutiva**. Su objetivo primordial es inferir los parámetros microclimáticos y ambientales latentes (velocidad del viento, dirección azimutal, humedad relativa y carga de combustible) que gobernaron la propagación histórica de un incendio forestal registrado por satélites.

Resuelve un problema inverso altamente no lineal y ruidoso utilizando un algoritmo genético acelerado por multiprocesamiento en paralelo, guiado por una **función de fitness híbrida** que combina la geometría fractal del perímetro con la métrica de superposición espacial directa (IoU).

---

## 2. Rol en la Arquitectura del Sistema
Este módulo constituye la **Fase 2** del proyecto. Conecta los datos satelitales procesados con el motor físico del autómata celular:
- Consume las matrices de incendios generadas en la Fase 1 (`ver_mapa_filtrado.py`).
- Evalúa miles de hipótesis de propagación mediante simulaciones Monte Carlo del autómata celular (`automata_celular.py`).
- Cuantifica la dimensión fractal con `calcular_dimension_fractal.py`.
- Genera el vector calibrado de mejores variables ambientales que luego alimenta a `simulador_predictivo.py` para pronosticar los escenarios futuros a 24h, 48h y 72h.

```
                  [Matrices Satelitales Reales]
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │        algoritmo_genetico.py                │
        │                                             │
        │  • Población: 32 cromosomas [V, θ, H, C]     │
        │  • Evaluación multinúcleo en paralelo       │
        │  • Monte Carlo (5 corridas por individuo)   │
        │  • Fitness híbrido (50% Fractal + 50% IoU)  │
        │  • Selección por torneo (k=3), Cruce, Mut   │
        │  • Elitismo (top 4 individuos conservados)  │
        └──────────────────────┬──────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [Telemetría y Convergencia]            [Variables Óptimas]
  • curva_fitness.png                    (V_vel, V_dir, Hum, Comb)
  • historial_fitness.csv                         │
  • resultados_optimizacion.csv                   ▼
                                       A simulador_predictivo.py
```

---

## 3. Entradas y Salidas
### Entradas:
- `entradas_matrices`: Puede ser la ruta a una matriz `.npy` única (análisis unitemporal) o una lista de tuplas `[(fecha, ruta_matriz), ...]` (serie multitemporal).

### Salidas:
- **Vector óptimo:** Lista de 4 variables de punto flotante `[viento_vel, viento_dir, humedad, combustible]`.
- **Artefactos en `output/`:**
  - `output/curva_fitness.png`: Gráfico de evolución temporal del mejor fitness y fitness promedio por generación.
  - `output/historial_fitness.csv`: Registro tabular generación por generación de los hiperparámetros y métricas de convergencia.
  - `output/resultados_optimizacion.csv`: Resumen final con los mejores parámetros inferidos y sus unidades físicas.

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `os`, `sys`, `random`, `csv`.
- **Cálculo numérico:** `numpy`.
- **Paralelismo:** `concurrent.futures.ProcessPoolExecutor`.
- **Graficación:** `matplotlib.pyplot`.
- **Módulos del proyecto:**
  - `automata_celular` (`simular_incendio_AC`, `_avanzar_pasos_AC`)
  - `calcular_dimension_fractal` (`extraer_perimetro`, `calcular_box_counting`, `calcular_dimension_fractal_directa`)
  - `ver_mapa_filtrado` (`procesar_rango_fechas`, en modo `__main__`)

---

## 5. Fundamentos del Algoritmo Genético

### Estructura del Cromosoma (Individuo):
Cada individuo codifica en valores continuos reales una hipótesis microclimática:
$$\vec{x} = [V_{\text{viento}}, \theta_{\text{viento}}, H_{\text{hum}}, C_{\text{comb}}]$$
- $V_{\text{viento}} \in [0, 50] \text{ km/h}$
- $\theta_{\text{viento}} \in [0, 360^\circ]$
- $H_{\text{hum}} \in [10\%, 80\%]$
- $C_{\text{comb}} \in [0.1, 1.0]$

### Función de Aptitud Híbrida (Fitness):
Para evitar que el algoritmo caiga en mínimos locales que reproduzcan la cantidad de área quemada sin respetar la forma geométrica ramificada (o viceversa), se formula un fitness balanceado:
$$\text{Fitness} = w_{\text{fractal}} \cdot F_{\text{fractal}} + w_{\text{IoU}} \cdot \text{IoU}$$
donde $w_{\text{fractal}} = 0.5$ y $w_{\text{IoU}} = 0.5$.

1. **Fitness Fractal:**
   $$F_{\text{fractal}} = \frac{1}{1 + |D_{\text{objetivo}} - D_{\text{simulado}}|}$$
   Premia a los individuos cuyo frente de fuego tenga una dimensión fractal similar al contorno observado satelitalmente.
2. **Superposición Espacial (IoU - Intersection over Union):**
   $$\text{IoU} = \frac{|M_{\text{real}} \cap M_{\text{sim}}|}{|M_{\text{real}} \cup M_{\text{sim}}|}$$
   Garantiza que el incendio se propague en la misma dirección y ubicación geográfica que el fenómeno real.

### Mitigación de Ruido Estocástico (Monte Carlo):
Dado que el autómata celular es probabilístico, un individuo prometedor podría obtener un mal puntaje por una tirada aleatoria desfavorable. Para estabilizar el fitness, cada individuo se evalúa promediando los resultados de $N = 5$ simulaciones Monte Carlo independientes (`NUM_SIMULACIONES = 5`).

### Operadores Genéticos y Estrategia Evolutiva:
- **Selección:** Torneo determinista de tamaño $k = 3$.
- **Cruce:** Cruce en un punto de valor real (`1-point crossover`).
- **Mutación:** Mutación aleatoria uniforme sobre un gen con probabilidad $P_m = 0.1$.
- **Elitismo:** Los 4 individuos más aptos de cada generación se preservan intactos para la siguiente (`NUM_ELITES = 4`), garantizando monotonicidad en el mejor fitness histórico.

