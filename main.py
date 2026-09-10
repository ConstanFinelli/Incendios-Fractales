import sys
import os
import numpy as np
from ver_mapa_filtrado import procesar_rango_fechas, procesar_fecha
from algoritmo_genetico import ejecutar_algoritmo_genetico, PASOS_POR_DIA
from simulador_predictivo import ejecutar_prediccion

def main():
    print("="*65)
    print("  SISTEMA DE PREVENCIÓN Y MODELADO FRACTAL MULTITEMPORAL DE INCENDIOS")
    print(f"  Configuración: {PASOS_POR_DIA} pasos de simulación por día")
    print("="*65)
    
    # 1. Solicitar Rango de Fechas
    print("\nIngrese el intervalo de fechas a analizar (ej. 2022-02-17 a 2022-02-19):")
    fecha_inicio = input("Fecha Inicial (AAAA-MM-DD): ").strip()
    
    if not fecha_inicio:
        print("Error: Debe ingresar al menos una fecha inicial. Saliendo...")
        sys.exit(1)
        
    fecha_fin = input("Fecha Final (opcional, presione Enter para analizar solo Fecha Inicial): ").strip()
    if not fecha_fin:
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
        
    # 3. Fase Preventiva / Predictiva
    print(f"\n[FASE 3] Simulación Predictiva y Generación de Mapa de Riesgo...")
    ejecutar_prediccion(datos_entrada, mejores_variables, pasos_futuros=100)
    
    print("\n" + "="*65)
    print("PROCESO MULTITEMPORAL INTEGRAL FINALIZADO CON ÉXITO")
    print("Archivos cartográficos y predictivos generados en 'output/':")
    print("  📍 output/mapa_corrientes_prediccion.png   (Mapa GIS de Corrientes)")
    print("  🌐 output/mapa_corrientes_interactivo.html  (Mapa Web de Corrientes)")
    print("  🇦🇷 output/mapa_argentina_prediccion.png    (Mapa GIS de Argentina)")
    print("  🌐 output/mapa_argentina_interactivo.html   (Mapa Web de Argentina)")
    print("  📊 output/mapa_riesgo_predictivo.png       (Matriz de riesgo comparativa)")
    print("="*65)



if __name__ == "__main__":
    main()

