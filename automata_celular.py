import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, mapa_combustible=None):
    """
    Función interna optimizada para avanzar el autómata celular n pasos en el tiempo.
    Itera únicamente sobre las celdas activas (Estado 1) para alto rendimiento.
    Incorpora heterogeneidad espacial biofísica real mediante mapa_combustible (Tarea T2.1).
    """
    if mapa_combustible is None:
        try:
            from capa_biomasa import obtener_mapa_combustible
            mapa_combustible = obtener_mapa_combustible(tamano)
        except Exception:
            mapa_combustible = np.ones((tamano, tamano), dtype=float)

    humedad_norm = humedad / 100.0  # Normalizar de 0 a 1
    factor_sequedad = 1.0 - humedad_norm
    theta_viento = np.radians(viento_dir)
    c_viento = 0.05  # Constante de sensibilidad al viento
    vecinos = [
        (-1, -1), (-1, 0), (-1, 1),
        ( 0, -1),          ( 0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]
    
    factores_viento = np.zeros(8)
    for k, (dy, dx) in enumerate(vecinos):
        theta_vecino = np.arctan2(-dy, dx)
        alineacion = np.cos(theta_viento - theta_vecino)
        factores_viento[k] = np.exp(c_viento * viento_vel * alineacion)
        
    rand_func = np.random.random
    
    for _ in range(pasos_tiempo):
        # Localizar celdas que están ardiendo activamente
        y_ardiendo, x_ardiendo = np.where(grilla == 1)
        if len(y_ardiendo) == 0:
            break  # El fuego se extinguió
            
        # Las celdas ardiendo pasan a cenizas (Estado 2)
        grilla[y_ardiendo, x_ardiendo] = 2
        
        # Propagar a vecinos intactos
        for y, x in zip(y_ardiendo, x_ardiendo):
            for k, (dy, dx) in enumerate(vecinos):
                ny, nx = y + dy, x + dx
                if 0 <= ny < tamano and 0 <= nx < tamano and grilla[ny, nx] == 0:
                    c_local = mapa_combustible[ny, nx] * combustible
                    if c_local <= 0.0:
                        continue  # Incombustible (cuerpos de agua o exterior)
                        
                    p_ignicion = min(c_local * factor_sequedad * factores_viento[k], 0.95)
                    if rand_func() < p_ignicion:
                        grilla[ny, nx] = 1 
                        
    return grilla

def simular_incendio_AC(viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, centro_y=None, centro_x=None, grilla_inicial=None, mapa_combustible=None):
    """
    Simulador de Autómata Celular Estocástico para Incendios Forestales.
    Estados de celda: 0 = Intacta, 1 = Ardiendo, 2 = Quemada (Cenizas).
    Acepta mapa_combustible para heterogeneidad espacial biofísica (Tarea T2.1).
    """
    # 1. Inicializar la grilla
    if grilla_inicial is not None:
        grilla = np.copy(grilla_inicial).astype(int)
        # Si la matriz proviene de datos satelitales (0 y 1), los píxeles con fuego arrancan ardiendo (1)
        # Si ya contiene estados 0, 1, 2, se preserva su estado
        if np.max(grilla) == 1:
            grilla[grilla > 0] = 1
    else:
        grilla = np.zeros((tamano, tamano), dtype=int)
        cy = centro_y if centro_y is not None else tamano // 2
        cx = centro_x if centro_x is not None else tamano // 2
        cy = max(1, min(tamano - 2, cy))
        cx = max(1, min(tamano - 2, cx))
        grilla[cy-1:cy+2, cx-1:cx+2] = 1
    
    # 2. Ejecutar simulación optimizada
    grilla = _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano, mapa_combustible=mapa_combustible)
    
    # 3. Retornar matriz de estados y matriz binaria (1 y 2 -> 1 para Box-Counting/IoU)
    matriz_binaria_final = np.where(grilla > 0, 1, 0)
    return grilla, matriz_binaria_final

def simular_evolucion_multietapa(viento_vel, viento_dir, humedad, combustible, grilla_inicial, pasos_por_dia, total_etapas, tamano=256, mapa_combustible=None):
    """
    Simula la evolución continua del fuego a lo largo de múltiples etapas (días).
    Retorna la lista de matrices binarias simuladas en cada etapa para su comparación día a día.
    Acepta mapa_combustible para heterogeneidad espacial biofísica (Tarea T2.1).
    """
    grilla = np.copy(grilla_inicial).astype(int)
    if np.max(grilla) == 1:
        grilla[grilla > 0] = 1
        
    instantaneas_binarias = []
    
    for _ in range(total_etapas):
        grilla = _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_por_dia, tamano, mapa_combustible=mapa_combustible)
        matriz_binaria_etapa = np.where(grilla > 0, 1, 0)
        instantaneas_binarias.append(matriz_binaria_etapa)
        
    return grilla, instantaneas_binarias

