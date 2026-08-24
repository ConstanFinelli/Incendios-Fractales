import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np
from scipy.ndimage import binary_dilation, label

# 1. Cargar el archivo JSON usando pandas clásico
nombre_archivo = './DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json'

print("Cargando base de datos completa de la NASA...")
df_pandas = pd.read_json(nombre_archivo)

# 2. Convertir los datos a un GeoDataFrame para el mapa interactivo
print("Construyendo geometrías espaciales...")
geometria = [Point(xy) for xy in zip(df_pandas['longitude'], df_pandas['latitude'])]
df_completo = gpd.GeoDataFrame(df_pandas, geometry=geometria, crs="EPSG:4326")

# 3. Mostrar menú de fechas disponibles en la consola
print("\n--- Fechas disponibles e incendios detectados ---")
distribucion_fechas = df_completo['acq_date'].value_counts().sort_index()
for fecha, cantidad in distribucion_fechas.items():
    print(f" *  {fecha} : {cantidad} focos")

# 4. Solicitar al usuario que elija una fecha
print("\n" + "="*50)
fecha_elegida = input("Escribí la fecha que querés procesar (ejemplo: 2024-08-30): ").strip()
print("="*50)

# 5. Validar y filtrar los datos para el día elegido
if fecha_elegida in df_completo['acq_date'].values:
    df_dia = df_completo[df_completo['acq_date'] == fecha_elegida]
    print(f"\nProcesando focos globales del día {fecha_elegida}...")

    # --- BLOQUE DE RECORTE DE TU ZONA DE INTERÉS ---
    print("Aplicando zoom geográfico sobre la región de estudio...")
    lat_min, lat_max = -30, -25
    lon_min, lon_max = -55.0, -45

    # Filtramos para conservar SOLO los focos dentro del cuadrado crítico
    df_filtrado = df_dia[
        (df_dia['latitude'] >= lat_min) & (df_dia['latitude'] <= lat_max) &
        (df_dia['longitude'] >= lon_min) & (df_dia['longitude'] <= lon_max)
    ]
    print(f"Focos detectados dentro del área de estudio: {len(df_filtrado)}")
    
    if len(df_filtrado) == 0:
        print("No hay incendios registrados en esta zona para la fecha solicitada. Finalizando proceso.")
        import sys
        sys.exit(0)

    # 6. RASTERIZACIÓN DE LA ZONA RECORTADA
    tamano_matriz = 256
    matriz_binaria = np.zeros((tamano_matriz, tamano_matriz))

    # Mapear las coordenadas geográficas de la zona a índices de la matriz (0 a 255)
    lats_idx = np.floor((df_filtrado['latitude'] - lat_min) / (lat_max - lat_min) * (tamano_matriz - 1)).astype(int)
    lons_idx = np.floor((df_filtrado['longitude'] - lon_min) / (lon_max - lon_min) * (tamano_matriz - 1)).astype(int)

    # Rellenar la matriz: 1 significa que esa celda está quemada/en llamas
    for lat_i, lon_i in zip(lats_idx, lons_idx):
        matriz_binaria[lat_i, lon_i] = 1

    # Guardar la matriz recortada original con los puntos dispersos
    np.save(f'output/matriz_fractal_recorte_{fecha_elegida}.npy', matriz_binaria)

    # --- FILTRO MORFOLÓGICO DE DILATACIÓN (10 ITERACIONES) ---
    print("Aplicando filtro morfológico para conectar los puntos del frente de fuego...")
    matriz_continua = binary_dilation(matriz_binaria, iterations=11).astype(int)
    
    # Guardamos la versión engrosada intermedia
    np.save(f'output/matriz_fractal_recorte_continua_{fecha_elegida}.npy', matriz_continua)

    # --- ALGORITMO DE LIMPIEZA AUTOMÁTICA DE PUNTOS AISLADOS (RUIDO) ---
    print("Identificando componentes conectados para eliminar islas flotantes...")
    estructura_vecindad = np.ones((3, 3)) # Revisa las 8 direcciones contiguas
    matrices_etiquetadas, num_features = label(matriz_continua, structure=estructura_vecindad)
    
    # Contar cuántos píxeles tiene cada isla/componente independiente
    tamano_componentes = np.bincount(matrices_etiquetadas.ravel())
    
    # Buscamos la isla con mayor cantidad de píxeles (el cuerpo principal del incendio)
    # El índice 0 es el fondo blanco, por eso buscamos a partir del elemento 1
    id_componente_principal = np.argmax(tamano_componentes[1:]) + 1
    
    # Filtramos la matriz: Solo sobrevive la masa de fuego unificada
    matriz_limpia = (matrices_etiquetadas == id_componente_principal).astype(int)
    
    # Guardamos el archivo numérico definitivo que leerá tu Algoritmo Genético
    nombre_matriz_limpia_npy = f'matriz_objetivo_limpia_{fecha_elegida}.npy'
    np.save('output/' + nombre_matriz_limpia_npy, matriz_limpia)
    print(f" -> Guardado archivo .npy limpio: {nombre_matriz_limpia_npy}")
    print(f" -> Islas aisladas eliminadas con éxito: {num_features - 1}")

    # ----------------------------------------------------
    # RENDERIZADO DE LAS TRES ETAPAS GEOMÉTRICAS (.png)
    # ----------------------------------------------------
    # 1. Puntos dispersos originales
    plt.figure(figsize=(6,6))
    plt.imshow(matriz_binaria, cmap='binary', origin='lower')
    plt.title(f"Silueta Fractal Recortada (Matriz {fecha_elegida})")
    plt.xlabel("Índice X")
    plt.ylabel("Índice Y")
    plt.savefig(f'output/silueta_fractal_recorte_{fecha_elegida}.png', dpi=300)
    plt.close()

    # 2. Conexión por dilatación morfológica
    plt.figure(figsize=(6,6))
    plt.imshow(matriz_continua, cmap='binary', origin='lower')
    plt.title(f"Silueta Fractal Continua (Matriz {fecha_elegida})")
    plt.xlabel("Índice X")
    plt.ylabel("Índice Y")
    plt.savefig(f'output/silueta_fractal_continua_{fecha_elegida}.png', dpi=300)
    plt.close()

    # 3. El cuerpo principal limpio de focos secundarios aislados
    plt.figure(figsize=(6,6))
    plt.imshow(matriz_limpia, cmap='binary', origin='lower')
    plt.title(f"Cuerpo Principal Unificado y Limpio ({fecha_elegida})")
    plt.xlabel("Índice X")
    plt.ylabel("Índice Y")
    nombre_silueta_limpia_png = f'silueta_fractal_limpia_{fecha_elegida}.png'
    plt.savefig(nombre_silueta_limpia_png, dpi=300)
    plt.close()
    print(f" -> Guardada imagen definitiva sin ruido: {nombre_silueta_limpia_png}")

    # ----------------------------------------------------
    # GENERACIÓN DE RESPALDOS VISUALES (HTML e Imagen de calor)
    # ----------------------------------------------------
    print("Generando mapa web interactivo enfocado...")
    mapa_interactivo = df_filtrado.explore(
        column='brightness',
        cmap='YlOrRd',
        tiles='CartoDB Positron',
        marker_kwds=dict(radius=3, fill=True)
    )
    nombre_html = f'mapa_incendios_recorte_{fecha_elegida}.html'
    mapa_interactivo.save(nombre_html)
    
    print("Generando imagen estática de alta resolución enfocada...")
    plt.figure(figsize=(10, 8))
    sc = plt.scatter(
        df_filtrado['longitude'], 
        df_filtrado['latitude'], 
        c=df_filtrado['brightness'], 
        cmap='hot', 
        s=4.0, 
        alpha=0.6
    )
    plt.title(f"Foco de Incendio Estudiado - Región de Estudio {fecha_elegida}")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.colorbar(sc, label='Intensidad de Brillo (Brightness)')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    nombre_png = f'mapa_incendios_recorte_{fecha_elegida}.png'
    plt.savefig(nombre_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n" + "="*50)
    print("¡PROCESO FINALIZADO CON ÉXITO!")
    print("La matriz limpia de ruido y su silueta visual están listas para tu AG.")
    print("="*50)

else:
    print(f"\nError: La fecha '{fecha_elegida}' no es válida.")
