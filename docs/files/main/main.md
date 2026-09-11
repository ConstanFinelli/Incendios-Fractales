# Documentación: `main.py`

## 1. Propósito General del Módulo
`main.py` constituye el punto de entrada principal (entrypoint) y orquestador maestro de la arquitectura completa del proyecto. Su función primordial es coordinar la interacción secuencial de las tres fases fundamentales del sistema:
1. **Fase 1: Extracción, Filtrado Espacial y Rasterización Satelital.**
2. **Fase 2: Optimización Inversa Multitemporal mediante Algoritmos Genéticos.**
3. **Fase 3: Modelado Predictivo Multi-Horizonte (24h, 48h, 72h) y Cartografía GIS Provincial (Corrientes).**

El script proporciona una interfaz interactiva de línea de comandos (CLI) que guía al usuario en la selección de intervalos temporales de análisis, valida la disponibilidad de datos de la NASA (VIIRS/FIRMS) y coordina el flujo de datos entre los distintos módulos especializados.

---

## 2. Rol en la Arquitectura del Sistema
`main.py` actúa como la capa de aplicación y control de alto nivel. No implementa algoritmos matemáticos ni transformaciones matriciales de bajo nivel de forma directa; en su lugar, consume las abstracciones provistas por:
- `ver_mapa_filtrado.py`: para la ingestión satelital y generación de siluetas fractales limpias.
- `algoritmo_genetico.py`: para inferir las condiciones microclimáticas latentes que guiaron el avance histórico del fuego.
- `simulador_predictivo.py`: para proyectar el avance táctico, preventivo y estratégico del fuego a +24h, +48h y +72h, exportando mapas estáticos e interactivos de Corrientes.

```
       [ Usuario / CLI ]
               │
               ▼
           main.py (Orquestador)
        ┌──────┼─────────────────────────┐
        ▼      ▼                         ▼
    [FASE 1] [FASE 2]                 [FASE 3]
  ver_mapa_  algoritmo_              simulador_
  filtrado   genetico                predictivo
               │                         │
               ├─► automata_celular      └─► visualizador_corrientes
               └─► dimension_fractal
```

---

## 3. Entradas y Salidas
### Entradas:
- **Interacción por consola (CLI):**
  - `fecha_inicio` (str): Fecha inicial en formato `AAAA-MM-DD` (ej. `2022-02-17`). Requerida.
  - `fecha_fin` (str): Fecha final en formato `AAAA-MM-DD` (ej. `2022-02-19`). Opcional; si se omite o coincide con `fecha_inicio`, el sistema autoconfigura el avance temporal continuo hacia el día siguiente (`fecha_inicio + 1 día`) garantizando una transición dinámica ($T_0 \to T_1$).

### Salidas:
- Orquesta la generación de todos los artefactos en la carpeta `output/`:
  - `output/npy/matriz_objetivo_limpia_{fecha}.npy`: Matrices binarias satelitales procesadas.
  - `output/siluetas/silueta_fuego_limpia_{fecha}.png`: Siluetas fractales limpias por fecha.
  - `output/curva_fitness.png`: Curva de convergencia evolutiva del algoritmo genético.
  - `output/historial_fitness.csv` y `output/resultados_optimizacion.csv`: Telemetría del AG.
  - `output/mapa_riesgo_predictivo.png`: Matriz isócrona multi-horizonte (24h, 48h, 72h).
  - `output/mapa_corrientes_prediccion.png`: Cartografía GIS de Corrientes en 4 paneles a 300 DPI.
  - `output/mapa_corrientes_interactivo.html`: Mapa interactivo multicapa de Corrientes (Folium).

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `sys`, `os`.
- **Librerías científicas:** `numpy`.
- **Módulos locales del proyecto:**
  - `ver_mapa_filtrado`
  - `algoritmo_genetico`
  - `simulador_predictivo`

---

## 5. Flujo de Ejecución Detallado
1. **Inicialización y banner informativo:** Presenta las constantes activas del sistema, notablemente `PASOS_POR_DIA` (definida en `algoritmo_genetico.py`), que calibra la escala temporal del autómata celular.
2. **Recepción y saneamiento de fechas:** Valida que al menos la fecha de inicio esté presente. Si se omite la fecha final o es idéntica a la inicial, autoconfigura el avance temporal dinámico sumando 1 día (`fecha_inicio + 1 día`) para garantizar la calibración de la propagación ($T_0 \to T_1$).
3. **Ejecución de Fase 1:**
   - Invoca a `procesar_rango_fechas(fecha_inicio, fecha_fin)` (o `procesar_fecha` en caso unitemporal) y genera las matrices binarias en `output/npy/` y las siluetas fractales limpias en `output/siluetas/`.
   - Valida la existencia de matrices rasterizadas válidas dentro del polígono provincial de Corrientes.
4. **Ejecución de Fase 2:**
   - Invoca `ejecutar_algoritmo_genetico(datos_entrada)`.
   - Si el AG converge con éxito, recibe la tupla de mejores variables microclimáticas: `(viento_vel, viento_dir, humedad, combustible)`.
5. **Ejecución de Fase 3:**
   - Invoca `ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA)`.
   - Se simulan los 3 horizontes continuos y se delega la generación de mapas georreferenciados.
6. **Cierre e informe de artefactos:** Imprime en consola la lista completa de productos analíticos y cartográficos generados.

