import numpy as np
import matplotlib.pyplot as plt
from automata_celular import simular_incendio_AC
from matplotlib.colors import ListedColormap

def ejecutar_prediccion(matriz_real, mejores_variables, pasos_futuros=200):
    """
    Toma la matriz del satélite actual y las variables microclimáticas óptimas,
    y simula el avance del fuego hacia el futuro.
    """
    viento_vel, viento_dir, humedad, combustible = mejores_variables
    tamano = matriz_real.shape[0]
    
    print("\n" + "="*50)
    print("INICIANDO FASE PREDICTIVA (PREVENCIÓN)")
    print("="*50)
    print(f"Estado Inicial: Mapa Satelital")
    print(f"Proyectando {pasos_futuros} pasos en el futuro...")
    print(f"Condiciones: Viento {viento_vel:.1f}km/h | Dirección {viento_dir:.1f}° | Humedad {humedad:.1f}%")
    
    # Simular
    grilla_final, matriz_binaria_futura = simular_incendio_AC(
        viento_vel=viento_vel,
        viento_dir=viento_dir,
        humedad=humedad,
        combustible=combustible,
        pasos_tiempo=pasos_futuros,
        tamano=tamano,
        grilla_inicial=matriz_real
    )
    
    print("Generando Mapa de Riesgo Predictivo...")
    
    # Crear un mapa combinado
    # 0 = Intacto
    # 1 = Fuego Original (Satélite)
    # 2 = Nuevo fuego proyectado (Riesgo)
    mapa_riesgo = np.zeros_like(matriz_real)
    
    # Marcar el fuego nuevo primero
    mapa_riesgo[matriz_binaria_futura > 0] = 2
    
    # Sobreescribir con el fuego original para que resalte el "centro"
    mapa_riesgo[matriz_real > 0] = 1
    
    # Visualizar
    plt.figure(figsize=(10, 8))
    
    # Colores: Blanco (Intacto), Gris/Negro oscuro (Fuego Pasado), Rojo Brillante (Proyección Futura)
    cmap_riesgo = ListedColormap(['#f5f5f5', '#4a4a4a', '#ff0000'])
    
    plt.imshow(mapa_riesgo, cmap=cmap_riesgo, interpolation='nearest')
    plt.title(f"Mapa de Riesgo: Predicción a {pasos_futuros} ciclos\n(Gris: Fuego Actual | Rojo: Expansión Proyectada)")
    
    # Leyenda customizada
    import matplotlib.patches as mpatches
    p_intacto = mpatches.Patch(color='#f5f5f5', label='Zona Intacta')
    p_actual = mpatches.Patch(color='#4a4a4a', label='Fuego Satelital Actual')
    p_futuro = mpatches.Patch(color='#ff0000', label='Riesgo de Avance (Predicción)')
    plt.legend(handles=[p_intacto, p_actual, p_futuro], loc='lower right')
    
    plt.grid(False)
    
    nombre_archivo = 'output/mapa_riesgo_predictivo.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Mapa de Riesgo exportado exitosamente a: {nombre_archivo}")
    return mapa_riesgo
