# Documentación: `simulador_predictivo.py`

## 1. Propósito General del Módulo
`simulador_predictivo.py` es el motor de inferencia prospectiva y orquestador cartográfico multi-horizonte del sistema. Toma las variables microclimáticas óptimas calibradas por el algoritmo genético y simula el avance futuro del fuego a partir del frente activo del último día observado, proyectando la evolución del siniestro a lo largo de tres horizontes temporales estratégicos:
- **+24 Horas (+30 ciclos | Nivel Táctico):** Coordinación directa de cuadrillas de brigadistas, despliegue de autobombas y ataque a la línea de fuego.
- **+48 Horas (+60 ciclos | Nivel Preventivo):** Alerta temprana a poblaciones rurales, preparación de evacuaciones y diseño de cortafuegos mecanizados pesados.
- **+72 Horas (+90 ciclos | Nivel Estratégico):** Declaración de emergencias provinciales/nacionales, gestión de recursos aéreos y protección de reservas ecológicas críticas (como los Esteros del Iberá).

Asimismo, construye la **matriz de riesgo isócrono acumulativo** y coordina la transposición espacial hacia el visualizador GIS provincial de Corrientes.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo materializa la **Fase 3** (Predicción y Cartografía). Une los resultados de la optimización con la toma de decisiones operativa:
- Utiliza las capacidades de simulación continua de `automata_celular.py`.
- Parte de la última observación satelital válida ($T_{\text{final}}$) como foco activo de ignición.
- Genera la matriz de riesgo isócrono y la figura multipanel matricial `output/mapa_riesgo_predictivo.png`.
- Delega la proyección geográfica georreferenciada a `visualizador_corrientes.py`.

```
    [Variables Inversas Calibradas del AG] + [Último Día Observado]
                              │
                              ▼
                 simulador_predictivo.py
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   simular_evolucion_multietapa()    Construcción de Matriz
     (3 etapas continuas de 30 ciclos)  de Riesgo Isócrono (0 a 4)
               │                             │
               └──────────────┬──────────────┘
                              │
       ┌──────────────────────┴──────────────────────┐
       ▼                                             ▼
[Matriz Isócrona PNG]                        [Mapas Corrientes]
 mapa_riesgo_predictivo                       • PNG 4 paneles
                                              • HTML interactivo
                                              • Ranking Departamental
```

---

## 3. Entradas y Salidas
### Entradas:
- `datos_entrada`: Serie temporal `[(fecha, ruta), ...]` o matriz única `.npy`. Se extrae `ruta_final` para cargar el foco base activo (`matriz_final`).
- `mejores_variables`: Tupla `(viento_vel, viento_dir, humedad, combustible)` inferida por el Algoritmo Genético.
- `pasos_por_dia` (int, opcional): Tasa de conversión de pasos temporales por día (calibrado en $30$).

### Salidas:
- **Matriz de riesgo isócrono:** `numpy.ndarray` de $256 \times 256$ con valores discretos $\{0, 1, 2, 3, 4\}$.
- **Artefactos en `output/`:**
  - `output/mapa_riesgo_predictivo.png`: Figura de 4 paneles en alta resolución que compara la base observada, la predicción a +24h, a +48h y el mapa isócrono final a +72h.
  - Orquesta la creación de los mapas estáticos GIS e interactivos en Folium a través de los módulos visualizadores.

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `os`, `traceback`.
- **Cálculo numérico:** `numpy`.
- **Graficación y diseño cartográfico:** `matplotlib.pyplot`, `matplotlib.patches`, `matplotlib.colors.ListedColormap`.
- **Módulos del proyecto:**
  - `automata_celular` (`simular_evolucion_multietapa`)
  - `visualizador_corrientes` (`generar_mapas_corrientes`)

---

## 5. Fundamentos del Modelado Isócrono

### Definición de Isócronas de Fuego:
Una **isócrona de fuego** es una curva de nivel espacial que delimita la posición del perímetro del incendio en instantes temporales equivalentes. En el modelado matricial discreto, la matriz de riesgo se estructura en 5 zonas mutuamente excluyentes y ordenadas jerárquicamente por prioridad temporal:

| Valor | Denominación | Horizonte | Paleta Hex | Significado Operativo |
|---|---|---|---|---|
| **0** | Zona Intacta | — | `#f8f9fa` | Vegetación sin afectación prevista |
| **1** | Foco Base Observado | $T_0$ | `#2c3e50` | Foco satelital confirmado en la fecha de partida |
| **2** | Riesgo Táctico | $+24\text{ h}$ | `#f39c12` | Área crítica de avance en las próximas 24 horas |
| **3** | Riesgo Preventivo | $+48\text{ h}$ | `#e67e22` | Zona amenazada en el segundo día de propagación |
| **4** | Riesgo Estratégico | $+72\text{ h}$ | `#e74c3c` | Máxima expansión proyectada al tercer día |

### Condición de Frontera Inicial:
A diferencia del análisis histórico acumulado, la simulación prospectiva parte estrictamente de los focos de calor activos del último día de la serie (`matriz_final = np.load(ruta_final)`). Esto asegura que la propagación del autómata celular comience sobre vegetación no quemada a partir del frente real del momento, evitando falsas igniciones en zonas previamente consumidas.

