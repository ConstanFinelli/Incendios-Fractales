import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
import csv

from ver_mapa_filtrado import procesar_rango_fechas
from algoritmo_genetico import (
    ejecutar_algoritmo_genetico,
    cargar_datos_serie_temporal,
    PASOS_POR_DIA
)
from automata_celular import _avanzar_pasos_AC
from calcular_dimension_fractal import calcular_dimension_fractal_directa
from visualizador_corrientes import cargar_geometria_corrientes, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

def ejecutar_validacion_walk_forward(
    fechas_calibracion=['2022-02-16', '2022-02-17'],
    fechas_prueba=['2022-02-18', '2022-02-19', '2022-02-20'],
    pasos_por_dia=PASOS_POR_DIA,
    mejores_variables=None
):
    """
    Ejecuta el protocolo científico de Validación Fuera de Muestra (Walk-Forward Validation)
    evaluando la capacidad predictiva ciega a 3 horizontes temporales (+24h, +48h y +72h).
    """
    print("=" * 75)
    print("  PROTOCOLO CIENTÍFICO: VALIDACIÓN FUERA DE MUESTRA (WALK-FORWARD)")
    print("  Evaluación Prospectiva Ciega a 3 Horizontes: +24h, +48h y +72h")
    print("=" * 75)
    
    # 1. Asegurar procesamiento de datos satelitales
    todas_fechas = sorted(list(set(fechas_calibracion + fechas_prueba)))
    fecha_inicio_global = todas_fechas[0]
    fecha_fin_global = todas_fechas[-1]
    
    print(f"\n[PASO 1] Preprocesando serie satelital completa ({fecha_inicio_global} -> {fecha_fin_global})...")
    serie_satelital = procesar_rango_fechas(fecha_inicio_global, fecha_fin_global)
    dict_rutas = {fecha: ruta for fecha, ruta in serie_satelital}
    
    # Validar que existan todas las fechas requeridas
    fechas_calib_validas = [f for f in fechas_calibracion if f in dict_rutas]
    fechas_prueba_validas = [f for f in fechas_prueba if f in dict_rutas]
    
    if len(fechas_calib_validas) < 1 or len(fechas_prueba_validas) < 1:
        print("Advertencia: No se encontraron suficientes fechas satelitales posteriores para la validación ciega.")
        return None
        
    print(f" -> Fechas de Calibración / Entrenamiento: {fechas_calib_validas}")
    print(f" -> Fechas de Prueba Ciega (+24h, +48h, +72h): {fechas_prueba_validas}")
    
    # 2. Fase de Calibración Inversa (Algoritmo Genético)
    if mejores_variables is None:
        print("\n" + "-" * 75)
        print("[PASO 2] Calibración Inversa: El AG optimiza variables sobre la ventana de entrenamiento...")
        print("-" * 75)
        entradas_calib = [(f, dict_rutas[f]) for f in fechas_calib_validas]
        mejores_variables = ejecutar_algoritmo_genetico(entradas_calib)
        if mejores_variables is None:
            print("Error en la optimización del Algoritmo Genético.")
            return None
    else:
        print("\n" + "-" * 75)
        print("[PASO 2] Utilizando variables microclimáticas ya calibradas por el AG...")
        print("-" * 75)
        entradas_calib = [(f, dict_rutas[f]) for f in fechas_calib_validas]
        
    viento_vel, viento_dir, humedad, combustible = mejores_variables
    print(f"\n[CALIBRACIÓN DISPONIBLE] Microclima Calibrado por el AG:")
    print(f" • Velocidad Viento: {viento_vel:.2f} km/h")
    print(f" • Dirección Viento: {viento_dir:.2f}°")
    print(f" • Humedad Relativa: {humedad:.2f} %")
    print(f" • Combustible:      {combustible:.3f}")
    
    # 3. Preparar estado inicial para la simulación prospectiva
    print("\n" + "-" * 75)
    print("[PASO 3] Inferencia Prospectiva Ciega a +24h, +48h y +72h en el Autómata Celular...")
    print("-" * 75)
    
    # Cargar la matriz real acumulada al final de la calibración
    datos_calib_cargados = cargar_datos_serie_temporal(entradas_calib)
    matriz_base_calib = datos_calib_cargados[-1]['matriz']  # Último día de entrenamiento
    fecha_base = fechas_calib_validas[-1]
    tamano = matriz_base_calib.shape[0]
    
    # Capa de combustible biofísica
    try:
        from capa_biomasa import obtener_mapa_combustible
        mapa_combustible = obtener_mapa_combustible(tamano)
    except Exception:
        mapa_combustible = None
        
    grilla_proyeccion = np.copy(matriz_base_calib).astype(int)
    if np.max(grilla_proyeccion) == 1:
        grilla_proyeccion[grilla_proyeccion > 0] = 1
        
    # Acumulador de matriz real satelital
    matriz_real_acumulada = np.copy(matriz_base_calib)
    
    resultados_horizontes = []
    horizontes_labels = ["+24h (1 Día)", "+48h (2 Días)", "+72h (3 Días)"]
    
    for idx, fecha_test in enumerate(fechas_prueba_validas):
        label_h = horizontes_labels[idx] if idx < len(horizontes_labels) else f"+{(idx+1)*24}h"
        horas_acum = (idx + 1) * 24
        pasos_etapa = pasos_por_dia
        
        # Avanzar el Autómata Celular 30 pasos hacia el siguiente horizonte
        grilla_proyeccion = _avanzar_pasos_AC(
            grilla_proyeccion,
            viento_vel=viento_vel,
            viento_dir=viento_dir,
            humedad=humedad,
            combustible=combustible,
            pasos_tiempo=pasos_etapa,
            tamano=tamano,
            mapa_combustible=mapa_combustible
        )
        
        matriz_sim_binaria = np.where(grilla_proyeccion > 0, 1, 0)
        
        # Cargar observación satelital real de ese día y acumular cicatriz
        matriz_dia_real = np.load(dict_rutas[fecha_test])
        matriz_real_acumulada = np.logical_or(matriz_real_acumulada > 0, matriz_dia_real > 0).astype(int)
        
        # Cómputo de Matriz de Confusión Espacial
        vp = np.logical_and(matriz_sim_binaria > 0, matriz_real_acumulada > 0).sum()
        fp = np.logical_and(matriz_sim_binaria > 0, matriz_real_acumulada == 0).sum()
        fn = np.logical_and(matriz_sim_binaria == 0, matriz_real_acumulada > 0).sum()
        vn = np.logical_and(matriz_sim_binaria == 0, matriz_real_acumulada == 0).sum()
        
        # Métricas de Cobertura Espacial
        recall = (vp / (vp + fn)) if (vp + fn) > 0 else 0.0
        precision = (vp / (vp + fp)) if (vp + fp) > 0 else 0.0
        f1_dice = (2.0 * vp / (2.0 * vp + fp + fn)) if (2.0 * vp + fp + fn) > 0 else 0.0
        iou = (vp / (vp + fp + fn)) if (vp + fp + fn) > 0 else 0.0
        
        # Métricas de Geometría Fractal
        d_real = calcular_dimension_fractal_directa(matriz_real_acumulada)
        d_sim = calcular_dimension_fractal_directa(matriz_sim_binaria)
        delta_d = abs(d_real - d_sim)
        fitness_fractal = 1.0 / (1.0 + delta_d)
        
        # Fitness Híbrido Ciego (50% Fractal + 50% F1-Dice)
        fitness_hibrido_ciego = (0.5 * fitness_fractal) + (0.5 * f1_dice)
        
        # Matriz de error visual:
        # 0 = Intacto / VN (Gris claro)
        # 1 = Verdadero Positivo VP (Verde: fuego predicho y real acertado)
        # 2 = Falso Positivo FP (Rojo: sobreexpansión predicha que no ocurrió)
        # 3 = Falso Negativo FN (Amarillo: fuego real no detectado por el modelo)
        matriz_error_visual = np.zeros((tamano, tamano), dtype=int)
        matriz_error_visual[np.logical_and(matriz_sim_binaria > 0, matriz_real_acumulada > 0)] = 1  # VP
        matriz_error_visual[np.logical_and(matriz_sim_binaria > 0, matriz_real_acumulada == 0)] = 2  # FP
        matriz_error_visual[np.logical_and(matriz_sim_binaria == 0, matriz_real_acumulada > 0)] = 3  # FN
        
        resultado_h = {
            'horizonte': label_h,
            'horas': horas_acum,
            'fecha': fecha_test,
            'f1_dice': f1_dice,
            'iou': iou,
            'recall': recall,
            'precision': precision,
            'd_real': d_real,
            'd_sim': d_sim,
            'delta_d': delta_d,
            'fitness_hibrido_ciego': fitness_hibrido_ciego,
            'vp': vp,
            'fp': fp,
            'fn': fn,
            'matriz_real': matriz_real_acumulada.copy(),
            'matriz_sim': matriz_sim_binaria.copy(),
            'matriz_error': matriz_error_visual
        }
        resultados_horizontes.append(resultado_h)
        
        print(f"\n[HORIZONTE {label_h} -> {fecha_test}]")
        print(f" * F1-Dice Ciego:       {f1_dice:.4f} ({f1_dice*100:.1f}%)")
        print(f" * IoU Ciego:           {iou:.4f} ({iou*100:.1f}%)")
        print(f" * Cobertura (Recall):  {recall:.4f} ({recall*100:.1f}% de focos reales cubiertos)")
        print(f" * Pureza (Precision):  {precision:.4f} ({precision*100:.1f}%)")
        print(f" * D_real = {d_real:.4f} | D_sim = {d_sim:.4f} | Error Delta_D = {delta_d:.4f}")
        print(f" * Fitness Hibrido Ciego: {fitness_hibrido_ciego:.4f}")

    # 4. Generación del Mapa Diagnóstico Espacial Multipanel (3 Filas x 3 Columnas)
    print("\n" + "-" * 75)
    print("[PASO 4] Generando visualización científica cartográfica con mapa de Corrientes...")
    print("-" * 75)
    
    num_horizontes = len(resultados_horizontes)
    gdf_corrientes = cargar_geometria_corrientes()
    extent = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    
    fig, axes = plt.subplots(num_horizontes, 3, figsize=(22, 6.8 * num_horizontes), dpi=300)
    if num_horizontes == 1:
        axes = np.array([axes])
        
    cmap_err = ListedColormap(['#10b981', '#ef4444', '#f59e0b'])  # 1: VP Verde, 2: FP Rojo, 3: FN Ámbar
    norm_err = BoundaryNorm([0.5, 1.5, 2.5, 3.5], 3)
    
    for row, res in enumerate(resultados_horizontes):
        ax1, ax2, ax3 = axes[row, 0], axes[row, 1], axes[row, 2]
        
        # Renderizar base cartográfica de departamentos de Corrientes en los 3 ejes
        for ax in (ax1, ax2, ax3):
            if gdf_corrientes is not None:
                gdf_corrientes.plot(ax=ax, color='#f1f5f9', edgecolor='#64748b', linewidth=0.75, zorder=1)
            ax.set_xlim(LON_MIN - 0.1, LON_MAX + 0.1)
            ax.set_ylim(LAT_MIN - 0.1, LAT_MAX + 0.1)
            ax.set_xlabel("Longitud Oeste", fontsize=9.5)
            ax.set_ylabel("Latitud Sur", fontsize=9.5)
            ax.grid(True, linestyle=':', alpha=0.4, color='#94a3b8', zorder=2)
            
        # Columna 1: Observación Satelital Real NASA sobre Corrientes
        m_real = np.ma.masked_where(res['matriz_real'] == 0, res['matriz_real'])
        ax1.imshow(m_real, origin='lower', extent=extent, cmap=ListedColormap(['#dc2626']), alpha=0.88, zorder=3)
        ax1.set_title(f"1. Verdad Satelital NASA ({res['fecha']})\nHorizonte {res['horizonte']} | D_real={res['d_real']:.3f}", fontsize=11.5, fontweight='bold', pad=8)
        p_real = mpatches.Patch(color='#dc2626', label=f"Cicatriz Satelital ({res['fecha']})")
        p_prov = mpatches.Patch(facecolor='#f1f5f9', edgecolor='#64748b', label='Provincia de Corrientes')
        ax1.legend(handles=[p_prov, p_real], loc='lower right', fontsize=8.5)
        
        # Columna 2: Predicción Prospectiva Ciega sobre Corrientes
        m_sim = np.ma.masked_where(res['matriz_sim'] == 0, res['matriz_sim'])
        ax2.imshow(m_sim, origin='lower', extent=extent, cmap=ListedColormap(['#ea580c']), alpha=0.88, zorder=3)
        ax2.set_title(f"2. Predicción Ciega AC ({res['horas']}h)\nF1-Dice={res['f1_dice']*100:.1f}% | D_sim={res['d_sim']:.3f}", fontsize=11.5, fontweight='bold', pad=8)
        p_sim = mpatches.Patch(color='#ea580c', label=f"Avance Simulado (+{res['horas']}h)")
        ax2.legend(handles=[p_prov, p_sim], loc='lower right', fontsize=8.5)
        
        # Columna 3: Mapa de Diagnóstico Espacial y Errores
        m_err = np.ma.masked_where(res['matriz_error'] == 0, res['matriz_error'])
        ax3.imshow(m_err, origin='lower', extent=extent, cmap=cmap_err, norm=norm_err, alpha=0.92, zorder=3)
        ax3.set_title(f"3. Diagnóstico Espacial ({res['horizonte']})\nRecall={res['recall']*100:.1f}% | Precision={res['precision']*100:.1f}% | IoU={res['iou']*100:.1f}%", fontsize=11.5, fontweight='bold', pad=8)
        p_vp = mpatches.Patch(color='#10b981', label='Verdadero Positivo (Acierto Fuego)')
        p_fp = mpatches.Patch(color='#ef4444', label='Falso Positivo (Sobreestimación)')
        p_fn = mpatches.Patch(color='#f59e0b', label='Falso Negativo (Subestimación)')
        ax3.legend(handles=[p_prov, p_vp, p_fp, p_fn], loc='lower right', fontsize=8.5)
            
    plt.suptitle(
        f"Validación Fuera de Muestra (Walk-Forward) sobre la Provincia de Corrientes\n"
        f"Calibración Inicial: {fechas_calib_validas[0]} a {fecha_base} | Microclima Óptimo: Viento {viento_vel:.1f} km/h @ {viento_dir:.1f}° | Humedad {humedad:.1f}% | Comb {combustible:.2f}",
        fontsize=13.5,
        fontweight='bold',
        y=0.995
    )
    plt.tight_layout()
    
    ruta_figura_diagnostico = 'output/walk_forward_comparativa_3dias.png'
    plt.savefig(ruta_figura_diagnostico, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Gráfico diagnóstico multipanel guardado en: {ruta_figura_diagnostico}")
    
    # 5. Gráfico de Evolución de Métricas a lo Largo del Horizonte Temporal
    fig, ax = plt.subplots(figsize=(9, 5))
    ejes_x = [res['horizonte'] for res in resultados_horizontes]
    valores_f1 = [res['f1_dice'] for res in resultados_horizontes]
    valores_iou = [res['iou'] for res in resultados_horizontes]
    valores_recall = [res['recall'] for res in resultados_horizontes]
    valores_precision = [res['precision'] for res in resultados_horizontes]
    valores_deltad = [res['delta_d'] for res in resultados_horizontes]
    
    ax.plot(ejes_x, valores_f1, 'g-o', linewidth=2.5, markersize=8, label='F1-Dice Ciego')
    ax.plot(ejes_x, valores_recall, 'b--s', linewidth=1.8, markersize=6, label='Cobertura (Recall)')
    ax.plot(ejes_x, valores_precision, 'm-.^', linewidth=1.8, markersize=6, label='Pureza (Precision)')
    ax.plot(ejes_x, valores_iou, 'c:d', linewidth=1.5, markersize=6, label='IoU Ciego (Jaccard)')
    ax.plot(ejes_x, valores_deltad, 'r-x', linewidth=1.8, markersize=7, label='Error Fractal ΔD')
    
    ax.set_title("Evolución de Métricas Prospectivas Clegas (+24h, +48h y +72h)", fontsize=13, pad=15)
    ax.set_xlabel("Horizonte Temporal de Predicción Ciega", fontsize=11)
    ax.set_ylabel("Valor de Métrica", fontsize=11)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=10)
    
    for i, txt in enumerate(valores_f1):
        ax.annotate(f"{txt:.3f}", (ejes_x[i], valores_f1[i] + 0.03), fontweight='bold', color='green', ha='center')
        
    ruta_figura_curvas = 'output/walk_forward_metricas_progression.png'
    plt.tight_layout()
    plt.savefig(ruta_figura_curvas, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Gráfico de evolución de métricas guardado en: {ruta_figura_curvas}")
    
    # 6. Exportar Tabla CSV Consolidada
    ruta_csv = 'output/reporte_walk_forward_3dias.csv'
    with open(ruta_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Horizonte', 'Horas_Proyectadas', 'Fecha_NASA',
            'F1_Dice_Ciego', 'IoU_Ciego', 'Recall_Cobertura', 'Precision_Pureza',
            'D_Real', 'D_Simulada', 'Delta_D_Error', 'Fitness_Hibrido_Ciego',
            'Verdaderos_Positivos', 'Falsos_Positivos', 'Falsos_Negativos',
            'Viento_Vel_kmh', 'Viento_Dir_deg', 'Humedad_pct', 'Combustible'
        ])
        for r in resultados_horizontes:
            writer.writerow([
                r['horizonte'], r['horas'], r['fecha'],
                f"{r['f1_dice']:.4f}", f"{r['iou']:.4f}", f"{r['recall']:.4f}", f"{r['precision']:.4f}",
                f"{r['d_real']:.4f}", f"{r['d_sim']:.4f}", f"{r['delta_d']:.4f}", f"{r['fitness_hibrido_ciego']:.4f}",
                r['vp'], r['fp'], r['fn'],
                f"{viento_vel:.2f}", f"{viento_dir:.2f}", f"{humedad:.2f}", f"{combustible:.3f}"
            ])
            
    print(f" -> Reporte cuantitativo consolidado exportado a: {ruta_csv}")
    
    # 7. Resumen Final en Consola
    print("\n" + "=" * 75)
    print("  RESUMEN EJECUTIVO: VALIDACION FUERA DE MUESTRA A 3 HORIZONTES")
    print("=" * 75)
    print(f"{'Horizonte':<15} | {'Fecha':<12} | {'F1-Dice':<10} | {'Recall':<10} | {'Precision':<10} | {'Error Delta_D':<10}")
    print("-" * 75)
    for r in resultados_horizontes:
        print(f"{r['horizonte']:<15} | {r['fecha']:<12} | {r['f1_dice']*100:>6.2f}%    | {r['recall']*100:>6.2f}%    | {r['precision']*100:>6.2f}%    | {r['delta_d']:>6.4f}")
    print("=" * 75)
    
    return resultados_horizontes

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validación Fuera de Muestra (Walk-Forward) a 3 Horizontes")
    parser.add_argument("--calib", nargs="+", default=['2022-02-16', '2022-02-17'], help="Fechas de calibración (ej: 2022-02-16 2022-02-17)")
    parser.add_argument("--test", nargs="+", default=['2022-02-18', '2022-02-19', '2022-02-20'], help="Fechas de prueba ciega a +24h, +48h, +72h")
    args = parser.parse_args()
    
    ejecutar_validacion_walk_forward(
        fechas_calibracion=args.calib,
        fechas_prueba=args.test
    )

