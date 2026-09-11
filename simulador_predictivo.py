import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from automata_celular import simular_evolucion_multietapa
from matplotlib.colors import ListedColormap
import os

PASOS_POR_DIA = 30  # 30 pasos de autómata celular equivalen a 1 día de propagación

def ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA):
    """
    Toma los datos satelitales y las variables microclimáticas óptimas inferidas por el AG,
    y simula el avance continuo del fuego a través de tres horizontes temporales clave:
      - 24 horas (+30 pasos | Nivel Táctico: brigadistas y línea de fuego)
      - 48 horas (+60 pasos | Nivel Preventivo: evacuación y cortafuegos pesados)
      - 72 horas (+90 pasos | Nivel Estratégico: gestión territorial y reservas)
    Genera un mapa de riesgo isócrono acumulativo y orquesta la transposición espacial.
    """
    viento_vel, viento_dir, humedad, combustible = mejores_variables
    
    # Determinar si es serie temporal o matriz directa
    if isinstance(datos_entrada, list):
        fecha_inicial, ruta_inicial = datos_entrada[0]
        fecha_final, ruta_final = datos_entrada[-1]
        matriz_inicial = np.load(ruta_inicial)
        # El punto de partida de la predicción es el foco activo del último día observado
        matriz_final = np.load(ruta_final)
            
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
    
    print("\n" + "="*65)
    print("INICIANDO FASE PREDICTIVA MULTI-HORIZONTE (24h, 48h y 72h)")
    print("="*65)
    print(f"Punto de partida de la proyección (Foco Observado Base): {fecha_final}")
    print(f"Horizontes de Simulación: +24h ({pasos_por_dia} ciclos) | +48h ({pasos_por_dia*2} ciclos) | +72h ({pasos_por_dia*3} ciclos)")
    print(f"Condiciones Microclimáticas Inferidas: Viento {viento_vel:.1f}km/h @ {viento_dir:.1f}° | Humedad {humedad:.1f}% | Comb {combustible:.2f}")
    
    # Simulación encadenada continua en 3 etapas sucesivas de 24 horas cada una:
    # M_base -> (+30) -> M_24h -> (+30) -> M_48h -> (+30) -> M_72h
    print("\nEjecutando propagación continua multietapa...")
    grilla_72h, instantaneas_binarias = simular_evolucion_multietapa(
        viento_vel=viento_vel,
        viento_dir=viento_dir,
        humedad=humedad,
        combustible=combustible,
        grilla_inicial=matriz_final,
        pasos_por_dia=pasos_por_dia,
        total_etapas=3,
        tamano=tamano
    )
    
    matriz_24h = instantaneas_binarias[0]
    matriz_48h = instantaneas_binarias[1]
    matriz_72h = instantaneas_binarias[2]
    
    celdas_base = int(np.sum(matriz_final > 0))
    celdas_24h = int(np.sum(matriz_24h > 0)) - celdas_base
    celdas_48h = int(np.sum(matriz_48h > 0)) - int(np.sum(matriz_24h > 0))
    celdas_72h = int(np.sum(matriz_72h > 0)) - int(np.sum(matriz_48h > 0))
    
    print(f" -> Foco Base Observado ({fecha_final}): {celdas_base} celdas")
    print(f" -> Avance Táctico +24h (Día 1): +{celdas_24h} nuevas celdas")
    print(f" -> Avance Preventivo +48h (Día 2): +{celdas_48h} nuevas celdas")
    print(f" -> Avance Estratégico +72h (Día 3): +{celdas_72h} nuevas celdas")
    print(f" -> Masa total acumulada proyectada (+72h): {int(np.sum(matriz_72h > 0))} celdas")
    
    # Construcción de la matriz de riesgo isócrona acumulativa:
    # 0 = Zona Intacta
    # 1 = Foco Satelital Observado (Base al término del período)
    # 2 = Riesgo Táctico (+24h / Día 1)
    # 3 = Riesgo Preventivo (+48h / Día 2)
    # 4 = Riesgo Estratégico (+72h / Día 3)
    mapa_riesgo = np.zeros_like(matriz_final, dtype=int)
    mapa_riesgo[matriz_72h > 0] = 4
    mapa_riesgo[matriz_48h > 0] = 3
    mapa_riesgo[matriz_24h > 0] = 2
    mapa_riesgo[matriz_final > 0] = 1
    
    # Paleta isócrona profesional
    # Blanco/Crema, Carbón consolidado, Ámbar táctico, Naranja preventivo, Rojo estratégico
    cmap_isocronas = ListedColormap(['#f8f9fa', '#2c3e50', '#f39c12', '#e67e22', '#e74c3c'])
    
    # Visualización Comparativa Multipanel (4 Paneles Horizontales)
    fig, axes = plt.subplots(1, 4, figsize=(24, 6), dpi=300)
    
    # Panel 1: Foco Base Observado
    axes[0].imshow(matriz_final, cmap='hot_r', origin='lower', interpolation='nearest')
    axes[0].set_title(f"1. Foco Base Observado\n({fecha_final})", fontsize=11.5, fontweight='bold', pad=8)
    axes[0].axis('off')
    p_base_obs = mpatches.Patch(color='#343a40', label=f'Foco Satelital ({fecha_final})')
    axes[0].legend(handles=[p_base_obs], loc='lower right', framealpha=0.92)
    
    # Panel 2: Predicción +24 Horas
    mapa_p2 = np.zeros_like(matriz_final, dtype=int)
    mapa_p2[matriz_24h > 0] = 2
    mapa_p2[matriz_final > 0] = 1
    cmap_p2 = ListedColormap(['#f8f9fa', '#2c3e50', '#f39c12'])
    axes[1].imshow(mapa_p2, cmap=cmap_p2, origin='lower', interpolation='nearest')
    axes[1].set_title(f"2. Predicción a +24 Horas\n(+{pasos_por_dia} Ciclos | Nivel Táctico)", fontsize=11.5, fontweight='bold', pad=8)
    axes[1].axis('off')
    p_tac = mpatches.Patch(color='#f39c12', label=f'Avance Táctico (+{celdas_24h} celdas)')
    axes[1].legend(handles=[p_base_obs, p_tac], loc='lower right', framealpha=0.92)
    
    # Panel 3: Predicción a +48 Horas
    mapa_p3 = np.zeros_like(matriz_final, dtype=int)
    mapa_p3[matriz_48h > 0] = 3
    mapa_p3[matriz_24h > 0] = 2
    mapa_p3[matriz_final > 0] = 1
    cmap_p3 = ListedColormap(['#f8f9fa', '#2c3e50', '#f39c12', '#e67e22'])
    axes[2].imshow(mapa_p3, cmap=cmap_p3, origin='lower', interpolation='nearest')
    axes[2].set_title(f"3. Predicción a +48 Horas\n(+{pasos_por_dia*2} Ciclos | Nivel Preventivo)", fontsize=11.5, fontweight='bold', pad=8)
    axes[2].axis('off')
    p_prev = mpatches.Patch(color='#e67e22', label=f'Avance Preventivo (+{celdas_48h} celdas)')
    axes[2].legend(handles=[p_base_obs, p_tac, p_prev], loc='lower right', framealpha=0.92)
    
    # Panel 4: Mapa de Riesgo Isócrono (+72 Horas)
    axes[3].imshow(mapa_riesgo, cmap=cmap_isocronas, origin='lower', interpolation='nearest')
    axes[3].set_title(f"4. Mapa de Riesgo Isócrono (+72h)\n(+{pasos_por_dia*3} Ciclos | Nivel Estratégico)", fontsize=11.5, fontweight='bold', pad=8)
    axes[3].axis('off')
    p_intacto = mpatches.Patch(color='#f8f9fa', label='Zona Intacta', ec='#ccc')
    p_est = mpatches.Patch(color='#e74c3c', label=f'Avance Estratégico (+{celdas_72h} celdas)')
    axes[3].legend(handles=[p_intacto, p_base_obs, p_tac, p_prev, p_est], loc='lower right', framealpha=0.92, fontsize=8)
    
    plt.suptitle(
        f"Simulación Predictiva Multi-Horizonte (24h, 48h, 72h) | Viento: {viento_vel:.1f} km/h @ {viento_dir:.1f}° | Humedad: {humedad:.1f}% | Comb: {combustible:.2f}",
        fontsize=13.5, fontweight='bold', y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    nombre_archivo = 'output/mapa_riesgo_predictivo.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nMapa de Riesgo Isócrono exportado exitosamente a: {nombre_archivo}")
    
    matrices_horizontes = {
        '24h': matriz_24h,
        '48h': matriz_48h,
        '72h': matriz_72h
    }
    
    # Generar transposición espacial sobre el mapa de la provincia de Corrientes
    try:
        from visualizador_corrientes import generar_mapas_corrientes
        generar_mapas_corrientes(
            matriz_inicial=matriz_inicial,
            matriz_final=matriz_final,
            matriz_futura=matrices_horizontes,
            mapa_riesgo=mapa_riesgo,
            fecha_inicial=fecha_inicial,
            fecha_final=fecha_final,
            mejores_variables=mejores_variables,
            pasos_futuros=pasos_por_dia * 3
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Advertencia al proyectar mapa de Corrientes: {e}")
        
    return mapa_riesgo




