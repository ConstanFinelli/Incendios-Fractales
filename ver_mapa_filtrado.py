import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np
from scipy.ndimage import binary_dilation, label

import os

# Constantes de la zona de estudio (Provincia de Corrientes, Argentina)
LAT_MIN, LAT_MAX = -30.8, -27.2
LON_MIN, LON_MAX = -59.8, -55.6

_df_completo_cache = None

def obtener_df_completo():
    """Carga diferida (Lazy Loading) de la base de datos de la NASA para máxima velocidad de import."""
    global _df_completo_cache
    if _df_completo_cache is None:
        nombre_archivo = './DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json'
        print("Cargando base de datos completa de la NASA...")
        df_pandas = pd.read_json(nombre_archivo)
        print("Construyendo geometrías espaciales...")
        geometria = [Point(xy) for xy in zip(df_pandas['longitude'], df_pandas['latitude'])]
        _df_completo_cache = gpd.GeoDataFrame(df_pandas, geometry=geometria, crs="EPSG:4326")
    return _df_completo_cache


def procesar_una_fecha(fecha, df_fuente=None, verbose=True):
    """
    Procesa los datos satelitales para una fecha específica.
    Filtra los focos en el área de estudio, rasteriza, dilata y limpia componentes aislados.
    Retorna la ruta del archivo .npy limpio, o None si no hay focos.
    """
    df_base = df_fuente if df_fuente is not None else obtener_df_completo()
    
    if fecha not in df_base['acq_date'].values:
        if verbose:
            print(f"Fecha {fecha} no encontrada en la base de datos.")
        return None
        
    df_dia = df_base[df_base['acq_date'] == fecha]
    
    # Filtrar dentro del área de estudio
    df_filtrado = df_dia[
        (df_dia['latitude'] >= LAT_MIN) & (df_dia['latitude'] <= LAT_MAX) &
        (df_dia['longitude'] >= LON_MIN) & (df_dia['longitude'] <= LON_MAX)
    ]
    
    num_focos = len(df_filtrado)
    if num_focos == 0:
        if verbose:
            print(f" -> [{fecha}] 0 focos en la zona de estudio. Fecha omitida automáticamente.")
        return None
        
    if verbose:
        print(f" -> [{fecha}] {num_focos} focos detectados en el área de estudio.")
        
    # Rasterización
    tamano_matriz = 256
    matriz_binaria = np.zeros((tamano_matriz, tamano_matriz))
    
    lats_idx = np.clip(np.floor((df_filtrado['latitude'] - LAT_MIN) / (LAT_MAX - LAT_MIN) * (tamano_matriz - 1)).astype(int), 0, tamano_matriz - 1)
    lons_idx = np.clip(np.floor((df_filtrado['longitude'] - LON_MIN) / (LON_MAX - LON_MIN) * (tamano_matriz - 1)).astype(int), 0, tamano_matriz - 1)
    
    for lat_i, lon_i in zip(lats_idx, lons_idx):
        matriz_binaria[lat_i, lon_i] = 1
        
    os.makedirs('output', exist_ok=True)
    np.save(f'output/matriz_fractal_recorte_{fecha}.npy', matriz_binaria)
    
    # Filtro morfológico de dilatación
    matriz_continua = binary_dilation(matriz_binaria, iterations=11).astype(int)
    np.save(f'output/matriz_fractal_recorte_continua_{fecha}.npy', matriz_continua)
    
    # Componentes conectados (limpieza de ruido e islas)
    estructura_vecindad = np.ones((3, 3))
    matrices_etiquetadas, num_features = label(matriz_continua, structure=estructura_vecindad)
    tamano_componentes = np.bincount(matrices_etiquetadas.ravel())
    
    if len(tamano_componentes) > 1:
        id_componente_principal = np.argmax(tamano_componentes[1:]) + 1
        matriz_limpia = (matrices_etiquetadas == id_componente_principal).astype(int)
    else:
        matriz_limpia = matriz_continua
        
    nombre_matriz_limpia_npy = f'output/matriz_objetivo_limpia_{fecha}.npy'
    np.save(nombre_matriz_limpia_npy, matriz_limpia)
    
    # Renderizar y guardar siluetas
    plt.figure(figsize=(6,6))
    plt.imshow(matriz_limpia, cmap='binary', origin='lower')
    plt.title(f"Cuerpo Principal Unificado y Limpio ({fecha})")
    plt.xlabel("Índice X")
    plt.ylabel("Índice Y")
    plt.savefig(f'output/silueta_fractal_limpia_{fecha}.png', dpi=300)
    plt.close()
    
    return nombre_matriz_limpia_npy

def procesar_rango_fechas(fecha_inicio, fecha_fin):
    """
    Procesa todas las fechas entre fecha_inicio y fecha_fin (inclusivas).
    Filtra automáticamente los días con 0 focos en la zona.
    Retorna una lista de tuplas [(fecha, ruta_matriz), ...] ordenadas cronológicamente.
    """
    print(f"\nBuscando registros satelitales entre {fecha_inicio} y {fecha_fin}...")
    df_completo = obtener_df_completo()
    
    # Obtener todas las fechas únicas disponibles en el rango
    fechas_en_rango = df_completo[
        (df_completo['acq_date'] >= fecha_inicio) & 
        (df_completo['acq_date'] <= fecha_fin)
    ]['acq_date'].unique()
    
    fechas_ordenadas = sorted(list(fechas_en_rango))
    
    if len(fechas_ordenadas) == 0:
        print(f"No se encontraron fechas registradas entre {fecha_inicio} y {fecha_fin}.")
        return []
        
    print(f"Fechas candidatas encontradas en la base ({len(fechas_ordenadas)} días): {fechas_ordenadas}")
    print("\nProcesando y filtrando serie temporal...")
    
    resultados = []
    for fecha in fechas_ordenadas:
        ruta = procesar_una_fecha(fecha, df_fuente=df_completo, verbose=True)
        if ruta is not None:
            resultados.append((fecha, ruta))
            
    print(f"\nTotal de fechas válidas procesadas: {len(resultados)} de {len(fechas_ordenadas)}")
    return resultados

def procesar_fecha(fecha_elegida=None):
    """Función para compatibilidad con ejecuciones de un solo día."""
    df_completo = obtener_df_completo()
    if fecha_elegida is None:
        print("\n--- Fechas disponibles e incendios detectados ---")
        distribucion_fechas = df_completo['acq_date'].value_counts().sort_index()
        for fecha, cantidad in distribucion_fechas.items():
            print(f" *  {fecha} : {cantidad} focos")
            
        print("\n" + "="*50)
        fecha_elegida = input("Escribí la fecha que querés procesar (ejemplo: 2022-02-18): ").strip()
        print("="*50)
        
    return procesar_una_fecha(fecha_elegida, df_fuente=df_completo)

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        procesar_rango_fechas(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        procesar_fecha(sys.argv[1])
    else:
        procesar_fecha()
