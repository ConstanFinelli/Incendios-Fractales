import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np

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
    df_filtrado = df_completo[df_completo['acq_date'] == fecha_elegida]
    print(f"\nProcesando {len(df_filtrado)} focos para el día {fecha_elegida}...")


    # Definir los límites del incendio (reemplaza con las coordenadas de tu zona de interés)
    lat_min, lat_max = df_filtrado['latitude'].min(), df_filtrado['latitude'].max()
    lon_min, lon_max = df_filtrado['longitude'].min(), df_filtrado['longitude'].max()

    tamano_matriz = 256
    matriz_binaria = np.zeros((tamano_matriz, tamano_matriz))

    # Mapear las coordenadas geográficas a índices de la matriz (0 a 255)
    lats_idx = np.floor((df_filtrado['latitude'] - lat_min) / (lat_max - lat_min) * (tamano_matriz - 1)).astype(int)
    lons_idx = np.floor((df_filtrado['longitude'] - lon_min) / (lon_max - lon_min) * (tamano_matriz - 1)).astype(int)

    # Rellenar la matriz: 1 significa que esa celda está quemada/en llamas
    for lat_i, lon_i in zip(lats_idx, lons_idx):
        matriz_binaria[lat_i, lon_i] = 1

    # Guardar la matriz para usarla como el objetivo del algoritmo genético
    np.save(f'output/matriz_fractal_{fecha_elegida}.npy', matriz_binaria)

    # Graficar la matriz continua en blanco y negro
    plt.figure(figsize=(6,6))
    plt.imshow(matriz_binaria, cmap='binary', origin='lower')
    plt.title(f"Silueta Fractal Continua (Matriz {fecha_elegida})")
    plt.savefig(f'output/silueta_fractal_{fecha_elegida}.png', dpi=300)
    plt.close()
    print(f"¡Matriz continua guardada como 'silueta_fractal_{fecha_elegida}.png'!")

    
    # ----------------------------------------------------
    # GENERACIÓN 1: MAPA INTERACTIVO (.html)
    # ----------------------------------------------------
    print("Generando mapa web interactivo...")
    mapa_interactivo = df_filtrado.explore(
        column='brightness',
        cmap='YlOrRd',
        tiles='CartoDB Positron',
        marker_kwds=dict(radius=3, fill=True)
    )
    nombre_html = f'mapa_incendios_{fecha_elegida}.html'
    mapa_interactivo.save('output/' + nombre_html)
    print(f" -> Guardado: {nombre_html}")
    
    # ----------------------------------------------------
    # GENERACIÓN 2: IMAGEN ESTÁTICA (.png)
    # ----------------------------------------------------
    print("Generando imagen estática de alta resolución...")
    plt.figure(figsize=(10, 8))
    
    # Graficamos los puntos usando el brillo/intensidad para el color
    sc = plt.scatter(
        df_filtrado['longitude'], 
        df_filtrado['latitude'], 
        c=df_filtrado['brightness'], 
        cmap='hot', 
        s=1.0, 
        alpha=0.4
    )
    
    plt.title(f"Distribución de Incendios en Brasil - {fecha_elegida}")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.colorbar(sc, label='Intensidad de Brillo (Brightness)')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    nombre_png = f'mapa_incendios_{fecha_elegida}.png'
    plt.savefig('output/' + nombre_png, dpi=300, bbox_inches='tight')
    plt.close() # Cierra la figura para liberar memoria
    print(f" -> Guardada: {nombre_png}")
    
    print("\n" + "="*50)
    print("¡PROCESO FINALIZADO CON ÉXITO!")
    print("Revisá tu carpeta actual para abrir ambos archivos.")
    print("="*50)

else:
    print(f"\nError: La fecha '{fecha_elegida}' no es válida.")
