import numpy as np
import random
import os
import csv
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
from automata_celular import simular_incendio_AC, _avanzar_pasos_AC
from calcular_dimension_fractal import extraer_perimetro, calcular_box_counting

# ==============================================================================
# CONFIGURACIÓN DEL ALGORITMO GENÉTICO
# ==============================================================================
TAMANO_POBLACION = 20        # Cantidad de hipótesis climáticas por generación
GENERACIONES = 40             # Número de iteraciones evolutivas
PROB_MUTACION = 0.2          # Probabilidad de mutar un gen
PASOS_POR_DIA = 30           # CONSTANTE: Pasos de simulación del AC por día calendario
NUM_SIMULACIONES = 3         # Cantidad de corridas Monte Carlo por individuo para mitigar ruido

# PONDERACIÓN DE LA FUNCIÓN DE APTITUD (FITNESS HÍBRIDO)
# Para darle más peso a la Geometría Fractal del perímetro (50/50 o 60/40)
PESO_FRACTAL = 0.5           # Peso asignado a la Dimensión Fractal
PESO_IOU = 0.5               # Peso asignado a la Superposición Espacial (IoU)

def cargar_datos_serie_temporal(entradas):
    """
    Carga una o múltiples matrices satelitales (.npy) y calcula la Dimensión Fractal real
    de cada una para la evaluación multitemporal.
    """
    if isinstance(entradas, str):
        entradas = [("Día_Único", entradas)]
        
    datos_serie = []
    for fecha, ruta in entradas:
        if not os.path.exists(ruta):
            print(f"Advertencia: No se encontró el archivo {ruta}. Se omitirá.")
            continue
            
        matriz_real = np.load(ruta)
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
        
        print(f" -> [{fecha}] Dimensión Fractal Satelital (D): {D_real:.4f} | Celdas afectadas: {np.sum(matriz_real > 0)}")
        
    return datos_serie

def generar_individuo():
    """Genera un cromosoma aleatorio (hipótesis climática)."""
    return [
        random.uniform(0, 50),     # viento_vel (km/h)
        random.uniform(0, 360),    # viento_dir (grados azimutales)
        random.uniform(10, 80),    # humedad (%)
        random.uniform(0.1, 1.0)   # combustible (índice 0-1)
    ]

def evaluar_fitness_multitemporal(individuo, datos_serie, pasos_por_dia=PASOS_POR_DIA, num_simulaciones=NUM_SIMULACIONES):
    """
    Evalúa el fitness del individuo a lo largo de la evolución temporal del incendio.
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
            suma_fitness += (PESO_FRACTAL * fitness_fractal) + (PESO_IOU * iou)
            
        return suma_fitness / num_simulaciones
        
    # --- CASO B: SERIE MULTITEMPORAL (Evolución Día a Día) ---
    suma_fitness_runs = 0.0
    
    for _ in range(num_simulaciones):
        grilla_sim = np.copy(datos_serie[0]['matriz']).astype(int)
        if np.max(grilla_sim) == 1:
            grilla_sim[grilla_sim > 0] = 1
            
        fitness_por_etapa = []
        
        for t in range(1, total_dias):
            matriz_real_t = datos_serie[t]['matriz']
            D_objetivo_t = datos_serie[t]['dimension_fractal']
            
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
            
            try:
                D_sim_t, *_ = calcular_box_counting(perimetro_sim)
            except Exception:
                D_sim_t = 0.0
            error_fractal = abs(D_objetivo_t - D_sim_t)
            fitness_fractal = 1.0 / (1.0 + error_fractal)
            
            interseccion = np.logical_and(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            union = np.logical_or(matriz_real_t > 0, matriz_binaria_sim > 0).sum()
            iou = (interseccion / union) if union > 0 else 0.0
            
            fit_etapa = (PESO_FRACTAL * fitness_fractal) + (PESO_IOU * iou)
            fitness_por_etapa.append(fit_etapa)
            
        suma_fitness_runs += np.mean(fitness_por_etapa)
        
    return suma_fitness_runs / num_simulaciones

def _evaluar_individuo_worker(args):
    """Función auxiliar para evaluación paralela multinúcleo."""
    individuo, datos_serie, pasos_por_dia, num_simulaciones = args
    fit = evaluar_fitness_multitemporal(
        individuo, datos_serie, pasos_por_dia=pasos_por_dia, num_simulaciones=num_simulaciones
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
    """Genera y guarda el gráfico de convergencia del mejor fitness y fitness promedio."""
    generaciones = [h['generacion'] for h in historial]
    mejores = [h['mejor_fitness'] for h in historial]
    promedios = [h['promedio_fitness'] for h in historial]
    
    plt.figure(figsize=(10, 6))
    plt.plot(generaciones, mejores, 'g-o', linewidth=2, label='Mejor Fitness')
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
        writer.writerow(['Generacion', 'Mejor_Fitness', 'Promedio_Fitness', 'Viento_Vel_kmh', 'Viento_Dir_deg', 'Humedad_pct', 'Combustible'])
        for h in historial:
            writer.writerow([
                h['generacion'],
                f"{h['mejor_fitness']:.6f}",
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
    
    datos_serie = cargar_datos_serie_temporal(entradas_matrices)
    if len(datos_serie) == 0:
        print("Error: No hay matrices válidas para optimizar.")
        return None
        
    print(f"\nSerie temporal cargada exitosamente: {len(datos_serie)} fechas analizadas.")
    if len(datos_serie) > 1:
        print(f"Se evaluarán {len(datos_serie) - 1} transiciones diarias continuas ({PASOS_POR_DIA} pasos AC cada una).")
    
    poblacion = [generar_individuo() for _ in range(TAMANO_POBLACION)]
    mejor_individuo_global = None
    mejor_fitness_global = -1.0
    historial_telemetria = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for generacion in range(GENERACIONES):
            tareas = [(ind, datos_serie, PASOS_POR_DIA, NUM_SIMULACIONES) for ind in poblacion]
            fitness_poblacion = list(executor.map(_evaluar_individuo_worker, tareas))
            
            fitness_poblacion.sort(key=lambda x: x[1], reverse=True)
            mejor_ind_gen, mejor_fit_gen = fitness_poblacion[0]
            avg_fit_gen = np.mean([fit for _, fit in fitness_poblacion])
            
            if mejor_fit_gen > mejor_fitness_global:
                mejor_fitness_global = mejor_fit_gen
                mejor_individuo_global = list(mejor_ind_gen)
                
            historial_telemetria.append({
                'generacion': generacion + 1,
                'mejor_fitness': mejor_fit_gen,
                'promedio_fitness': avg_fit_gen,
                'viento_vel': mejor_ind_gen[0],
                'viento_dir': mejor_ind_gen[1],
                'humedad': mejor_ind_gen[2],
                'combustible': mejor_ind_gen[3]
            })
            
            print(f"Gen {generacion+1:02d}/{GENERACIONES:02d} | Mejor Fitness: {mejor_fit_gen:.4f} (Prom: {avg_fit_gen:.4f}) | Viento: {mejor_ind_gen[0]:.1f}km/h @ {mejor_ind_gen[1]:.1f}° | Humedad: {mejor_ind_gen[2]:.1f}% | Comb: {mejor_ind_gen[3]:.2f}")
            
            NUM_ELITES = 2
            nueva_poblacion = [ind_fit[0] for ind_fit in fitness_poblacion[:NUM_ELITES]]
            
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
