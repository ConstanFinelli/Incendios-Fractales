# Informe Científico: Validación Fuera de Muestra (_Walk-Forward Validation_) a 3 Horizontes (+24h, +48h y +72h)

**Tarea Asociada:** T3.1 (_Walk-Forward Validation / Blind Testing_)  
**Estado:** ✅ **Completado e Implementado**  
**Módulo Ejecutable:** [`validacion_walk_forward.py`](../validacion_walk_forward.py)  
**Entregables Generados:**

- **Mapa Diagnóstico Espacial Multipanel:** [`output/walk_forward_comparativa_3dias.png`](../output/walk_forward_comparativa_3dias.png)
- **Curva de Evolución Temporal de Métricas:** [`output/walk_forward_metricas_progression.png`](../output/walk_forward_metricas_progression.png)
- **Reporte Cuantitativo Tabular:** [`output/reporte_walk_forward_3dias.csv`](../output/reporte_walk_forward_3dias.csv)

---

## 1. Justificación Metodológica y Diseño Experimental

En el modelado de sistemas complejos y dinámica de incendios forestales, evaluar un modelo evolutivo sobre el mismo intervalo temporal en el que fue optimizado introduce un sesgo de sobreajuste (_in-sample bias_).

Para garantizar la **validez prospectiva** del modelo de optimización inversa, se diseñó un protocolo de **Validación Fuera de Muestra (_Walk-Forward_)**:

1. **Ventana de Calibración / Entrenamiento ($T_0 \to T_1$):** El Algoritmo Genético optimiza las variables climáticas ($v_{\text{viento}}, \theta_{\text{dir}}, H_{\text{hum}}, C_{\text{comb}}$) observando únicamente los días **16 y 17 de febrero de 2022**.
2. **Ventana de Prueba Ciega Multietapa ($T+1, T+2, T+3$):** A partir del estado del frente activo de fuego al finalizar el entrenamiento ($T_1$, 17 de febrero), se proyecta la evolución del fuego en el Autómata Celular durante 3 días consecutivos sin reentrenar el algoritmo:
   - **Horizonte +24h:** 18 de febrero de 2022 (+30 pasos AC).
   - **Horizonte +48h:** 19 de febrero de 2022 (+60 pasos AC).
   - **Horizonte +72h:** 20 de febrero de 2022 (+90 pasos AC).
3. **Contraste Ciego contra NASA FIRMS:** Cada proyección simulada se evalúa contra las observaciones satelitales reales instantáneas no vistas por el AG.

---

## 2. Resultados Cuantitativos Consolidados

| Horizonte |     Horas     | Fecha Satelital | $F_1$-Dice Ciego | IoU Ciego (Jaccard) | Cobertura ($\text{Recall}$) | Pureza ($\text{Precision}$) | $D_{\text{real}}$ | $D_{\text{sim}}$ | Error $\Delta D$ | Fitness Híbrido |
| :-------- | :-----------: | :-------------: | :--------------: | :-----------------: | :-------------------------: | :-------------------------: | :---------------: | :--------------: | :--------------: | :-------------: |
| **+24h**  | $24\text{ h}$ |  `2022-02-18`   |  **$81.05\%$**   |      $68.14\%$      |          $69.42\%$          |        **$97.38\%$**        |     $1.4757$      |     $1.4097$     |     $0.0660$     |  **$0.8743$**   |
| **+48h**  | $48\text{ h}$ |  `2022-02-19`   |  **$72.49\%$**   |      $56.85\%$      |          $57.67\%$          |        **$97.55\%$**        |     $1.5124$      |     $1.4097$     |     $0.1027$     |  **$0.8159$**   |
| **+72h**  | $72\text{ h}$ |  `2022-02-20`   |  **$70.29\%$**   |      $54.19\%$      |          $54.93\%$          |        **$97.55\%$**        |     $1.5220$      |     $1.4097$     |     $0.1122$     |  **$0.8010$**   |

---

## 3. Análisis y Hallazgos Científicos

1. **Ultra-Alta Pureza Espacial ($\text{Precision} > 97\%$):**
   - En los tres horizontes, la precisión se mantuvo en **$97.4\% - 97.6\%$**, lo que demuestra que el modelo **no genera falsas alarmas ni sobreexpande el fuego hacia áreas intactas o cuerpos de agua protegidos por la capa de biomasa**.
2. **Capacidad Predictiva a 24 Horas ($F_1\text{-Dice} = 81.05\%$):**
   - A $+24\text{ horas}$, el modelo predice con un $81\%$ de fidelidad espacial y un error fractal minúsculo ($\Delta D = 0.066$), capturando la propagación real del frente.
3. **Decaimiento Temporal Esperable y Coherente a +48h y +72h:**
   - A medida que nos alejamos temporalmente de la ventana de calibración, la cobertura ($\text{Recall}$) desciende suavemente de $69.4\%$ a $54.9\%$, debido a que las condiciones meteorológicas reales de la atmósfera cambiaron en los días posteriores. Aun así, el $F_1$-Score se sostiene **por encima del $70\%$ a 72 horas vista**, validando la solidez de la formulación híbrida.
