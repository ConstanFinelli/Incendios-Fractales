# Funciones de `calcular_dimension_fractal.py`

## 1. Funciones Definidas en este Archivo

<a id="extraer_perimetro"></a>
### `extraer_perimetro(matriz_binaria)`
- **Firma:** `def extraer_perimetro(matriz_binaria):`
- **Descripción:** Extrae la frontera exterior o contorno perimetral de una silueta de fuego binaria. Utiliza una erosión morfológica binaria que contrae la región encendida en un píxel en todas las direcciones y luego sustrae la versión erosionada de la matriz original:
  $$\text{Perímetro} = A \setminus (A \ominus B)$$
- **Parámetros:**
  - `matriz_binaria` (`numpy.ndarray` 2D): Matriz booleana o entera binaria ($0/1$) que representa el área quemada.
- **Retorno:** `numpy.ndarray` 2D de tipo entero, donde los píxeles con valor `1` pertenecen estrictamente al contorno exterior y `0` representa el interior o el fondo intacto.

---

<a id="calcular_box_counting"></a>
### `calcular_box_counting(matriz_perimetro)`
- **Firma:** `def calcular_box_counting(matriz_perimetro):`
- **Descripción:** Implementa el cálculo de la dimensión fractal de Minkowski-Bouligand mediante el método de Box-Counting de alta velocidad (100% vectorizado en NumPy). Divide progresivamente el espacio en grillas cuadradas con cajas de tamaño $\epsilon = n, n/2, n/4, \dots, 1$. Para cada tamaño intermedio, efectúa una redistribución tensorial en 4 dimensiones (`reshape(n // tamano, tamano, n // tamano, tamano)`) y aplica `any(axis=(1, 3))` para determinar qué cajas intersectan el perímetro. Finalmente, calcula una regresión lineal en escala log-log mediante `numpy.polyfit(x, y, 1)`.
- **Parámetros:**
  - `matriz_perimetro` (`numpy.ndarray` 2D): Matriz binaria que contiene únicamente el perímetro del incendio (generalmente obtenida con `extraer_perimetro`).
- **Retorno:** Tupla de 5 elementos:
  1. `dimension_fractal` (float): Pendiente de la recta de regresión (Dimensión Fractal $D$).
  2. `x` (`numpy.ndarray`): Valores de $\ln(1/\epsilon)$ evaluados.
  3. `y` (`numpy.ndarray`): Valores de $\ln(\max(N(\epsilon), 1))$ observados.
  4. `tamanos_caja` (`list` de int): Lista de tamaños de caja $\epsilon$ en píxeles.
  5. `conteos_cajas` (`list` de int): Lista de cantidades de cajas no vacías $N(\epsilon)$ contabilizadas.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

*Este archivo no importa funciones ni constantes de otros módulos del proyecto.* Es un módulo de base geométrica y matemática autosuficiente.

