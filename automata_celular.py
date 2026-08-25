import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def simular_incendio_AC(viento_vel, viento_dir, humedad, combustible, pasos_tiempo, tamano=256, centro_y=None, centro_x=None):
    """
    Simulador de Autómata Celular Estocástico para Incendios Forestales.
    Estados de celda: 0 = Intacta, 1 = Ardiendo, 2 = Quemada (Cenizas)
    """
    # 1. Inicializar la grilla 256x256 (Estado 0: Intacta)
    grilla = np.zeros((tamano, tamano), dtype=int)
    
    # Iniciar el fuego en la coordenada dada, o en el centro por defecto
    cy = centro_y if centro_y is not None else tamano // 2
    cx = centro_x if centro_x is not None else tamano // 2
    
    # Evitar desbordamientos si el centro está en los bordes
    cy = max(1, min(tamano - 2, cy))
    cx = max(1, min(tamano - 2, cx))
    
    grilla[cy-1:cy+2, cx-1:cx+2] = 1 
    
    # 2. Configurar parámetros base
    humedad_norm = humedad / 100.0  # Normalizar de 0 a 1
    prob_base = combustible * (1.0 - humedad_norm)
    
    # Convertir dirección del viento a radianes (matemática de ángulos)
    theta_viento = np.radians(viento_dir)
    c_viento = 0.05 # Constante de sensibilidad al viento
    
    # Coordenadas relativas de los 8 vecinos (Vecindad de Moore)
    # (dy, dx)
    vecinos = [
        (-1, -1), (-1, 0), (-1, 1),
        ( 0, -1),          ( 0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]
    
    # 3. Bucle principal de tiempo
    for paso in range(pasos_tiempo):
        nueva_grilla = grilla.copy()
        
        # Encontrar todas las celdas que están ardiendo (Estado 1)
        # y_ardiendo, x_ardiendo = np.where(grilla == 1)
        # Iterar sobre las celdas es lento en Python puro, pero claro para empezar
        for y in range(1, tamano - 1):
            for x in range(1, tamano - 1):
                
                if grilla[y, x] == 1:
                    # Regla 1: La celda que arde se convierte en ceniza en el siguiente turno
                    nueva_grilla[y, x] = 2
                    
                    # Regla 2: Intentar contagiar a los 8 vecinos
                    for dy, dx in vecinos:
                        ny, nx = y + dy, x + dx
                        
                        # Solo se puede contagiar vegetación intacta (Estado 0)
                        if grilla[ny, nx] == 0:
                            
                            # Calcular ángulo geométrico hacia el vecino
                            # np.arctan2(y, x), notar que el eje Y en matrices crece hacia abajo
                            theta_vecino = np.arctan2(-dy, dx) 
                            
                            # Factor de alineación del viento (Cos() de la diferencia de ángulos)
                            alineacion = np.cos(theta_viento - theta_vecino)
                            
                            # Probabilidad final condicionada por el viento
                            factor_viento = np.exp(c_viento * viento_vel * alineacion)
                            prob_final = prob_base * factor_viento
                            
                            # Límite de probabilidad para evitar locuras matemáticas (máx 95%)
                            prob_final = min(prob_final, 0.95)
                            
                            # ¡El momento estocástico! Tirar los dados virtuales.
                            if np.random.rand() < prob_final:
                                nueva_grilla[ny, nx] = 1 # ¡Fuego!
                                
        grilla = nueva_grilla

    # 4. Retornar la matriz final (Para Box-Counting, unimos el 1 y el 2 como área total quemada)
    # Convertimos los 1s y 2s a '1' (área afectada), dejando el 0 intacto.
    matriz_binaria_final = np.where(grilla > 0, 1, 0)
    return grilla, matriz_binaria_final

# ==========================================
# PRUEBA RÁPIDA DEL SIMULADOR
# ==========================================
if __name__ == "__main__":
    from pathlib import Path
    
    print("Iniciando simulación del Autómata Celular...")
    
    params_hipotesis = {
        "viento_vel": 35.0,     
        "viento_dir": 45.0,     
        "humedad": 20.0,        
        "combustible": 0.8,     
        "pasos_tiempo": 50      
    }
    
    # Ejecutar la simulación
    grilla_estados, matriz_fractal = simular_incendio_AC(**params_hipotesis)

    # 1. Guardar la matriz binaria del simulador
    nombre_archivo_salida = 'matriz_simulada_prueba.npy'
    np.save('output/' + nombre_archivo_salida, matriz_fractal)
    print(f"-> Archivo generado exitosamente: {nombre_archivo_salida}")

    
    # Renderizado visual
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Gráfico 1: El estado físico del incendio (Intacto, Fuego Activo, Cenizas)
    colores_estados = ['#2E8B57', '#FF4500', '#2F4F4F'] # Verde(0), Naranja(1), Gris(2)
    mapa_colores = ListedColormap(colores_estados)
    ax1.imshow(grilla_estados, cmap=mapa_colores, origin='lower')
    ax1.set_title("Evolución Dinámica (Estados del AC)")
    ax1.axis('off')
    
    # Gráfico 2: La matriz binaria que leerá el Algoritmo de Box-Counting
    ax2.imshow(matriz_fractal, cmap='binary', origin='lower')
    ax2.set_title("Silueta Binaria para Box-Counting")
    ax2.axis('off')
    
    plt.tight_layout()
    plt.savefig('prueba_automata.png', dpi=300)
    print("Simulación terminada. Gráfico guardado como 'prueba_automata.png'.")
    plt.show()
