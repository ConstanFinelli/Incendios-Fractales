import sys
import os
import matplotlib
matplotlib.use('Agg')
import numpy as np
from datetime import datetime, timedelta
from ver_mapa_filtrado import procesar_rango_fechas, procesar_fecha
from algoritmo_genetico import ejecutar_algoritmo_genetico, PASOS_POR_DIA
from simulador_predictivo import ejecutar_prediccion
from validacion_walk_forward import ejecutar_validacion_walk_forward

def main():
    print("="*65)
    print("  SISTEMA DE PREVENCIÓN Y MODELADO FRACTAL MULTITEMPORAL DE INCENDIOS")
    print(f"  Configuración: {PASOS_POR_DIA} pasos de simulación por día")
    print("="*65)
    
    # 1. Solicitar Rango de Fechas
    print("\nIngrese el intervalo de fechas a analizar (ej. 2022-02-16 a 2022-02-17):")
    fecha_inicio = input("Fecha Inicial (AAAA-MM-DD): ").strip()
    
    if not fecha_inicio:
        print("Error: Debe ingresar al menos una fecha inicial. Saliendo...")
        sys.exit(1)
        
    fecha_fin = input("Fecha Final (opcional, presione Enter para calibrar hacia el día siguiente): ").strip()
    if not fecha_fin or fecha_fin == fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin = (dt_inicio + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f" -> Configurado avance temporal continuo: {fecha_inicio} (T0 partida) -> {fecha_fin} (T1 objetivo)")
        except ValueError:
            fecha_fin = fecha_inicio
        
    print(f"\n[FASE 1] Extracción y rasterización satelital ({fecha_inicio} -> {fecha_fin})...")
    
    if fecha_inicio == fecha_fin:
        ruta_matriz = procesar_fecha(fecha_inicio)
        if ruta_matriz is None or not os.path.exists(ruta_matriz):
            print(f"No se pudo generar la matriz para la fecha {fecha_inicio}.")
            sys.exit(1)
        datos_entrada = [(fecha_inicio, ruta_matriz)]
    else:
        datos_entrada = procesar_rango_fechas(fecha_inicio, fecha_fin)
        if len(datos_entrada) == 0:
            print("No se encontraron registros de incendios válidos en el área para ese intervalo.")
            sys.exit(1)
            
    print(f"\n[FASE 2] Optimización Inversa Multitemporal (Algoritmo Genético)...")
    mejores_variables = ejecutar_algoritmo_genetico(datos_entrada)
    
    if mejores_variables is None:
        print("El algoritmo genético no pudo completar la optimización.")
        sys.exit(1)
        
    # 3. Fase Preventiva / Predictiva Multi-Horizonte (24h, 48h, 72h)
    print(f"\n[FASE 3] Simulación Predictiva Multi-Horizonte (24h, 48h, 72h) y Cartografía GIS...")
    ejecutar_prediccion(datos_entrada, mejores_variables, pasos_por_dia=PASOS_POR_DIA)
    
    # 4. Fase de Validación Fuera de Muestra (Walk-Forward contra días reales siguientes)
    print(f"\n[FASE 4] Validación Fuera de Muestra (Walk-Forward: +24h, +48h y +72h)...")
    try:
        dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        fechas_futuras = [(dt_fin + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 4)]
        fechas_calib = [f for f, _ in datos_entrada]
        
        ejecutar_validacion_walk_forward(
            fechas_calibracion=fechas_calib,
            fechas_prueba=fechas_futuras,
            pasos_por_dia=PASOS_POR_DIA,
            mejores_variables=mejores_variables
        )
    except Exception as e:
        print(f"Nota: No se pudo completar la validación ciega automática ({e}).")
    
    print("\n" + "="*65)
    print("PROCESO MULTITEMPORAL INTEGRAL FINALIZADO CON ÉXITO")
    print("Archivos cartográficos, predictivos y de validación en 'output/':")
    print("  📊 output/walk_forward_comparativa_3dias.png (Diagnóstico espacial 3x3 vs Satélite Real)")
    print("  📈 output/walk_forward_metricas_progression.png (Evolución temporal F1-Dice y Error)")
    print("  📑 output/reporte_walk_forward_3dias.csv     (Métricas cuantitativas fuera de muestra)")
    print("  🗺️ output/mapa_riesgo_predictivo.png        (Matriz isócrona multi-horizonte 24h, 48h, 72h)")
    print("  📍 output/mapa_corrientes_prediccion.png    (Mapa GIS 4 paneles de Corrientes @ 300 DPI)")
    print("  🌐 output/mapa_corrientes_interactivo.html   (Mapa Web interactivo multicapa de Corrientes)")
    print("  🌿 output/mapa_cobertura_combustible.png    (Mapa de susceptibilidad de biomasa IGN WFS)")
    print("  💾 output/npy/                              (Matrices binarias satelitales .npy)")
    print("  🖼️ output/siluetas/                         (Siluetas fractales procesadas .png)")
    print("="*65)



if __name__ == "__main__":
    main()

