import numpy as np
import random
import os
import csv
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
from automata_celular import simular_incendio_AC, _avanzar_pasos_AC
from calcular_dimension_fractal import extraer_perimetro, calcular_box_counting, calcular_dimension_fractal_directa

# ==============================================================================
# CONFIGURACIÓN DEL ALGORITMO GENÉTICO
# ==============================================================================
TAMANO_POBLACION = 32        # Cantidad de hipótesis climáticas por generación
GENERACIONES = 40             # Número de iteraciones evolutivas
PROB_MUTACION = 0.2          # Probabilidad de mutar un gen
PASOS_POR_DIA = 30         # CONSTANTE: Pasos de simulación del AC por día calendario (fácil de modificar)
NUM_SIMULACIONES = 5         # Cantidad de corridas Monte Carlo por individuo para mitigar ruido

# PONDERACIÓN DE LA FUNCIÓN DE APTITUD (FITNESS HÍBRIDO)
PESO_FRACTAL = 0.5           # Peso asignado a la Dimensión Fractal del perímetro/frente activo
PESO_IOU = 0.5               # Peso asignado a la Superposición Espacial (IoU)

def cargar_datos_serie_temporal(entradas):
    """
    Carga una o múltiples matrices satelitales (.npy) y calcula la Dimensión Fractal real
    de cada una para la evaluación multitemporal.
    
    Acepta:
      - Una ruta de archivo (str): "output/matriz_objetivo_limpia_2022-02-18.npy"
      - Una lista de tuplas: [("2022-02-17", "output/matriz_...npy"), ...]
    """
    if isinstance(entradas, str):
        entradas = [("Día_Único", entradas)]
        
    datos_serie = []
    matriz_acumulada = None
    
    for fecha, ruta in entradas:
        if not os.path.exists(ruta):
            nombre_solo = os.path.basename(ruta)
            ruta_alt1 = os.path.join('output', 'npy', nombre_solo)
            ruta_alt2 = os.path.join('output', nombre_solo)
            if os.path.exists(ruta_alt1):
                ruta = ruta_alt1
            elif os.path.exists(ruta_alt2):
                ruta = ruta_alt2
            else:
                print(f"Advertencia: No se encontró el archivo {ruta}. Se omitirá.")
                continue
            
        matriz_dia = np.load(ruta)
        
        if matriz_acumulada is None:
            matriz_acumulada = matriz_dia.copy()
        else:
            # Hacer que la matriz real sea acumulativa (cicatriz de fuego total)
            matriz_acumulada = np.logical_or(matriz_acumulada > 0, matriz_dia > 0).astype(int)
            
        matriz_real = matriz_acumulada.copy()
        # T1.5: Dimensión fractal directa sobre el frente activo multicluster
        D_real = calcular_dimension_fractal_directa(matriz_real)
            
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

def evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, num_simulaciones=NUM_SIMULACIONES, mapa_combustible=None):
    """
    Evalúa la aptitud de un individuo contra la serie temporal satelital real.
    Incorpora la capa raster de cobertura de suelo y biomasa real (Tarea T2.1).
    
    Principio físico-metodológico:
      El punto de partida de la simulación son siempre las celdas correspondientes
      a los puntos de calor del día de inicio (T0). Desde allí, el autómata celular
      se expande a las demás zonas buscando reproducir la evolución observada
      en los días sucesivos (T1, ..., Tk).
      
    Promedia los resultados a lo largo de 'num_simulaciones' corridas Monte Carlo.
    """
    viento_vel, viento_dir, humedad, combustible = individuo
    total_dias = len(datos_serie)
    
    if total_dias == 0:
        return 0.0
        
    # --- CASO A: UN SOLO DÍA (Punto de partida en celdas iniciales y expansión de prueba) ---
    if total_dias == 1:
        matriz_real = datos_serie[0]['matriz']
        D_objetivo = datos_serie[0]['dimension_fractal']
        
        suma_fitness = 0.0
        for _ in range(num_simulaciones):
            # Inicializar la grilla con los puntos de calor del día de inicio
            grilla_sim = np.copy(matriz_real).astype(int)
            if np.max(grilla_sim) == 1:
                grilla_sim[grilla_sim > 0] = 1
                
            # Avanzar expansión desde las celdas de calor iniciales con heterogeneidad de biomasa
            grilla_sim = _avanzar_pasos_AC(
                grilla_sim,
                viento_vel=viento_vel,
                viento_dir=viento_dir,
                humedad=humedad,
                combustible=combustible,
                pasos_tiempo=pasos_por_dia,
                mapa_combustible=mapa_combustible
            )
            matriz_binaria = np.where(grilla_sim > 0, 1, 0)
            
            D_sim = calcular_dimension_fractal_directa(matriz_binaria)
            error_fractal = abs(D_objetivo - D_sim)
            fitness_fractal = 1.0 / (1.0 + error_fractal)
            interseccion = np.logical_and(matriz_real > 0, matriz_binaria > 0).sum()
            union = np.logical_or(matriz_real > 0, matriz_binaria > 0).sum()
            iou = (interseccion / union) if union > 0 else 0.0
            suma_fitness += (PESO_FRACTAL * fitness_fractal) + (PESO_IOU * iou)
            
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
            
            # Avanzar la simulación continua 'pasos_por_dia' pasos con heterogeneidad de biomasa
            grilla_sim = _avanzar_pasos_AC(
                grilla_sim, 
                viento_vel=viento_vel, 
                viento_dir=viento_dir, 
                humedad=humedad, 
                combustible=combustible, 
                pasos_tiempo=pasos_por_dia,
                mapa_combustible=mapa_combustible
            )
            
            matriz_binaria_sim = np.where(grilla_sim > 0, 1, 0)
            
            # 1. Fitness Fractal del día t (Directo sobre frente activo T1.5)
            D_sim_t = calcular_dimension_fractal_directa(matriz_binaria_sim)
            error_fractal = abs(D_objetivo_t - D_sim_t)
            fitness_fractal = 1.0 / (1.0 + error_fractal)
            
            # 2. Superposición espacial (IoU) del día t
            interseccion = np.logical_and(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            union = np.logical_or(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            iou = (interseccion / union) if union > 0 else 0.0
            
            # 3. Fitness híbrido de la etapa
            fit_etapa = (PESO_FRACTAL * fitness_fractal) + (PESO_IOU * iou)
            fitness_por_etapa.append(fit_etapa)
            
        # Promedio del fitness entre todas las transiciones diarias de esta simulación
        suma_fitness_runs += np.mean(fitness_por_etapa)
        
    return suma_fitness_runs / num_simulaciones

def _evaluar_individuo_worker(args):
    """Función de nivel superior para ejecución limpia y sin problemas de serialización en Windows y Mac."""
    if len(args) == 5:
        individuo, datos_serie, pasos_por_dia, num_simulaciones, mapa_combustible = args
    else:
        individuo, datos_serie, pasos_por_dia, num_simulaciones = args
        mapa_combustible = None
        
    fit = evaluar_fitness_multitemporal(
        individuo=individuo,
        datos_serie=datos_serie,
        pasos_por_dia=pasos_por_dia,
        num_simulaciones=num_simulaciones,
        mapa_combustible=mapa_combustible
    )
    return (individuo, fit)

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

def guardar_grafico_fitness(historial, ruta_salida='output/curva_fitness.png'):
    """Genera y guarda el gráfico de convergencia del récord global acumulado y el fitness promedio."""
    generaciones = [h['generacion'] for h in historial]
    mejores_globales = [h['mejor_fitness'] for h in historial]
    promedios = [h['promedio_fitness'] for h in historial]
    
    plt.figure(figsize=(10, 6))
    plt.plot(generaciones, mejores_globales, 'g-o', linewidth=2, label='Mejor Fitness (Récord Global)')
    if 'mejor_fitness_gen' in historial[0]:
        mejores_gen = [h['mejor_fitness_gen'] for h in historial]
        plt.plot(generaciones, mejores_gen, 'g--', alpha=0.35, linewidth=1.2, label='Mejor de la Generación')
    plt.plot(generaciones, promedios, 'b--s', linewidth=1.5, label='Fitness Promedio')
    plt.title(f"Evolución del Fitness por Generación (Ponderación {PESO_FRACTAL}*Fractal + {PESO_IOU}*IoU)", fontsize=13, pad=15)
    plt.xlabel("Generación", fontsize=12)
    plt.ylabel(f"Fitness Híbrido ({PESO_FRACTAL}*Fractal + {PESO_IOU}*IoU)", fontsize=12)
    plt.ylim(0.0, 1.0)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    plt.savefig(ruta_salida, dpi=300)
    plt.close()
    print(f" -> Gráfica de convergencia exportada a: {ruta_salida}")

def guardar_csv_resultados(historial, mejor_individuo, mejor_fitness):
    """Exporta el historial de telemetría y el resultado final a archivos CSV."""
    os.makedirs('output', exist_ok=True)
    
    ruta_historial = 'output/historial_fitness.csv'
    with open(ruta_historial, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Generacion', 'Mejor_Fitness_Global', 'Mejor_Fitness_Gen', 'Promedio_Fitness', 'Viento_Vel_kmh', 'Viento_Dir_deg', 'Humedad_pct', 'Combustible'])
        for h in historial:
            writer.writerow([
                h['generacion'],
                f"{h['mejor_fitness']:.6f}",
                f"{h.get('mejor_fitness_gen', h['mejor_fitness']):.6f}",
                f"{h['promedio_fitness']:.6f}",
                f"{h['viento_vel']:.2f}",
                f"{h['viento_dir']:.2f}",
                f"{h['humedad']:.2f}",
                f"{h['combustible']:.3f}"
            ])
    print(f" -> Historial de fitness exportado a: {ruta_historial}")

    ruta_resumen = 'output/resultados_optimizacion.csv'
    with open(ruta_resumen, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Parametro', 'Valor_Inferido', 'Unidad'])
        writer.writerow(['Mejor_Fitness_Alcanzado', f"{mejor_fitness:.6f}", "Índice (0-1)"])
        writer.writerow(['Velocidad_Viento', f"{mejor_individuo[0]:.2f}", "km/h"])
        writer.writerow(['Direccion_Viento', f"{mejor_individuo[1]:.2f}", "grados azimutales"])
        writer.writerow(['Humedad_Relativa', f"{mejor_individuo[2]:.2f}", "%"])
        writer.writerow(['Carga_Combustible', f"{mejor_individuo[3]:.3f}", "índice (0.1-1.0)"])
        writer.writerow(['Peso_Fractal_Utilizado', f"{PESO_FRACTAL:.2f}", "ponderación"])
        writer.writerow(['Peso_IoU_Utilizado', f"{PESO_IOU:.2f}", "ponderación"])
    print(f" -> Resultados finales de optimización exportados a: {ruta_resumen}")

def ejecutar_algoritmo_genetico(entradas_matrices):
    """
    Ejecuta el Algoritmo Genético de Optimización Inversa Multitemporal con evaluación multinúcleo en paralelo.
    """
    num_cpus = os.cpu_count() or 4
    num_workers = max(1, num_cpus - 1)
    
    print("="*60)
    print("INICIANDO OPTIMIZACIÓN INVERSA PARALELA POR ALGORITMO GENÉTICO")
    print(f"Configuración: {GENERACIONES} Generaciones | {TAMANO_POBLACION} Individuos | {PASOS_POR_DIA} Pasos/Día")
    print(f"Ponderación Fitness: {PESO_FRACTAL} * Dimensión Fractal + {PESO_IOU} * IoU Espacial")
    print(f"Aceleración por Multiprocesamiento: {num_workers} núcleos CPU activos")
    print("="*60)
    
    # 1. Cargar datos de la serie temporal
    datos_serie = cargar_datos_serie_temporal(entradas_matrices)
    if len(datos_serie) == 0:
        print("Error: No hay matrices válidas para optimizar.")
        return None
        
    print(f"\nSerie temporal cargada exitosamente: {len(datos_serie)} fechas analizadas.")
    if len(datos_serie) > 1:
        print(f"Se evaluarán {len(datos_serie) - 1} transiciones diarias continuas ({PASOS_POR_DIA} pasos AC cada una).")
    
    # 2. Inicializar población y mapa de combustible biofísico (Tarea T2.1)
    tamano = datos_serie[0]['matriz'].shape[0] if len(datos_serie) > 0 else 256
    try:
        from capa_biomasa import obtener_mapa_combustible
        mapa_combustible = obtener_mapa_combustible(tamano)
    except Exception:
        mapa_combustible = None
        
    poblacion = [generar_individuo() for _ in range(TAMANO_POBLACION)]
    mejor_individuo_global = None
    mejor_fitness_global = -1.0
    historial_telemetria = []
    
    # 3. Bucle evolutivo multinúcleo
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for generacion in range(GENERACIONES):
            tareas = [(ind, datos_serie, PASOS_POR_DIA, NUM_SIMULACIONES, mapa_combustible) for ind in poblacion]
            fitness_poblacion = list(executor.map(_evaluar_individuo_worker, tareas))
            
            fitness_poblacion.sort(key=lambda x: x[1], reverse=True)
            mejor_ind_gen, mejor_fit_gen = fitness_poblacion[0]
            avg_fit_gen = np.mean([fit for _, fit in fitness_poblacion])
            
            if mejor_fit_gen > mejor_fitness_global:
                mejor_fitness_global = mejor_fit_gen
                mejor_individuo_global = list(mejor_ind_gen)
                
            historial_telemetria.append({
                'generacion': generacion + 1,
                'mejor_fitness': mejor_fitness_global,
                'mejor_fitness_gen': mejor_fit_gen,
                'promedio_fitness': avg_fit_gen,
                'viento_vel': mejor_individuo_global[0],
                'viento_dir': mejor_individuo_global[1],
                'humedad': mejor_individuo_global[2],
                'combustible': mejor_individuo_global[3]
            })
            
            print(f"Gen {generacion+1:02d}/{GENERACIONES:02d} | Récord Global: {mejor_fitness_global:.4f} (Gen: {mejor_fit_gen:.4f}, Prom: {avg_fit_gen:.4f}) | Viento: {mejor_individuo_global[0]:.1f}km/h @ {mejor_individuo_global[1]:.1f}° | Humedad: {mejor_individuo_global[2]:.1f}% | Comb: {mejor_individuo_global[3]:.2f}")
            
            # Elitismo: Conservar los 2 mejores
            NUM_ELITES = 2
            nueva_poblacion = [list(ind_fit[0]) for ind_fit in fitness_poblacion[:NUM_ELITES]]
            
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
    
    guardar_grafico_fitness(historial_telemetria)
    guardar_csv_resultados(historial_telemetria, mejor_individuo_global, mejor_fitness_global)
    
    return mejor_individuo_global

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        from ver_mapa_filtrado import procesar_rango_fechas
        entradas = procesar_rango_fechas(sys.argv[1], sys.argv[2])
        if entradas:
            ejecutar_algoritmo_genetico(entradas)

