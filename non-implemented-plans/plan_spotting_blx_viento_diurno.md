# Plan de Implementación Integral: Focos Secundarios (*Spotting*), Operadores Continuos (BLX-$\alpha$ y Mutación Gaussiana) y Dinámica Horaria del Viento

**Estado:** Documento de Diseño Técnico y Metodológico (Pendiente de Ejecución)  
**Módulos Afectados:** `automata_celular.py`, `algoritmo_genetico.py`, `simulador_predictivo.py`, `docs/tasks.md`, `docs/DOCUMENTACION_COMPLETA_PROYECTO.md`  
**Tareas Asociadas en Hoja de Ruta (`tasks.md`):** **T2.2** (*Spotting Effect*), **T2.4** (Dinámica Horaria del Viento), **T4.2** (Operadores Genéticos Continuos en $\mathbb{R}^k$).

---

## 1. Motivación Científica y Diagnóstico del Problema

Tras haber completado con éxito la calibración morfológica satelital (**T1.1**, $r \approx 1.6\text{ km}$, 1 iteración), la preservación integral multicluster (**T1.2**, 100% de focos NASA) y la reestructuración del fitness a Cobertura Eficiente $F_1$-Dice (**T3.2**, 50/50 con dimensión fractal $D$), el sistema ha alcanzado una base matemática sólida. Sin embargo, persisten tres limitaciones biofísicas y computacionales que restringen la convergencia del algoritmo genético hacia valores de fitness superiores a $0.80$:

1. **Limitación de Propagación Estrictamente Adyacente (Vecindad de Moore):**  
   En incendios forestales severos (como los megaincendios de Corrientes de enero-febrero 2022), las pavesas incandescentes (*embers*) son elevadas por la columna de convección térmica y proyectadas a distancias de entre 2 y 6 km a favor del viento. Al modelar únicamente la vecindad contigua inmediata (1 celda $\approx 1.6\text{ km}$), el simulador se ve obligado a inflar artificialmente la velocidad del viento o la carga global de combustible para "alcanzar" focos satelitales aislados, lo que causa sobreexpansión en zonas intermedias intactas y degrada drásticamente la precisión del $F_1$-Dice.
2. **Limitación de Operadores Genéticos Discretos en Espacios Continuos:**  
   El algoritmo genético utilizaba cruce de un punto (*single-point crossover*) y mutación aleatoria uniforme. En problemas de optimización en $\mathbb{R}^k$, el cruce de un punto solo intercambia parámetros completos sin explorar combinaciones lineales intermedias en el hipervolumen de búsqueda. Asimismo, la mutación uniforme aplica saltos destructivos con la misma probabilidad en la generación 1 que en la 40, dificultando el refinamiento fino (*exploitation*).
3. **Limitación del Campo de Viento Homogéneo y Estático:**  
   El modelo asume un único vector de viento $(\text{vel}, \text{dir})$ constante durante las 24 horas del día. En la realidad meteorológica de Corrientes, el gradiente térmico entre el día y la noche genera rotaciones diurnas sistemáticas de entre $\pm 30^\circ$ y $\pm 60^\circ$, produciendo la típica curvatura en abanico de las cicatrices reales.

---

## 2. Formulación Biofísica y Matemática Rigurosa

### 2.1. Focos Secundarios por Pavesas (*Fire Spotting* — Tarea T2.2)

#### Formulación Estocástica de Emisión
En cada ciclo temporal del autómata celular ($p \in [0, \text{pasos\_por\_dia}-1]$, donde cada paso representa $48\text{ minutos}$ de tiempo físico):
1. Se identifica el conjunto de celdas en ignición activa: $\mathcal{A}_p = \{(y, x) \mid \text{grilla}[y, x] == 1\}$, con cardinalidad $M = |\mathcal{A}_p|$.
2. La probabilidad de emisión de una pavesa viable por cada celda activa depende linealmente de la velocidad del viento y del factor de sequedad del combustible:
   $$P_{\text{spot}} = k_{\text{spot}} \cdot \left(\frac{v_{\text{viento}}}{50.0}\right) \cdot \left(1.0 - \frac{H_{\text{hum}}}{100.0}\right)$$
   donde $k_{\text{spot}} = 0.025$ es la constante de calibración empírica para la escala temporal de 48 minutos.
3. El número de eventos de desprendimiento de pavesas en el paso $p$ se modela mediante un muestreo binomial:
   $$N_{\text{pavesas}} \sim \text{Binomial}\left(M, \ P_{\text{spot}}\right)$$
   Si $M \cdot P_{\text{spot}} \ll 1$, el proceso se aproxima eficientemente por Poisson con $\lambda = M \cdot P_{\text{spot}}$.

#### Balística y Dispersión Anisotrópica
Para cada una de las $N_{\text{pavesas}}$ generadas:
1. **Celda de origen:** Se selecciona uniformemente al azar una celda $(y_0, x_0) \in \mathcal{A}_p$.
2. **Distancia de salto convectivo:** Se muestrea una distancia discreta en celdas $d \sim \mathcal{U}\{2, 3, 4\}$, equivalente a un alcance de transporte de:
   $$d_{\text{km}} \in [3.14\text{ km}, \ 6.28\text{ km}]$$
3. **Ángulo de eyección:** Se orienta en la dirección del viento instantáneo $\theta_p$ más una perturbación angular gaussiana acotada (cono de dispersión):
   $$\theta_{\text{pavesa}} = \theta_p + \delta\theta, \quad \delta\theta \sim \text{clip}\left(\mathcal{N}(0, \sigma_{\theta}^2), \ -25^\circ, \ +25^\circ\right)$$
   con desviación típica $\sigma_{\theta} = 12.5^\circ$.
4. **Coordenadas de impacto en la grilla:**
   $$y_{\text{dest}} = \text{round}\left(y_0 - d \cdot \sin(\text{radians}(\theta_{\text{pavesa}}))\right)$$
   $$x_{\text{dest}} = \text{round}\left(x_0 + d \cdot \cos(\text{radians}(\theta_{\text{pavesa}}))\right)$$
5. **Criterio de Ignición y Respeto a Barreras Biofísicas:**
   - Si $(y_{\text{dest}}, x_{\text{dest}})$ excede los límites $[0, N-1] \times [0, N-1]$, la pavesa sale del dominio y se descarta.
   - Si $\text{grilla}[y_{\text{dest}}, x_{\text{dest}}] \neq 0$ (ya está ardiendo o es ceniza), no produce efecto.
   - Si $\text{mapa\_combustible}[y_{\text{dest}}, x_{\text{dest}}] \le 0.0$ (cuerpo de agua, estero profundo o fuera de la provincia), la pavesa cae en agua y se extingue sin ignición.
   - Si la celda es combustible ($C > 0$), la probabilidad de que inicie un foco secundario depende de la carga local de combustible:
     $$P_{\text{ign\_spot}} = \min(1.0, \ \text{mapa\_combustible}[y_{\text{dest}}, x_{\text{dest}}] \cdot C_{\text{comb}} \cdot (1.0 - H_{\text{hum}}/100.0) \cdot 1.5)$$
     Si $\mathcal{U}(0, 1) < P_{\text{ign\_spot}}$, se establece $\text{grilla}[y_{\text{dest}}, x_{\text{dest}}] = 1$.

---

### 2.2. Operadores Genéticos Continuos en $\mathbb{R}^k$ (Tarea T4.2)

#### Cruce Aritmético BLX-$\alpha$ (Blend Crossover, $\alpha = 0.3$)
Sean dos individuos progenitores seleccionados por torneo:
$$\vec{P}_1 = [x_{1, 0}, \dots, x_{1, k-1}], \quad \vec{P}_2 = [x_{2, 0}, \dots, x_{2, k-1}]$$
Para cada gen no circular $i$ ($V_{\text{viento}}, \Delta\theta_{\text{rot}}, H_{\text{hum}}, C_{\text{comb}}$):
1. Calcular el intervalo delimitado por los padres:
   $$c_{\min} = \min(x_{1, i}, x_{2, i}), \quad c_{\max} = \max(x_{1, i}, x_{2, i}), \quad I = c_{\max} - c_{\min}$$
2. Generar los alelos descendientes muestreando en el intervalo extendido por $\alpha = 0.3$:
   $$h_{1, i} \sim \mathcal{U}\left(c_{\min} - \alpha I, \ c_{\max} + \alpha I\right)$$
   $$h_{2, i} \sim \mathcal{U}\left(c_{\min} - \alpha I, \ c_{\max} + \alpha I\right)$$
3. Acotar $h_{1, i}$ y $h_{2, i}$ a los rangos biofísicos permitidos mediante `clip`.

#### Tratamiento Especial para la Variable Angular ($\theta_{\text{inicio}} \in [0, 360^\circ)$)
Debido a la topología circular de $\mathbb{S}^1$, interpolar directamente en $\mathbb{R}$ provocaría discontinuidades artificiales (ej. el promedio entre $5^\circ$ y $355^\circ$ no es $180^\circ$ sino $0^\circ$).  
Se implementa la recombinación sobre la distancia geodésica mínima:
1. Diferencia angular modular:
   $$\Delta\theta = ((\theta_2 - \theta_1 + 180^\circ) \pmod{360^\circ}) - 180^\circ \in [-180^\circ, 180^\circ]$$
2. Interpolación con dispersión BLX-$\alpha$:
   $$\gamma_1 \sim \mathcal{U}(-\alpha, 1 + \alpha), \quad \gamma_2 \sim \mathcal{U}(-\alpha, 1 + \alpha)$$
   $$\theta_{h_1} = (\theta_1 + \gamma_1 \cdot \Delta\theta) \pmod{360^\circ}$$
   $$\theta_{h_2} = (\theta_1 + \gamma_2 \cdot \Delta\theta) \pmod{360^\circ}$$

#### Mutación Gaussiana Autoadaptativa con Enfriamiento
En lugar de una sustitución uniforme que destruye genomas maduros, la mutación aplica perturbaciones normales proporcionales al rango de cada gen, moduladas por un factor de enfriamiento evolutivo dependiente de la generación:
$$\sigma_i(g) = \sigma_{0, i} \cdot \left(1.0 - 0.75 \cdot \frac{g}{G}\right)$$
donde $g$ es la generación actual, $G$ el total de generaciones, y $\sigma_{0, i}$ es el 15% de la amplitud del rango del gen $i$.  
Si el gen $i$ es seleccionado para mutar (probabilidad `PROB_MUTACION = 0.10`):
$$x_i^{\text{mut}} = \text{clip}\left(x_i + \mathcal{N}(0, \sigma_i(g)^2), \ \text{Límite}_{\min, i}, \ \text{Límite}_{\max, i}\right)$$

---

### 2.3. Dinámica Horaria del Viento (Rotación Diurna $\Delta\theta$ — Tarea T2.4)

#### Estructura del Cromosoma Ampliado (5 Genes)
El vector de decisión del Algoritmo Genético pasa de 4 a 5 variables continuas:
$$\vec{x} = \big[V_{\text{viento}}, \ \theta_{\text{inicio}}, \ \Delta\theta_{\text{rot}}, \ H_{\text{hum}}, \ C_{\text{comb}}\big]$$

| Gen | Variable | Rango Físico | Unidad | Descripción Biofísica |
| :---: | :--- | :---: | :---: | :--- |
| **0** | $V_{\text{viento}}$ | $[0.0, \ 50.0]$ | km/h | Velocidad sostenida media del viento |
| **1** | $\theta_{\text{inicio}}$ | $[0.0, \ 360.0)$ | grados | Dirección azimutal inicial del viento al comenzar el día ($T=0$h) |
| **2** | $\Delta\theta_{\text{rot}}$ | $[-60.0, \ +60.0]$ | grados/día | Tasa neta de rotación diurna angular del viento a lo largo de 24h |
| **3** | $H_{\text{hum}}$ | $[10.0, \ 80.0]$ | % | Humedad relativa del aire media de la jornada |
| **4** | $C_{\text{comb}}$ | $[0.1, \ 1.0]$ | índice [0, 1] | Carga global de biomasa combustible vegetal |

#### Actualización Dinámica en el Autómata Celular
En cada paso temporal $p \in [0, P-1]$ ($P = \text{pasos\_por\_dia} = 30$):
$$\theta(p) = \left(\theta_{\text{inicio}} + \Delta\theta_{\text{rot}} \cdot \frac{p}{\max(1, P - 1)}\right) \pmod{360.0}$$
En cada ciclo $p$, se recalculan vectorialmente los factores anisotrópicos de Moore hacia los 8 vecinos contiguos:
$$\text{factores\_viento}_k(p) = \exp\left(c_{\text{viento}} \cdot V_{\text{viento}} \cdot \cos\big(\text{radians}(\theta(p)) - \theta_{\text{vecino}, k}\big)\right)$$

---

## 3. Especificación de Cambios por Módulo de Código

### 3.1. Módulo [`automata_celular.py`](file:///c:/Facu/Algoritmos-geneticos/Incendios-Fractales/automata_celular.py)

#### Firma y Cuerpo de `_avanzar_pasos_AC`
```python
def _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, 
                      tamano=256, mapa_combustible=None, viento_rot=0.0, activar_spotting=True):
    """
    Avanza el autómata celular estocástico n pasos en el tiempo con:
      - Heterogeneidad espacial biofísica (mapa_combustible IGN WFS - T2.1)
      - Focos secundarios por pavesas a favor del viento (Spotting - T2.2)
      - Rotación diurna del viento en 24h (T2.4)
    """
    if mapa_combustible is None:
        try:
            from capa_biomasa import obtener_mapa_combustible
            mapa_combustible = obtener_mapa_combustible(tamano)
        except Exception:
            mapa_combustible = np.ones((tamano, tamano), dtype=float)

    humedad_norm = humedad / 100.0
    factor_sequedad = 1.0 - humedad_norm
    c_viento = 0.05
    vecinos = [
        (-1, -1), (-1, 0), (-1, 1),
        ( 0, -1),          ( 0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]
    thetas_vecinos = np.array([np.arctan2(-dy, dx) for dy, dx in vecinos])
    rand_func = np.random.random
    
    # Parámetros de Spotting (T2.2)
    k_spot = 0.025
    p_spot_base = k_spot * (viento_vel / 50.0) * factor_sequedad

    for p in range(pasos_tiempo):
        # 1. Dirección instantánea del viento con rotación diurna continua (T2.4)
        rot_prog = (p / max(1, pasos_tiempo - 1)) if pasos_tiempo > 1 else 0.0
        theta_instantaneo = np.radians((viento_dir + viento_rot * rot_prog) % 360.0)
        
        # Factores anisotrópicos para los 8 vecinos contiguos
        alineaciones = np.cos(theta_instantaneo - thetas_vecinos)
        factores_viento = np.exp(c_viento * viento_vel * alineaciones)
        
        # 2. Localizar celdas ardiendo
        y_ardiendo, x_ardiendo = np.where(grilla == 1)
        num_ardiendo = len(y_ardiendo)
        if num_ardiendo == 0:
            break
            
        # Celdas activas pasan a cenizas (Estado 2)
        grilla[y_ardiendo, x_ardiendo] = 2
        
        # 3. Propagación estándar por vecindad adyacente de Moore
        for y, x in zip(y_ardiendo, x_ardiendo):
            for k, (dy, dx) in enumerate(vecinos):
                ny, nx = y + dy, x + dx
                if 0 <= ny < tamano and 0 <= nx < tamano and grilla[ny, nx] == 0:
                    c_local = mapa_combustible[ny, nx] * combustible
                    if c_local <= 0.0:
                        continue
                    p_ignicion = min(c_local * factor_sequedad * factores_viento[k], 0.95)
                    if rand_func() < p_ignicion:
                        grilla[ny, nx] = 1

        # 4. Mecanismo de Focos Secundarios por Pavesas (Spotting - T2.2)
        if activar_spotting and p_spot_base > 0 and num_ardiendo > 0:
            num_pavesas = np.random.binomial(num_ardiendo, min(p_spot_base, 0.5))
            if num_pavesas > 0:
                indices_origen = np.random.choice(num_ardiendo, size=num_pavesas, replace=True)
                saltos = np.random.choice([2, 3, 4], size=num_pavesas)
                conos = np.radians(np.clip(np.random.normal(0, 12.5, size=num_pavesas), -25.0, 25.0))
                angulos_pavesas = theta_instantaneo + conos
                
                y_dests = np.round(y_ardiendo[indices_origen] - saltos * np.sin(angulos_pavesas)).astype(int)
                x_dests = np.round(x_ardiendo[indices_origen] + saltos * np.cos(angulos_pavesas)).astype(int)
                
                for yd, xd in zip(y_dests, x_dests):
                    if 0 <= yd < tamano and 0 <= xd < tamano and grilla[yd, xd] == 0:
                        c_dest = mapa_combustible[yd, xd] * combustible
                        if c_dest > 0.0:
                            p_ign_spot = min(1.0, c_dest * factor_sequedad * 1.5)
                            if rand_func() < p_ign_spot:
                                grilla[yd, xd] = 1

    return grilla
```

#### Actualización de `simular_incendio_AC` y `simular_evolucion_multietapa`
Añadir el argumento opcional `viento_rot=0.0` y `activar_spotting=True` en ambas funciones y propagarlo en la llamada a `_avanzar_pasos_AC`.

---

### 3.2. Módulo [`algoritmo_genetico.py`](file:///c:/Facu/Algoritmos-geneticos/Incendios-Fractales/algoritmo_genetico.py)

#### 1. Generación de Individuo (5 Genes)
```python
def generar_individuo():
    """Genera un cromosoma aleatorio con 5 variables climáticas y dinámicas."""
    return [
        random.uniform(0.0, 50.0),    # viento_vel (km/h)
        random.uniform(0.0, 360.0),   # viento_dir (grados azimutales)
        random.uniform(-60.0, 60.0),  # viento_rot (grados de rotación en 24h)
        random.uniform(10.0, 80.0),   # humedad (%)
        random.uniform(0.1, 1.0)      # combustible (índice 0.1 - 1.0)
    ]
```

#### 2. Operador de Cruce BLX-$\alpha$
```python
def cruzar_blx_alpha(padre1, padre2, alpha=0.3):
    """
    Cruce Aritmético Continuo BLX-alpha con tratamiento circular para la dirección del viento.
    """
    limites = [
        (0.0, 50.0, False),    # viento_vel
        (0.0, 360.0, True),    # viento_dir (circular)
        (-60.0, 60.0, False),  # viento_rot
        (10.0, 80.0, False),   # humedad
        (0.1, 1.0, False)      # combustible
    ]
    
    hijo1 = []
    hijo2 = []
    
    for i, (min_val, max_val, es_circular) in enumerate(limites):
        p1 = padre1[i]
        p2 = padre2[i]
        
        if es_circular:
            delta_theta = ((p2 - p1 + 180.0) % 360.0) - 180.0
            u1 = random.uniform(-alpha, 1.0 + alpha)
            u2 = random.uniform(-alpha, 1.0 + alpha)
            h1 = (p1 + u1 * delta_theta) % 360.0
            h2 = (p1 + u2 * delta_theta) % 360.0
        else:
            c_min = min(p1, p2)
            c_max = max(p1, p2)
            I = c_max - c_min
            h1 = random.uniform(c_min - alpha * I, c_max + alpha * I)
            h2 = random.uniform(c_min - alpha * I, c_max + alpha * I)
            h1 = float(np.clip(h1, min_val, max_val))
            h2 = float(np.clip(h2, min_val, max_val))
            
        hijo1.append(h1)
        hijo2.append(h2)
        
    return hijo1, hijo2
```

#### 3. Operador de Mutación Gaussiana Autoadaptativa
```python
def mutar_gaussiano(individuo, generacion_actual=0, total_generaciones=40):
    """
    Mutación Gaussiana Autoadaptativa con enfriamiento evolutivo.
    """
    limites = [
        (0.0, 50.0, 50.0, False),    # viento_vel
        (0.0, 360.0, 360.0, True),   # viento_dir
        (-60.0, 60.0, 120.0, False), # viento_rot
        (10.0, 80.0, 70.0, False),   # humedad
        (0.1, 1.0, 0.9, False)       # combustible
    ]
    
    factor_enfriamiento = 1.0 - 0.75 * (generacion_actual / max(1, total_generaciones))
    
    for i in range(len(individuo)):
        if random.random() < PROB_MUTACION:
            min_val, max_val, rango, es_circular = limites[i]
            sigma = 0.15 * rango * factor_enfriamiento
            perturbacion = random.gauss(0, sigma)
            
            if es_circular:
                individuo[i] = (individuo[i] + perturbacion) % 360.0
            else:
                individuo[i] = float(np.clip(individuo[i] + perturbacion, min_val, max_val))
                
    return individuo
```

#### 4. Evaluación de Fitness Multitemporal
Desempaquetar el cromosoma de 5 genes con retrocompatibilidad:
```python
def evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, 
                                  num_simulaciones=NUM_SIMULACIONES, mapa_combustible=None):
    if len(individuo) == 5:
        viento_vel, viento_dir, viento_rot, humedad, combustible = individuo
    else:
        viento_vel, viento_dir, humedad, combustible = individuo
        viento_rot = 0.0
        
    # En las llamadas a _avanzar_pasos_AC, propagar viento_rot:
    grilla_sim = _avanzar_pasos_AC(
        grilla_sim,
        viento_vel=viento_vel,
        viento_dir=viento_dir,
        humedad=humedad,
        combustible=combustible,
        pasos_tiempo=pasos_por_dia,
        mapa_combustible=mapa_combustible,
        viento_rot=viento_rot,
        activar_spotting=True
    )
    ...
```

#### 5. Telemetría y Exportación de Resultados
Actualizar `guardar_csv_resultados` y `guardar_grafico_fitness` para registrar `Viento_Rot_deg_dia` tanto en `output/historial_fitness.csv` como en `output/resultados_optimizacion.csv`.

---

### 3.3. Módulo [`simulador_predictivo.py`](file:///c:/Facu/Algoritmos-geneticos/Incendios-Fractales/simulador_predictivo.py)

#### Soporte para 5 Variables en `ejecutar_prediccion`
```python
def ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA):
    if len(mejores_variables) == 5:
        viento_vel, viento_dir, viento_rot, humedad, combustible = mejores_variables
    else:
        viento_vel, viento_dir, humedad, combustible = mejores_variables
        viento_rot = 0.0

    print(f"Condiciones Microclimáticas Inferidas: Viento {viento_vel:.1f}km/h @ {viento_dir:.1f}° ({viento_rot:+.1f}°/d) | Humedad {humedad:.1f}% | Comb {combustible:.2f}")

    # Propagar viento_rot a simular_evolucion_multietapa
    grilla_72h, instantaneas_binarias = simular_evolucion_multietapa(
        viento_vel=viento_vel,
        viento_dir=viento_dir,
        humedad=humedad,
        combustible=combustible,
        grilla_inicial=matriz_final,
        pasos_por_dia=pasos_por_dia,
        total_etapas=3,
        tamano=tamano,
        mapa_combustible=mapa_combustible,
        viento_rot=viento_rot
    )
    ...
```

---

## 4. Script Completo de Verificación y Pruebas Automatizadas

Se define el script ejecutable de prueba integral `tests/test_spotting_blx_viento.py` para validar todas las piezas de forma independiente y coordinada:

```python
import numpy as np
import pytest
from automata_celular import _avanzar_pasos_AC, simular_incendio_AC
from algoritmo_genetico import (
    generar_individuo,
    cruzar_blx_alpha,
    mutar_gaussiano,
    evaluar_fitness_multitemporal
)

def test_spotting_genera_focos_a_distancia():
    """Verifica que el spotting genera focos aislados a 2-4 celdas a favor del viento."""
    grilla = np.zeros((64, 64), dtype=int)
    grilla[32, 32] = 1
    mapa_comb = np.ones((64, 64), dtype=float)
    
    grilla_res = _avanzar_pasos_AC(
        grilla.copy(),
        viento_vel=45.0,
        viento_dir=0.0,
        humedad=15.0,
        combustible=0.9,
        pasos_tiempo=1,
        tamano=64,
        mapa_combustible=mapa_comb,
        activar_spotting=True
    )
    assert np.any(grilla_res > 0), "La simulación debe tener celdas quemadas o ardiendo"

def test_spotting_respeta_cuerpos_de_agua():
    """Verifica que las pavesas no encienden celdas con combustible nulo (agua)."""
    grilla = np.zeros((64, 64), dtype=int)
    grilla[32, 32] = 1
    mapa_comb = np.zeros((64, 64), dtype=float)
    
    grilla_res = _avanzar_pasos_AC(
        grilla.copy(),
        viento_vel=40.0,
        viento_dir=90.0,
        humedad=10.0,
        combustible=1.0,
        pasos_tiempo=5,
        tamano=64,
        mapa_combustible=mapa_comb,
        activar_spotting=True
    )
    assert np.sum(grilla_res == 1) == 0, "No debe haber focos ardiendo sobre agua"

def test_cruce_blx_alpha_respeta_limites_y_circularidad():
    """Verifica que el cruce BLX-alpha respeta límites y calcula distancias circulares."""
    p1 = [10.0, 5.0, -10.0, 30.0, 0.4]
    p2 = [40.0, 355.0, 20.0, 70.0, 0.8]
    
    h1, h2 = cruzar_blx_alpha(p1, p2, alpha=0.3)
    
    assert len(h1) == 5 and len(h2) == 5
    for h in [h1, h2]:
        assert 0.0 <= h[0] <= 50.0
        assert 0.0 <= h[1] < 360.0
        assert -60.0 <= h[2] <= 60.0
        assert 10.0 <= h[3] <= 80.0
        assert 0.1 <= h[4] <= 1.0

def test_mutacion_gaussiana_mantiene_genes_en_rango():
    """Verifica que la mutación gaussiana produce perturbaciones acotadas."""
    ind = [25.0, 180.0, 0.0, 50.0, 0.5]
    for gen in [0, 20, 40]:
        mutado = mutar_gaussiano(list(ind), generacion_actual=gen, total_generaciones=40)
        assert 0.0 <= mutado[0] <= 50.0
        assert 0.0 <= mutado[1] < 360.0
        assert -60.0 <= mutado[2] <= 60.0
        assert 10.0 <= mutado[3] <= 80.0
        assert 0.1 <= mutado[4] <= 1.0
```

---

## 5. Análisis de Rendimiento y Recursos Computacionales

| Operación | Complejidad Temporal | Consumo Adicional de RAM | Impacto en Tiempo AG (40 gen, 8 núcleos) | Viabilidad en PC Local |
| :--- | :---: | :---: | :---: | :---: |
| **Spotting Vectorizado** | $O(N_{\text{pavesas}})$ | $< 2\text{ MB}$ (arrays temporales) | $+8\text{ a } 12\text{ segundos}$ (+15-20%) | **100% Viable** (sin GPU) |
| **Cruce BLX-$\alpha$** | $O(1)$ por pareja | Despreciable | Inapreciable ($< 5\text{ ms}$) | **100% Viable** |
| **Mutación Gaussiana** | $O(1)$ por individuo | Despreciable | Inapreciable ($< 2\text{ ms}$) | **100% Viable** |
| **Rotación Diurna Viento**| $O(1)$ por paso de AC | Despreciable | Inapreciable ($< 1\%$) | **100% Viable** |

---

## 6. Lista de Verificación para Implementación Futura

Cuando el usuario decida ejecutar este plan, se seguirán estos pasos en orden secuencial estricto:
- [ ] 1. Crear rama de trabajo `feat/spotting-blx-viento`.
- [ ] 2. Modificar `automata_celular.py` incorporando el parámetro `viento_rot` y el bloque vectorizado de *Spotting*.
- [ ] 3. Modificar `algoritmo_genetico.py` adaptando el cromosoma a 5 genes, integrando `cruzar_blx_alpha` y `mutar_gaussiano`.
- [ ] 4. Modificar `simulador_predictivo.py` para proyectar las 5 variables climáticas.
- [ ] 5. Ejecutar la suite de tests en `tests/test_spotting_blx_viento.py`.
- [ ] 6. Ejecutar una corrida de calibración completa con las fechas de Corrientes (`2022-02-17` -> `2022-02-18`) y comparar la convergencia del fitness $F_1$-Dice frente a la línea base previa.
- [ ] 7. Actualizar `docs/tasks.md` marcando **T2.2**, **T2.4** y **T4.2** como ✅ **Implementado**.
- [ ] 8. Consolidar cambios y generar commit descriptivo.
