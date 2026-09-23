import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, mapa_combustible=None):
    if mapa_combustible is None:
        try:
            from capa_biomasa import obtener_mapa_combustible
            mapa_combustible = obtener_mapa_combustible(tamano)
        except Exception:
            mapa_combustible = np.ones((tamano, tamano), dtype=float)

    humedad_norm = humedad / 100.0  # normalizar de 0 a 1
    factor_sequedad = 1.0 - humedad_norm
    theta_viento = np.radians(viento_dir)
    c_viento = 0.05
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
        y_ardiendo, x_ardiendo = np.where(grilla == 1)
        if len(y_ardiendo) == 0:
            break
            
        grilla[y_ardiendo, x_ardiendo] = 2
        
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
                        
    return grilla

def simular_incendio_AC(viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, centro_y=None, centro_x=None, grilla_inicial=None, mapa_combustible=None):
    if grilla_inicial is not None:
        grilla = np.copy(grilla_inicial).astype(int)
        if np.max(grilla) == 1:
            grilla[grilla > 0] = 1
    else:
        grilla = np.zeros((tamano, tamano), dtype=int)
        cy = centro_y if centro_y is not None else tamano // 2
        cx = centro_x if centro_x is not None else tamano // 2
        cy = max(1, min(tamano - 2, cy))
        cx = max(1, min(tamano - 2, cx))
        grilla[cy-1:cy+2, cx-1:cx+2] = 1
    
    grilla = _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano, mapa_combustible=mapa_combustible)
    
    matriz_binaria_final = np.where(grilla > 0, 1, 0)
    return grilla, matriz_binaria_final

def simular_evolucion_multietapa(viento_vel, viento_dir, humedad, combustible, grilla_inicial, pasos_por_dia, total_etapas, tamano=256, mapa_combustible=None):
    grilla = np.copy(grilla_inicial).astype(int)
    if np.max(grilla) == 1:
        grilla[grilla > 0] = 1
        
    instantaneas_binarias = []
    
    for _ in range(total_etapas):
        grilla = _avanzar_pasos_AC(grilla, viento_vel, viento_dir, humedad, combustible, pasos_por_dia, tamano, mapa_combustible=mapa_combustible)
        matriz_binaria_etapa = np.where(grilla > 0, 1, 0)
        instantaneas_binarias.append(matriz_binaria_etapa)
        
    return grilla, instantaneas_binarias

