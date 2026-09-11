# Funciones de `automata_celular.py`

## 1. Funciones Definidas en este Archivo

<a id="_avanzar_pasos_AC"></a>
### `_avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256)`
- **Firma:** `def _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256):`
- **Descripción:** Función interna de alto rendimiento encargada de iterar el autómata celular durante un número determinado de pasos discretos (`pasos_tiempo`). Calcula previamente el vector de 8 probabilidades de propagación anisotrópica para la vecindad de Moore según la velocidad y ángulo del viento. En cada ciclo temporal, localiza exclusivamente las celdas en ignición (`grilla == 1`), las extingue a cenizas (`grilla = 2`) e intenta encender a sus vecinos circundantes intactos (`grilla == 0`). Si en algún ciclo el frente se extingue por completo (`len(y_ardiendo) == 0`), corta la iteración anticipadamente.
- **Parámetros:**
  - `grilla` (`numpy.ndarray` 2D): Matriz de estados actuales del autómata ($0, 1, 2$).
  - `viento_vel` (float): Velocidad del viento en km/h.
  - `viento_dir` (float): Dirección del viento en grados azimutales ($0^\circ$ a $360^\circ$).
  - `humedad` (float): Porcentaje de humedad relativa ($10\%$ a $80\%$).
  - `combustible` (float): Coeficiente de combustible vegetal ($0.1$ a $1.0$).
  - `pasos_tiempo` (int): Cantidad de ciclos a simular.
  - `tamano` (int, opcional): Dimensión espacial de la grilla cuadrada. Por defecto `256`.
- **Retorno:** `numpy.ndarray` 2D con la grilla actualizada tras completar los ciclos temporales.

---

<a id="simular_incendio_AC"></a>
### `simular_incendio_AC(viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, centro_y=None, centro_x=None, grilla_inicial=None)`
- **Firma:** `def simular_incendio_AC(viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, centro_y=None, centro_x=None, grilla_inicial=None):`
- **Descripción:** Wrapper principal para inicializar y ejecutar una simulación completa de propagación. Permite dos modalidades de arranque:
  1. **Desde un punto/ignición sintética:** Si `grilla_inicial` es `None`, crea una grilla vacía y coloca un foco inicial de $3 \times 3$ celdas ardiendo centrado en `(centro_y, centro_x)` (o en el centro geométrico de la grilla si no se especifican coordenadas).
  2. **Desde datos observados reales:** Si se proporciona `grilla_inicial`, clona la matriz y asigna estado `1` (ardiendo) a todos los píxeles encendidos preexistentes.
  Luego delega la propagación a `_avanzar_pasos_AC`.
- **Parámetros:**
  - `viento_vel`, `viento_dir`, `humedad`, `combustible`: Parámetros microclimáticos.
  - `pasos_tiempo` (int): Duración temporal de la simulación.
  - `tamano` (int, opcional): Tamaño de la grilla ($256$).
  - `centro_y`, `centro_x` (int, opcional): Coordenadas de ignición sintética inicial.
  - `grilla_inicial` (`numpy.ndarray`, opcional): Matriz inicial de partida.
- **Retorno:** Tupla `(grilla_estados, matriz_binaria_final)`:
  - `grilla_estados`: Matriz con valores discretos $\{0, 1, 2\}$.
  - `matriz_binaria_final`: Matriz binaria donde las celdas quemadas o ardiendo valen `1` y las intactas `0`.

---

<a id="simular_evolucion_multietapa"></a>
### `simular_evolucion_multietapa(viento_vel, viento_dir, humedad, combustible, grilla_inicial, pasos_por_dia, total_etapas, tamano=256)`
- **Firma:** `def simular_evolucion_multietapa(viento_vel, viento_dir, humedad, combustible, grilla_inicial, pasos_por_dia, total_etapas, tamano=256):`
- **Descripción:** Ejecuta una simulación temporal continua encadenada a lo largo de múltiples etapas sucesivas (por ejemplo, 3 etapas de 24 horas cada una para proyectar +24h, +48h y +72h). En cada etapa, avanza el autómata celular `pasos_por_dia` pasos acumulativos a partir del estado terminal de la etapa previa, capturando una instantánea binaria consolidada al finalizar cada período.
- **Parámetros:**
  - `viento_vel`, `viento_dir`, `humedad`, `combustible`: Variables microclimáticas.
  - `grilla_inicial` (`numpy.ndarray` 2D): Estado inicial del frente observado.
  - `pasos_por_dia` (int): Ciclos del AC correspondientes a 1 etapa diaria (típicamente $30$).
  - `total_etapas` (int): Cantidad de horizontes a proyectar (típicamente $3$ para 24h, 48h y 72h).
  - `tamano` (int, opcional): Dimensión de la grilla ($256$).
- **Retorno:** Tupla `(grilla_final, instantaneas_binarias)`:
  - `grilla_final`: Matriz de estados finales en la última etapa.
  - `instantaneas_binarias`: Lista de matrices binarias `[matriz_etapa_1, matriz_etapa_2, ...]`.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

*Este archivo no importa funciones ni constantes de otros módulos del proyecto.* Funciona como el motor físico fundamental de la simulación.

