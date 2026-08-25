import numpy as np
import random
from automata_celular import simular_incendio_AC
from calcular_dimension_fractal import extraer_perimetro, calcular_box_counting

# --- CONFIGURACIÓN DEL ALGORITMO GENÉTICO ---
TAMANO_POBLACION = 20     # Tamaño pequeño para pruebas rápidas
GENERACIONES = 50      # Número de iteraciones
PROB_MUTACION = 0.2
PASOS_TIEMPO_SIMULACION = 100
import os

# Eliminamos la variable global fija, se calculará dinámicamente
# DIMENSION_FRACTAL_OBJETIVO = 1.65 

def calcular_dimension_objetivo_desde_matriz(ruta_matriz):
    """
    Carga la matriz binaria (.npy) generada por ver_mapa_filtrado, 
    y le calcula su dimensión fractal usando box-counting.
    """
    if not os.path.exists(ruta_matriz):
        print(f"Error: No se encontró el archivo {ruta_matriz}.")
        print("Asegúrate de haber ejecutado ver_mapa_filtrado.py primero para generar la matriz del incendio real.")
        return None
        
    print(f"Cargando matriz real desde: {ruta_matriz}")
    matriz_real = np.load(ruta_matriz)
    
    # Extraer perímetro y calcular fractal
    perimetro_real = extraer_perimetro(matriz_real)
    D_real, *_ = calcular_box_counting(perimetro_real)
    
    print(f"-> Dimensión Fractal Objetivo (del satélite) calculada: {D_real:.4f}")
    
    # Calcular también la coordenada central del incendio real para iniciar ahí la simulación
    y_coords, x_coords = np.where(matriz_real > 0)
    if len(y_coords) > 0:
        cy_real = int(np.mean(y_coords))
        cx_real = int(np.mean(x_coords))
    else:
        cy_real, cx_real = 128, 128
        
    return D_real, matriz_real, cy_real, cx_real

def generar_individuo():
    """Genera un cromosoma aleatorio (hipótesis climática)."""
    # Vector de variables: [viento_vel, viento_dir, humedad, combustible]
    return [
        random.uniform(0, 50),     # viento_vel (km/h)
        random.uniform(0, 360),    # viento_dir (grados)
        random.uniform(10, 80),    # humedad (%)
        random.uniform(0.1, 1.0)   # combustible (índice 0-1)
    ]

def evaluar_fitness(individuo, dimension_objetivo, matriz_real, cy_real, cx_real):
    """
    Evalúa el fitness del individuo promediando múltiples simulaciones estocásticas.
    Combina la Dimensión Fractal con el índice de superposición (IoU).
    """
    viento_vel, viento_dir, humedad, combustible = individuo
    
    NUM_SIMULACIONES = 3
    suma_fitness = 0.0
    
    for _ in range(NUM_SIMULACIONES):
        # 1. Simular el incendio con los parámetros del cromosoma iniciando en el foco real
        _, matriz_binaria = simular_incendio_AC(
            viento_vel=viento_vel, 
            viento_dir=viento_dir, 
            humedad=humedad, 
            combustible=combustible, 
            pasos_tiempo=PASOS_TIEMPO_SIMULACION,
            centro_y=cy_real,
            centro_x=cx_real
        )
        
        # 2. Calcular la dimensión fractal de la simulación
        perimetro = extraer_perimetro(matriz_binaria)
        
        try:
            D_simulada, *_ = calcular_box_counting(perimetro)
        except Exception:
            D_simulada = 0.0 # Castigo severo si falla el cálculo o no hay fuego
            
        # 3. Calcular Fitness Fractal
        error_fractal = abs(dimension_objetivo - D_simulada)
        fitness_fractal = 1.0 / (1.0 + error_fractal)
        
        # 4. Calcular superposición espacial (IoU)
        interseccion = np.logical_and(matriz_real > 0, matriz_binaria > 0).sum()
        union = np.logical_or(matriz_real > 0, matriz_binaria > 0).sum()
        
        iou = (interseccion / union) if union > 0 else 0.0
        
        # 5. Fitness Híbrido: 40% forma (fractal), 60% ubicación/superposición (IoU)
        fitness_hibrido = (0.4 * fitness_fractal) + (0.6 * iou)
        
        suma_fitness += fitness_hibrido
        
    # Retornar el promedio de las simulaciones para combatir el ruido estocástico
    return suma_fitness / NUM_SIMULACIONES


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


def ejecutar_algoritmo_genetico(ruta_matriz_real):
    print("Iniciando Algoritmo Genético de Optimización Inversa...")
    
    # 1. Calcular objetivo a partir del incendio real
    resultado = calcular_dimension_objetivo_desde_matriz(ruta_matriz_real)
    if resultado is None:
        return
    dimension_objetivo, matriz_real, cy_real, cx_real = resultado
        
    # Inicializar población
    poblacion = [generar_individuo() for _ in range(TAMANO_POBLACION)]
    
    for generacion in range(GENERACIONES):
        print(f"\n--- Generación {generacion + 1}/{GENERACIONES} ---")
        
        # Evaluar fitness de toda la población
        fitness_poblacion = []
        for i, ind in enumerate(poblacion):
            fit = evaluar_fitness(ind, dimension_objetivo, matriz_real, cy_real, cx_real)
            fitness_poblacion.append((ind, fit))
            
        # Ordenar por fitness descendente (mayor fitness = mejor)
        fitness_poblacion.sort(key=lambda x: x[1], reverse=True)
        
        mejor_individuo = fitness_poblacion[0][0]
        mejor_fitness = fitness_poblacion[0][1]
        
        # Imprimir progreso
        print(f"Mejor fitness: {mejor_fitness:.4f}")
        print(f"Variables: Viento_vel={mejor_individuo[0]:.1f}, Viento_dir={mejor_individuo[1]:.1f}, Humedad={mejor_individuo[2]:.1f}, Comb={mejor_individuo[3]:.2f}")
        
        # Selección (Elitismo: guardamos a los 2 mejores directamente)
        NUM_ELITES = 2
        nueva_poblacion = [ind_fit[0] for ind_fit in fitness_poblacion[:NUM_ELITES]]
        
        # Cruzamiento y Mutación usando Selección por Torneo para el resto
        while len(nueva_poblacion) < TAMANO_POBLACION:
            padre1 = seleccion_torneo(fitness_poblacion)
            padre2 = seleccion_torneo(fitness_poblacion)
            hijo1, _ = cruzar(padre1, padre2)
            nueva_poblacion.append(mutar(hijo1))
            
        poblacion = nueva_poblacion
        
    print("\nOptimización finalizada.")
    print(f"Mejor fitness alcanzado: {mejor_fitness:.4f}")
    print("Las condiciones microclimáticas inferidas (mejor resultado) son:")
    print(f"Velocidad Viento: {mejor_individuo[0]:.2f} km/h")
    print(f"Dirección Viento: {mejor_individuo[1]:.2f} grados")
    print(f"Humedad: {mejor_individuo[2]:.2f}%")
    print(f"Combustible: {mejor_individuo[3]:.2f}")
    
    return mejor_individuo

if __name__ == "__main__":
    # Necesitas pasar la ruta de la matriz que generó ver_mapa_filtrado.py
    # Por ejemplo, para el 2022-02-18:
    fecha = "2022-02-18" # Cambia esto si analizaste otra fecha
    ruta = f"output/matriz_objetivo_limpia_{fecha}.npy"
    ejecutar_algoritmo_genetico(ruta_matriz_real=ruta)
