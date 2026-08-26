import numpy as np
import random
import os
import multiprocessing
from functools import partial
from automata_celular import simular_incendio_AC, _avanzar_pasos_AC
from calcular_dimension_fractal import extraer_perimetro, calcular_box_counting

# ==============================================================================
# CONFIGURACIÓN DEL ALGORITMO GENÉTICO
# ==============================================================================
TAMANO_POBLACION = 20        # Cantidad de hipótesis climáticas por generación
GENERACIONES = 40             # Número de iteraciones evolutivas
PROB_MUTACION = 0.2          # Probabilidad de mutar un gen
PASOS_POR_DIA = 30           # CONSTANTE: Pasos de simulación del AC por día calendario (fácil de modificar)
NUM_SIMULACIONES = 3         # Cantidad de corridas Monte Carlo por individuo para mitigar ruido

def cargar_datos_serie_temporal(entradas):
    """
    Carga una o múltiples matrices satelitales (.npy) y calcula la Dimensión Fractal real
    de cada una para la evaluación multitemporal.
    
    Acepta:
      - Una ruta de archivo (str): "output/matriz_objetivo_limpia_2022-02-18.npy"
      - Una lista de tuplas: [("2022-02-17", "output/matriz_...npy"), ...]
    """
    if isinstance(entradas, str):
        # Modo día único
        entradas = [("Día_Único", entradas)]
        
    datos_serie = []
    matriz_acumulada = None
    
    for fecha, ruta in entradas:
        if not os.path.exists(ruta):
            print(f"Advertencia: No se encontró el archivo {ruta}. Se omitirá.")
            continue
            
        matriz_dia = np.load(ruta)
        
        if matriz_acumulada is None:
            matriz_acumulada = matriz_dia.copy()
        else:
            # Hacer que la matriz real sea acumulativa (cicatriz de fuego total)
            matriz_acumulada = np.logical_or(matriz_acumulada > 0, matriz_dia > 0).astype(int)
            
        matriz_real = matriz_acumulada.copy()
        perimetro_real = extraer_perimetro(matriz_real)
        
        try:
            D_real, *_ = calcular_box_counting(perimetro_real)
        except Exception:
            D_real = 1.0
            
        datos_serie.append({
            'fecha': fecha,
            'ruta': ruta,
            'matriz': matriz_real,
            'dimension_fractal': D_real
        })
        
        print(f" -> [{fecha}] Dimensión Fractal Satelital (D): {D_real:.4f} | Celdas acumuladas: {np.sum(matriz_real > 0)}")
        
    return datos_serie

def generar_individuo():
    """Genera un cromosoma aleatorio (hipótesis climática)."""
    # Vector de variables: [viento_vel, viento_dir, humedad, combustible]
    return [
        random.uniform(0, 50),     # viento_vel (km/h)
        random.uniform(0, 360),    # viento_dir (grados azimutales)
        random.uniform(10, 80),    # humedad (%)
        random.uniform(0.1, 1.0)   # combustible (índice 0-1)
    ]

def evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, num_simulaciones=NUM_SIMULACIONES):
    """
    Evalúa el fitness del individuo a lo largo de la evolución temporal del incendio.
    
    Si hay múltiples días (T0, T1, ... Tk):
      1. Inicializa el AC con el fuego del Día 0 (T0).
      2. Para cada transición (T0->T1, T1->T2, ...), avanza 'pasos_por_dia' pasos en el AC.
      3. Evalúa la concordancia (Fractal + IoU) contra la foto satelital real de cada día.
      4. Promedia el fitness obtenido entre todos los días evaluados.
      
    Promedia los resultados a lo largo de 'num_simulaciones' corridas Monte Carlo.
    """
    viento_vel, viento_dir, humedad, combustible = individuo
    total_dias = len(datos_serie)
    
    if total_dias == 0:
        return 0.0
        
    # --- CASO A: UN SOLO DÍA (Evaluación Estática) ---
    if total_dias == 1:
        matriz_real = datos_serie[0]['matriz']
        D_objetivo = datos_serie[0]['dimension_fractal']
        y_coords, x_coords = np.where(matriz_real > 0)
        cy = int(np.mean(y_coords)) if len(y_coords) > 0 else 128
        cx = int(np.mean(x_coords)) if len(x_coords) > 0 else 128
        
        suma_fitness = 0.0
        for _ in range(num_simulaciones):
            _, matriz_binaria = simular_incendio_AC(
                viento_vel=viento_vel, viento_dir=viento_dir, humedad=humedad, combustible=combustible,
                pasos_tiempo=100, centro_y=cy, centro_x=cx
            )
            perimetro = extraer_perimetro(matriz_binaria)
            try:
                D_sim, *_ = calcular_box_counting(perimetro)
            except Exception:
                D_sim = 0.0
            error_fractal = abs(D_objetivo - D_sim)
            fitness_fractal = 1.0 / (1.0 + error_fractal)
            interseccion = np.logical_and(matriz_real > 0, matriz_binaria > 0).sum()
            union = np.logical_or(matriz_real > 0, matriz_binaria > 0).sum()
            iou = (interseccion / union) if union > 0 else 0.0
            suma_fitness += (0.5 * fitness_fractal) + (0.5 * iou)
            
        return suma_fitness / num_simulaciones
        
    # --- CASO B: SERIE MULTITEMPORAL (Evolución Día a Día) ---
    suma_fitness_runs = 0.0
    
    for _ in range(num_simulaciones):
        # Iniciar grilla con el estado del día 0
        grilla_sim = np.copy(datos_serie[0]['matriz']).astype(int)
        if np.max(grilla_sim) == 1:
            grilla_sim[grilla_sim > 0] = 1
            
        fitness_por_etapa = []
        
        # Simular la transición hacia cada día sucesivo
        for t in range(1, total_dias):
            matriz_real_t = datos_serie[t]['matriz']
            D_objetivo_t = datos_serie[t]['dimension_fractal']
            
            # Avanzar la simulación continua 'pasos_por_dia' pasos
            grilla_sim = _avanzar_pasos_AC(
                grilla_sim, 
                viento_vel=viento_vel, 
                viento_dir=viento_dir, 
                humedad=humedad, 
                combustible=combustible, 
                pasos_tiempo=pasos_por_dia
            )
            
            matriz_binaria_sim = np.where(grilla_sim > 0, 1, 0)
            perimetro_sim = extraer_perimetro(matriz_binaria_sim)
            
            # 1. Fitness Fractal del día t
            try:
                D_sim_t, *_ = calcular_box_counting(perimetro_sim)
            except Exception:
                D_sim_t = 0.0
            error_fractal = abs(D_objetivo_t - D_sim_t)
            fitness_fractal = 1.0 / (1.0 + error_fractal)
            
            # 2. Superposición espacial (IoU) del día t
            interseccion = np.logical_and(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            union = np.logical_or(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            iou = (interseccion / union) if union > 0 else 0.0
            
            # 3. Fitness híbrido de la etapa
            fit_etapa = (0.4 * fitness_fractal) + (0.6 * iou)
            fitness_por_etapa.append(fit_etapa)
            
        # Promedio del fitness entre todas las transiciones diarias de esta simulación
        suma_fitness_runs += np.mean(fitness_por_etapa)
        
    return suma_fitness_runs / num_simulaciones

def cruzar(padre1, padre2):
    """Cruce de un punto."""
    punto_cruce = random.randint(1, len(padre1) - 1)
    hijo1 = padre1[:punto_cruce] + padre2[punto_cruce:]
    hijo2 = padre2[:punto_cruce] + padre1[punto_cruce:]
    return hijo1, hijo2

def mutar(individuo):
    """Muta un gen del individuo aleatoriamente."""
    if random.random() < PROB_MUTACION:
        gen_a_mutar = random.randint(0, 3)
        if gen_a_mutar == 0:
            individuo[0] = random.uniform(0, 50)
        elif gen_a_mutar == 1:
            individuo[1] = random.uniform(0, 360)
        elif gen_a_mutar == 2:
            individuo[2] = random.uniform(10, 80)
        elif gen_a_mutar == 3:
            individuo[3] = random.uniform(0.1, 1.0)
    return individuo

def seleccion_torneo(fitness_poblacion, k=3):
    """Selección por torneo: elige k individuos al azar y retorna el mejor."""
    participantes = random.sample(fitness_poblacion, k)
    participantes.sort(key=lambda x: x[1], reverse=True)
    return participantes[0][0]

def ejecutar_algoritmo_genetico(entradas_matrices):
    """
    Ejecuta el Algoritmo Genético de Optimización Inversa Multitemporal.
    Acepta una ruta única o una lista de tuplas [(fecha, ruta), ...].
    """
    print("="*60)
    print("INICIANDO OPTIMIZACIÓN INVERSA POR ALGORITMO GENÉTICO")
    print(f"Configuración: {GENERACIONES} Generaciones | {TAMANO_POBLACION} Individuos | {PASOS_POR_DIA} Pasos/Día")
    print("="*60)
    
    # 1. Cargar datos de la serie temporal
    datos_serie = cargar_datos_serie_temporal(entradas_matrices)
    if len(datos_serie) == 0:
        print("Error: No hay matrices válidas para optimizar.")
        return None
        
    print(f"\nSerie temporal cargada exitosamente: {len(datos_serie)} fechas analizadas.")
    if len(datos_serie) > 1:
        print(f"Se evaluarán {len(datos_serie) - 1} transiciones diarias continuas ({PASOS_POR_DIA} pasos AC cada una).")
    
    # 2. Inicializar población
    poblacion = [generar_individuo() for _ in range(TAMANO_POBLACION)]
    mejor_individuo_global = None
    mejor_fitness_global = -1.0
    
    # 3. Bucle evolutivo
    num_cpus = max(1, multiprocessing.cpu_count() - 1)  # Dejar un núcleo libre para el SO
    eval_func = partial(evaluar_fitness_multitemporal, datos_serie=datos_serie, pasos_por_dia=PASOS_POR_DIA)
    
    with multiprocessing.Pool(processes=num_cpus) as pool:
        for generacion in range(GENERACIONES):
            # Evaluar el fitness de toda la población en paralelo
            fitness_valores = pool.map(eval_func, poblacion)
            
            # Reconstruir la lista de tuplas (individuo, fitness)
            fitness_poblacion = list(zip(poblacion, fitness_valores))
            
            fitness_poblacion.sort(key=lambda x: x[1], reverse=True)
            mejor_ind_gen, mejor_fit_gen = fitness_poblacion[0]
            
            if mejor_fit_gen > mejor_fitness_global:
                mejor_fitness_global = mejor_fit_gen
                mejor_individuo_global = list(mejor_ind_gen)
                
            print(f"Gen {generacion+1:02d}/{GENERACIONES:02d} | Mejor Fitness: {mejor_fit_gen:.4f} | Viento: {mejor_ind_gen[0]:.1f}km/h @ {mejor_ind_gen[1]:.1f}° | Humedad: {mejor_ind_gen[2]:.1f}% | Comb: {mejor_ind_gen[3]:.2f}")
            
            # Elitismo: Conservar los 2 mejores
            NUM_ELITES = 2
            nueva_poblacion = [ind_fit[0] for ind_fit in fitness_poblacion[:NUM_ELITES]]
            
            # Reproducción (Torneo + Cruce + Mutación)
            while len(nueva_poblacion) < TAMANO_POBLACION:
                p1 = seleccion_torneo(fitness_poblacion, k=3)
                p2 = seleccion_torneo(fitness_poblacion, k=3)
                h1, _ = cruzar(p1, p2)
                nueva_poblacion.append(mutar(h1))
                
            poblacion = nueva_poblacion
        
    print("\n" + "="*60)
    print("OPTIMIZACIÓN INVERSA FINALIZADA")
    print(f"Mejor Fitness Multitemporal Alcanzado: {mejor_fitness_global:.4f}")
    print("Condiciones Microclimáticas Inferidas:")
    print(f" -> Velocidad del Viento: {mejor_individuo_global[0]:.2f} km/h")
    print(f" -> Dirección del Viento: {mejor_individuo_global[1]:.2f} grados")
    print(f" -> Humedad Relativa:     {mejor_individuo_global[2]:.2f} %")
    print(f" -> Carga de Combustible: {mejor_individuo_global[3]:.2f}")
    print("="*60)
    
    return mejor_individuo_global

