# Documentación: `calcular_dimension_fractal.py`

## 1. Propósito General del Módulo
`calcular_dimension_fractal.py` implementa los algoritmos geométricos y estadísticos para cuantificar la complejidad espacial y rugosidad morfométrica de los frentes de fuego. Provee métodos altamente optimizados para la extracción del perímetro morfológico exterior y el cálculo de la **Dimensión Fractal de Minkowski-Bouligand (Dimensión Box-Counting, $D$)** mediante transformaciones matriciales 100% vectorizadas en NumPy sin bucles lentos de Python.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo suministra la métrica morfométrica clave que fundamenta el proyecto:
- **En la Fase de Optimización Inversa:** Es consumido directamente por `algoritmo_genetico.py` para evaluar qué tan semejante es la rugosidad del frente de fuego generado por el autómata celular respecto al frente real capturado por el satélite.
- **En Análisis Independiente:** Puede ejecutarse como un script autónomo de diagnóstico para generar reportes visuales con gráficos en escala log-log y ajustes por regresión lineal por mínimos cuadrados.

```
 [Matriz Binaria de Fuego]
            │
            ▼
    extraer_perimetro()  ◄── Erosión morfológica binaria
            │
            ▼
 [Matriz de Perímetro (Rugosidad)]
            │
            ▼
  calcular_box_counting() ◄── Reshape 4D vectorizado + Conteo de cajas
            │
            ▼
  Regresión Lineal Log-Log [ln(1/ε) vs ln(N(ε))]
            │
            ▼
    Dimensión Fractal (D) ──► Utilizada en la Función de Fitness del AG
```

---

## 3. Entradas y Salidas
### Entradas:
- Matrices binarias 2D de tamaño $256 \times 256$ (tipo booleano o entero `0/1`), típicamente cargadas desde `output/matriz_objetivo_limpia_<fecha>.npy` o producidas dinámicamente por el autómata celular.

### Salidas:
- **Valor escalar:** Dimensión fractal $D \in [1.0, 2.0]$ (donde $1.0$ representa una línea euclidiana lisa y valores cercanos a $2.0$ denotan una frontera extremadamente ramificada y rugosa que llena el plano).
- **Vectores de análisis:** Vectores coordenados en escala logarítmica para análisis de regresión ($x, y$), lista de tamaños de caja ($\epsilon$) y conteos observados ($N(\epsilon)$).
- **Artefacto gráfico (en modo script):** `reporte_fractal_<fecha>.png`, figura comparativa compuesta por el mapa de perímetro y el gráfico de dispersión con la recta de regresión ajustada.

---

## 4. Dependencias y Librerías
- **Cálculo numérico y álgebra lineal:** `numpy`.
- **Morfología matemática:** `scipy.ndimage.binary_erosion`.
- **Graficación y reporte:** `matplotlib.pyplot`.

---

## 5. Fundamentos Físicos y Matemáticos
### ¿Por qué medir el perímetro y no el área sólida?
En la física de propagación de incendios, el interior de la mancha quemada es una superficie conexa bidimensional continua ($D \approx 2.0$), lo cual enmascara la dinámica del fuego. La verdadera firma fractal del siniestro radica en su **frente de propagación activo (el contorno o perímetro)**. Este perímetro refleja la interacción turbulenta entre el viento, la heterogeneidad de la biomasa vegetal y la topografía local, exhibiendo una geometría no euclidiana típicamente comprendida entre $1.15 \le D \le 1.65$.

### Algoritmo de Box-Counting Vectorizado:
La dimensión fractal de Hausdorff/Box-Counting se define formalmente como:
$$D = \lim_{\epsilon \to 0} \frac{\ln N(\epsilon)}{\ln(1/\epsilon)}$$
Donde $N(\epsilon)$ es el número de cajas de tamaño $\epsilon$ necesarias para cubrir completamente el perímetro.

Para evitar cuellos de botella en la ejecución iterativa del Algoritmo Genético, este módulo reemplaza los bucles tradicionales anidados por un **reshape matricial en cuatro dimensiones**:
```python
bloques = matriz_perimetro.reshape(n // tamano, tamano, n // tamano, tamano).any(axis=(1, 3))
contador = np.count_nonzero(bloques)
```
Esta operación reorganiza la memoria a nivel de punteros C en NumPy, evaluando instantáneamente la ocupación de cada celda de tamaño $\epsilon \times \epsilon$ con una reducción booleana sobre los ejes 1 y 3.
Posteriormente, se ajusta un polinomio de grado 1 (`np.polyfit`) sobre los pares de puntos logarítmicos:
$$\ln N(\epsilon) = D \cdot \ln(1/\epsilon) + c$$
La pendiente del ajuste resultante es la dimensión fractal $D$.

