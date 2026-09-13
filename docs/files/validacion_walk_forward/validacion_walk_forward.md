# Documentación: `validacion_walk_forward.py`

## 1. Propósito General del Módulo

`validacion_walk_forward.py` implementa el protocolo científico de **Validación Fuera de Muestra (_Walk-Forward Validation / Blind Testing_)** para contrastar la capacidad predictiva y generalización del sistema ante escenarios de propagación de incendios forestales.

El módulo evalúa prospectivamente a ciegas **3 horizontes temporales disjuntos (+24h, +48h y +72h)** frente a observaciones satelitales reales de la NASA (VIIRS/MODIS) que **jamás fueron observadas ni utilizadas durante la fase de optimización del Algoritmo Genético**.

---

## 2. Justificación de su Existencia

- **Problema que resuelve:** En computación evolutiva y optimización inversa, evaluar un modelo sobre el mismo conjunto temporal utilizado para calibrarlo introduce un sesgo de memoria o sobreajuste (_in-sample overfit_). `validacion_walk_forward.py` resuelve este problema garantizando una validación ciega rigurosa conforme a los estándares de comités editoriales de revistas científicas internacionales (Scopus/IEEE).
- **Motivo de separación:** Mantiene el núcleo de optimización (`algoritmo_genetico.py`) y el simulador de riesgo (`simulador_predictivo.py`) desacoplados del protocolo experimental formal de validación y cálculo de matrices de confusión espacial (VP, FP, FN).
- **Ventajas de diseño:** Permite ejecutar corridas automatizadas por línea de comandos especificando ventanas arbitrarias de calibración y prueba (`--calib` y `--test`), generando reportes cuantitativos y diagnósticos espaciales multipanel sin alterar el pipeline interactivo estándar de `main.py`.

---

## 3. Rol en la Arquitectura del Sistema

Este módulo corresponde a la **Fase 4: Validación Científica** del proyecto:

1. Divide la serie satelital en ventana de calibración ($T_0 \to T_1$) y ventana de prueba ($T+1, T+2, T+3$).
2. Invoca a `algoritmo_genetico.py` para deducir el microclima óptimo sobre la ventana de calibración.
3. Proyecta de manera continua el Autómata Celular (`automata_celular.py`) a lo largo de 30, 60 y 90 pasos temporales modulado por la capa biofísica de combustible del IGN (`capa_biomasa.py`).
4. Extrae la dimensión fractal directa (`calcular_dimension_fractal.py`) y contrasta píxel a píxel contra las cicatrices reales.

```
       [Ventana Calibración: T0 -> T1]           [Ventana Prueba: T+1, T+2, T+3]
                      │                                         │
                      ▼                                         ▼
         ┌─────────────────────────┐               ┌─────────────────────────┐
         │  algoritmo_genetico.py  │               │ Observaciones NASA Real │
         └────────────┬────────────┘               └────────────┬────────────┘
                      │                                         │
                      ▼ (Microclima Óptimo)                     │
         ┌─────────────────────────┐                            │
         │   automata_celular.py   │ ──(Proyección Ciega)──►    │
         └─────────────────────────┘                            │
                      │                                         │
                      └───────────────────┬─────────────────────┘
                                          ▼
                         ┌─────────────────────────────────┐
                         │  validacion_walk_forward.py     │
                         │                                 │
                         │  • Matriz de Confusión Espacial │
                         │  • F1-Dice, IoU, Recall, Prec   │
                         │  • Error Fractal ΔD             │
                         │  • Visualización Multipanel 3x3 │
                         └────────────────┬────────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
     [Gráficos Diagnósticos]                       [Reporte Cuantitativo]
      • walk_forward_comparativa_3dias.png          • reporte_walk_forward_3dias.csv
      • walk_forward_metricas_progression.png
```

---

## 4. Entradas y Salidas

### Entradas:

- `--calib`: Lista de fechas para la ventana de entrenamiento (por defecto: `2022-02-16 2022-02-17`).
- `--test`: Lista de fechas para la evaluación ciega a +24h, +48h y +72h (por defecto: `2022-02-18 2022-02-19 2022-02-20`).

### Salidas:

- **`output/walk_forward_comparativa_3dias.png`:** Diagnóstico espacial multipanel (Verdad Satelital vs. Predicción Ciega vs. Mapa de Errores VP/FP/FN).
- **`output/walk_forward_metricas_progression.png`:** Curvas de evolución de las métricas de rendimiento en función del horizonte temporal.
- **`output/reporte_walk_forward_3dias.csv`:** Registro tabular con todas las métricas calculadas ($F_1$-Dice, IoU, Cobertura, Pureza, $\Delta D$, VP, FP, FN y variables microclimáticas).

---

## 5. Dependencias y Librerías

- **Librerías estándar:** `os`, `sys`, `csv`, `argparse`.
- **Cálculo numérico y manipulación de matrices:** `numpy`, `pandas`.
- **Graficación y mapas de diagnóstico:** `matplotlib.pyplot`, `matplotlib.patches`, `matplotlib.colors.ListedColormap`.
- **Módulos internos del proyecto:**
  - `ver_mapa_filtrado.py`
  - `algoritmo_genetico.py`
  - `automata_celular.py`
  - `calcular_dimension_fractal.py`
  - `capa_biomasa.py`
