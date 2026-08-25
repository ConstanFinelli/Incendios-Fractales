import sys
import os
import numpy as np
from ver_mapa_filtrado import procesar_fecha
from algoritmo_genetico import ejecutar_algoritmo_genetico
from simulador_predictivo import ejecutar_prediccion

def main():
    print("="*60)
    print("SISTEMA DE PREVENCIÓN Y MODELADO FRACTAL DE INCENDIOS")
    print("="*60)
    
    # 1. Solicitar Fecha
    fecha_elegida = input("Ingrese la fecha a analizar (ej. 2022-02-18): ").strip()
    
    if not fecha_elegida:
        print("Fecha no válida. Saliendo...")
        sys.exit(1)
        
    print(f"\n[FASE 1] Extracción de datos satelitales para la fecha {fecha_elegida}...")
    ruta_matriz_real = procesar_fecha(fecha_elegida)
    
    if ruta_matriz_real is None or not os.path.exists(ruta_matriz_real):
        print("No se pudo generar o encontrar la matriz del incendio. Revisa si hay focos en esa fecha.")
        sys.exit(1)
        
    print(f"\n[FASE 2] Optimización Inversa (Buscando microclima mediante GA)...")
    mejores_variables = ejecutar_algoritmo_genetico(ruta_matriz_real)
    
    if mejores_variables is None:
        print("El algoritmo genético falló o no pudo procesar la matriz.")
        sys.exit(1)
        
    # 3. Fase Preventiva
    print(f"\n[FASE 3] Simulación Predictiva (Generación de Mapa de Riesgo)...")
    matriz_real = np.load(ruta_matriz_real)
    # Proyectar 150 pasos hacia el futuro (puedes ajustar esto)
    ejecutar_prediccion(matriz_real, mejores_variables, pasos_futuros=150)
    
    print("\n" + "="*60)
    print("PROCESO INTEGRAL FINALIZADO")
    print("="*60)

if __name__ == "__main__":
    main()
