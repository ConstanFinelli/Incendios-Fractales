import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from automata_celular import simular_incendio_AC
from matplotlib.colors import ListedColormap
import os

def ejecutar_prediccion(datos_entrada, mejores_variables, pasos_futuros=100):
    """
    Toma los datos satelitales (matriz única o lista de fechas/matrices) y las
    variables microclimáticas óptimas, y simula el avance del fuego hacia el futuro
    a partir de la última observación registrada.
    """
    viento_vel, viento_dir, humedad, combustible = mejores_variables
    
    # Determinar si es serie temporal o matriz directa
    if isinstance(datos_entrada, list):
        fecha_inicial, ruta_inicial = datos_entrada[0]
        fecha_final, ruta_final = datos_entrada[-1]
        matriz_inicial = np.load(ruta_inicial)
        
        # Generar matriz final acumulativa (cicatriz histórica)
        matriz_final = np.zeros_like(matriz_inicial)
        for _, ruta in datos_entrada:
            matriz_dia = np.load(ruta)
            matriz_final = np.logical_or(matriz_final > 0, matriz_dia > 0).astype(int)
            
        modo_multitemporal = len(datos_entrada) > 1
    elif isinstance(datos_entrada, np.ndarray):
        matriz_inicial = datos_entrada
        matriz_final = datos_entrada
        fecha_inicial = "Observación Inicial"
        fecha_final = "Observación Final"
        modo_multitemporal = False
    elif isinstance(datos_entrada, str):
        matriz_inicial = np.load(datos_entrada)
        matriz_final = matriz_inicial
        fecha_inicial = "Observación"
        fecha_final = "Observación"
        modo_multitemporal = False
    else:
        raise ValueError("Formato de datos de entrada no reconocido.")
        
    tamano = matriz_final.shape[0]
    
    print("\n" + "="*60)
    print("INICIANDO FASE PREDICTIVA (PREVENCIÓN Y GESTIÓN DE RIESGO)")
    print("="*60)
    print(f"Punto de partida de la proyección: {fecha_final}")
    print(f"Proyectando {pasos_futuros} pasos en el futuro...")
    print(f"Condiciones Microclimáticas: Viento {viento_vel:.1f}km/h @ {viento_dir:.1f}° | Humedad {humedad:.1f}% | Comb {combustible:.2f}")
    
    # Simular proyección a partir del último estado observado
    grilla_final, matriz_binaria_futura = simular_incendio_AC(
        viento_vel=viento_vel,
        viento_dir=viento_dir,
        humedad=humedad,
        combustible=combustible,
        pasos_tiempo=pasos_futuros,
        tamano=tamano,
        grilla_inicial=matriz_final
    )
    
    # Crear matriz de riesgo:
    # 0 = Intacto, 1 = Fuego Satelital Observado (Base), 2 = Riesgo de Expansión Futura
    mapa_riesgo = np.zeros_like(matriz_final)
    mapa_riesgo[matriz_binaria_futura > 0] = 2
    mapa_riesgo[matriz_final > 0] = 1
    
    cmap_riesgo = ListedColormap(['#f8f9fa', '#343a40', '#dc3545'])
    
    if modo_multitemporal:
        # Visualización Comparativa Multipanel (Evolución + Predicción)
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Panel 1: Estado Inicial Observado
        axes[0].imshow(matriz_inicial, cmap='hot_r', origin='lower', interpolation='nearest')
        axes[0].set_title(f"1. Foco Inicial ({fecha_inicial})", fontsize=12, fontweight='bold')
        axes[0].axis('off')
        
        # Panel 2: Estado Final Observado
        axes[1].imshow(matriz_final, cmap='hot_r', origin='lower', interpolation='nearest')
        axes[1].set_title(f"2. Foco Expandido ({fecha_final})", fontsize=12, fontweight='bold')
        axes[1].axis('off')
        
        # Panel 3: Proyección Futura
        axes[2].imshow(mapa_riesgo, cmap=cmap_riesgo, origin='lower', interpolation='nearest')
        axes[2].set_title(f"3. Mapa de Riesgo Predictivo (+{pasos_futuros} ciclos)", fontsize=12, fontweight='bold')
        axes[2].axis('off')
        
        p_intacto = mpatches.Patch(color='#f8f9fa', label='Zona Intacta', ec='#ccc')
        p_actual = mpatches.Patch(color='#343a40', label=f'Fuego Observado ({fecha_final})')
        p_futuro = mpatches.Patch(color='#dc3545', label='Riesgo de Avance Proyectado')
        axes[2].legend(handles=[p_intacto, p_actual, p_futuro], loc='lower right')
        
        plt.suptitle(f"Simulación Predictiva Multitemporal | Viento: {viento_vel:.1f} km/h @ {viento_dir:.1f}° | Humedad: {humedad:.1f}%", fontsize=14)
        plt.tight_layout()
    else:
        # Visualización de Panel Único
        plt.figure(figsize=(10, 8))
        plt.imshow(mapa_riesgo, cmap=cmap_riesgo, origin='lower', interpolation='nearest')
        plt.title(f"Mapa de Riesgo: Predicción (+{pasos_futuros} ciclos)\n(Gris: Fuego Observado | Rojo: Expansión Proyectada)", fontsize=13)
        p_intacto = mpatches.Patch(color='#f8f9fa', label='Zona Intacta', ec='#ccc')
        p_actual = mpatches.Patch(color='#343a40', label='Fuego Satelital Actual')
        p_futuro = mpatches.Patch(color='#dc3545', label='Riesgo de Avance (Predicción)')
        plt.legend(handles=[p_intacto, p_actual, p_futuro], loc='lower right')
        plt.axis('off')
        plt.tight_layout()
        
    nombre_archivo = 'output/mapa_riesgo_predictivo.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Mapa de Riesgo exportado exitosamente a: {nombre_archivo}")
    
    # Generar transposición espacial sobre el mapa de la provincia de Corrientes
    try:
        from visualizador_corrientes import generar_mapas_corrientes
        generar_mapas_corrientes(
            matriz_inicial=matriz_inicial,
            matriz_futura=matriz_binaria_futura,
            mapa_riesgo=mapa_riesgo,
            fecha_inicial=fecha_inicial,
            fecha_final=fecha_final,
            mejores_variables=mejores_variables,
            pasos_futuros=pasos_futuros
        )
    except Exception as e:
        print(f"Advertencia al proyectar mapa de Corrientes: {e}")
        
    # Generar transposición espacial sobre el mapa de la República Argentina
    try:
        from visualizador_argentina import generar_mapas_argentina
        generar_mapas_argentina(
            matriz_inicial=matriz_inicial,
            matriz_futura=matriz_binaria_futura,
            mapa_riesgo=mapa_riesgo,
            fecha_inicial=fecha_inicial,
            fecha_final=fecha_final,
            mejores_variables=mejores_variables,
            pasos_futuros=pasos_futuros
        )
    except Exception as e:
        print(f"Advertencia al proyectar mapa de Argentina: {e}")
        
    return mapa_riesgo



