# Funciones de `main.py`

## 1. Funciones Definidas en este Archivo

<a id="main"></a>
### `main()`
- **Firma:** `def main():`
- **Descripción:** Punto de entrada principal y orquestador del sistema. Controla secuencialmente la recepción de entradas del usuario, el preprocesamiento de datos satelitales, la optimización inversa por algoritmo genético y la simulación predictiva cartográfica.
- **Parámetros:** Ninguno (lee directamente de `input()` y parámetros por consola).
- **Retorno:** `None`.
- **Lógica interna:**
  1. Imprime el encabezado y banner de inicialización del sistema.
  2. Solicita interactivamente la fecha inicial (`fecha_inicio`) y fecha final (`fecha_fin`). Si la fecha inicial está vacía, aborta la ejecución con código de error `1`.
  3. Si la fecha final está vacía o coincide con la inicial, autoconfigura el avance dinámico al día siguiente (`fecha_inicio + 1 día`) asegurando la calibración temporal del modelo.
  4. Llama al subproceso de extracción satelital (`procesar_rango_fechas` o `procesar_fecha`), generando las matrices en `output/npy/` y las siluetas en `output/siluetas/`.
  5. Ejecuta la optimización inversa llamando a `ejecutar_algoritmo_genetico(datos_entrada)` para inferir las condiciones microclimáticas.
  6. Dispara la fase predictiva invocando `ejecutar_prediccion(...)`.
  7. Imprime el resumen consolidado de las rutas de todos los artefactos generados en `output/`.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

Este archivo no reimplementa lógica satelital, evolutiva ni cartográfica, sino que consume funciones definidas en otros módulos del proyecto:

### Provenientes de `ver_mapa_filtrado.py`:
- **`procesar_rango_fechas(fecha_inicio, fecha_fin)`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/ver_mapa_filtrado/functions.md`](../ver_mapa_filtrado/functions.md).
  - *Rol en `main.py`:* Procesa secuencialmente cada día del intervalo satelital, filtrando la región geográfica de Corrientes, dilatando a radio físico ($2$ iteraciones) y conservando los clusters con masa crítica ($k \ge 3$).
- **`procesar_fecha(fecha_elegida=None)`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/ver_mapa_filtrado/functions.md`](../ver_mapa_filtrado/functions.md).
  - *Rol en `main.py`:* Procesa una única fecha cuando se requiere de forma aislada.

### Provenientes de `algoritmo_genetico.py`:
- **`ejecutar_algoritmo_genetico(entradas_matrices)`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/algoritmo_genetico/functions.md`](../algoritmo_genetico/functions.md).
  - *Rol en `main.py`:* Ejecuta el ciclo evolutivo multinúcleo para encontrar la combinación óptima de viento, humedad y combustible.
- **`PASOS_POR_DIA`** *(Constante de configuración)*:
  - *Ubicación de la definición:* Documentada en [`docs/files/algoritmo_genetico/algoritmo_genetico.md`](../algoritmo_genetico/algoritmo_genetico.md).
  - *Rol en `main.py`:* Define la calibración temporal del autómata celular (30 ciclos de simulación = 24 horas reales).

### Provenientes de `simulador_predictivo.py`:
- **`ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA)`**:
  - *Ubicación de la definición:* Se encuentra definida y documentada en [`docs/files/simulador_predictivo/functions.md`](../simulador_predictivo/functions.md).
  - *Rol en `main.py`:* Toma las variables inferidas por el AG y proyecta el avance del fuego a +24h, +48h y +72h, orquestando las salidas gráficas GIS y HTML.

