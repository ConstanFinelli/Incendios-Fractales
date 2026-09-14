# Documentación: `automata_celular.py`

## 1. Propósito General del Módulo

`automata_celular.py` implementa el simulador biofísico de propagación de incendios forestales basado en un **Autómata Celular Estocástico Bidimensional en Grilla Regular**. Modela la dinámica de transferencia de calor y propagación de frentes de combustión en función de las variables ambientales clave: velocidad del viento, dirección del viento, humedad relativa del ambiente y carga de combustible vegetal disponible.

---

## 2. Rol en la Arquitectura del Sistema

Este módulo es el motor computacional de simulación física del proyecto y es utilizado en dos instancias críticas:

1. **En la Fase 2 (Optimización Inversa):** Es invocado decenas de miles de veces por `algoritmo_genetico.py` para simular la evolución del fuego bajo diferentes hipótesis climáticas candidatas y comparar las geometrías resultantes contra las fotos satelitales.
2. **En la Fase 3 (Predicción Operativa):** Es invocado por `simulador_predictivo.py` para avanzar la grilla hacia el futuro a través de múltiples etapas sucesivas (+24h, +48h, +72h).

```
          [Variables Ambientales del AG o Predictor]
         (Viento Vel, Viento Dir, Humedad, Combustible)
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │     automata_celular.py               │
         │                                       │
         │  • Cálculo de probabilidades aniso-   │
         │    trópicas de propagación            │
         │  • Máquina de estados finitos (0,1,2) │
         │  • Optimización por celdas activas    │
         └───────────────────┬───────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   simular_incendio_AC()            simular_evolucion_multietapa()
   (Optimización y pruebas)         (Predicción continua 24h/48h/72h)
```

---

## 3. Entradas y Salidas

### Entradas:

- `viento_vel` (float): Velocidad del viento en $\text{km/h} \in [0, 50]$.
- `viento_dir` (float): Dirección del viento en grados azimutales $\in [0, 360^\circ]$ ($0^\circ = \text{Norte}, 90^\circ = \text{Este}, 180^\circ = \text{Sur}, 270^\circ = \text{Oeste}$).
- `humedad` (float): Humedad relativa del aire en porcentaje $\in [10\%, 80\%]$.
- `combustible` (float): Coeficiente escalar global de sequedad/disponibilidad $\in [0.1, 1.0]$.
- `pasos_tiempo` / `pasos_por_dia` (int): Cantidad de ciclos de reloj discretos a iterar (calibrado en $30 \text{ pasos} \equiv 24 \text{ horas}$).
- `grilla_inicial` (`numpy.ndarray`, opcional): Matriz base sobre la cual iniciar la simulación (focos observados reales o cicatrices previas).
- `mapa_combustible` (`numpy.ndarray` 2D, opcional): Matriz de coeficientes biofísicos de cobertura vegetal $C_{\text{local}} \in [0.0, 1.0]$ provista por `capa_biomasa.py`. Si es `None`, se carga automáticamente el mapa oficial rasterizado de Corrientes.

### Salidas:

- **Matriz de estados:** `numpy.ndarray` con valores enteros $\{0, 1, 2\}$.
- **Matriz binaria consolidada:** `numpy.ndarray` booleana/binaria $\{0, 1\}$ (donde tanto las celdas ardiendo como las quemadas valen $1$, lista para análisis de contorno fractal e intersección sobre unión IoU).
- **Secuencia multietapa:** Lista de matrices instantáneas al finalizar cada horizonte temporal diario.

---

## 4. Dependencias y Librerías

- **Cálculo numérico y aleatorio:** `numpy`.
- **Graficación y mapas de color:** `matplotlib.pyplot`, `matplotlib.colors.ListedColormap`.
- **Heterogeneidad espacial:** `capa_biomasa.obtener_mapa_combustible`.

---

## 5. Fundamentos Matemáticos y Reglas de Transición

### Estados de Celda:

Cada celda $(y, x)$ de la grilla $256 \times 256$ adopta en cada paso temporal $t$ uno de tres estados discretos:

- **Estado 0 (Intacta / No quemada):** Vegetación susceptible con biomasa disponible.
- **Estado 1 (Ardiendo / Frente activo):** Celda en proceso activo de combustión y emisión térmica.
- **Estado 2 (Quemada / Cenizas):** Biomasa consumida; no puede reencenderse ni propagar fuego.

### Modelo Físico de Propagación con Heterogeneidad Espacial:

La probabilidad base de ignición $P_{\text{base}}$ depende de la carga local de combustible según el tipo de cobertura biofísica y de la humedad relativa $H \in [0, 1]$:
$$C_{\text{local}}(y, x) = M_{\text{comb}}(y, x) \cdot c_{\text{global}}$$
$$P_{\text{base}}(y, x) = C_{\text{local}}(y, x) \cdot (1 - H)$$

- **Cuerpos de agua y esteros profundos:** $M_{\text{comb}}(y, x) = 0.0 \implies P_{\text{ignición}} = 0.0$ (barrera cortafuego absoluta).
- **Bañados y vegetación hidrófila:** $M_{\text{comb}}(y, x) = 0.2$ (resistencia hídrica elevada).
- **Pastizales y sabanas:** $M_{\text{comb}}(y, x) = 0.6$ (matriz de propagación base).
- **Plantaciones forestales:** $M_{\text{comb}}(y, x) = 1.0$ (máxima inflamabilidad y aceleración de copa).
- **Límites exteriores provinciales:** $M_{\text{comb}}(y, x) = 0.0$ (condición Dirichlet absorbente).

La influencia direccional del viento introduce una **anisotropía exponencial** en la vecindad de Moore (8 vecinos circundantes):
Para cada vecino en la posición relativa $(\Delta y, \Delta x)$, se define el ángulo espacial del vecino:
$$\theta_{\text{vecino}} = \operatorname{atan2}(-\Delta y, \Delta x)$$
La alineación angular con el vector del viento $\theta_{\text{viento}}$ se evalúa mediante el coseno:
$$\cos(\Delta \theta) = \cos(\theta_{\text{viento}} - \theta_{\text{vecino}})$$
El factor de amplificación por viento es modelado como:
$$f_{\text{viento}} = \exp(c_{\text{viento}} \cdot V_{\text{viento}} \cdot \cos(\Delta \theta))$$
con $c_{\text{viento}} = 0.05$. La probabilidad final de que una celda intacta se encienda por contacto con un vecino en llamas es:
$$P_{\text{ignición}}(y, x) = \min(P_{\text{base}}(y, x) \cdot f_{\text{viento}}, \, 0.95)$$
Si $C_{\text{local}}(y, x) \le 0.0$, la celda se omite de forma determinística en la evaluación de propagación.

### Optimización por Localización de Celdas Activas:

En lugar de recorrer las $256 \times 256 = 65,536$ celdas en cada ciclo temporal, el algoritmo utiliza `np.where(grilla == 1)` para indexar **únicamente las celdas activas**. Las celdas activas pasan automáticamente al estado 2 (cenizas), y solo sus vecinos intactos inmediatos son evaluados contra números pseudoaleatorios uniformes $U(0, 1)$. Esto reduce el tiempo computacional de la simulación en más de un $92\%$.

### Definición Formal del Paso de Simulación ($\Delta t$):

Un **paso de simulación** es la unidad atómica de integración temporal del Autómata Celular:

1. **Calibración Temporal:** Con `PASOS_POR_DIA = 30`, cada paso equivale a:
   $$\Delta t = \frac{24\text{ horas}}{30\text{ pasos}} = 0.8\text{ horas} = 48\text{ minutos}$$
2. **Escala Espacial:** Con una resolución de celda de $\approx 1.57\text{ km}$, el avance de una celda por paso implica una velocidad máxima del frente de combustión de $\approx 1.96\text{ km/h}$.
3. **Transición en 1 Paso ($t \to t+1$):**
   - El frente activo actual ($t$) se extingue localmente a cenizas incombustibles (Estado 2).
   - El frente intenta contagiar estocásticamente a los vecinos intactos (Estado 0) mediante la probabilidad anisótropa del viento $P_{\text{ignición}}$.
   - Los vecinos exitosamente encendidos constituyen el nuevo frente activo para el paso $t+1$.
