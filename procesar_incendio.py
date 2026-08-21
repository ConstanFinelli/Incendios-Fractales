import json
import pandas as pd

nombre_archivo = './DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json'

try:
    with open(nombre_archivo, 'r') as f:
        datos = json.load(f)
    
    # Si la estructura viene como GeoJSON estándar, extraemos los datos numéricos
    if 'features' in datos:
        puntos = [feat['properties'] for feat in datos['features']]
        df = pd.DataFrame(puntos)
    else:
        # Si viene como un JSON de tabla plano
        df = pd.DataFrame(datos)
        
    print("¡Datos cargados con éxito!")
    print(f"Total de focos de incendio detectados: {len(df)}")
    print("\nColumnas disponibles para tu Algoritmo Genético:")
    print(df.columns.tolist())

        # --- NUEVO BLOQUE DE FILTRADO ---
    print("\n--- Distribución de incendios por fecha ---")
    distribucion_fechas = df['acq_date'].value_counts().sort_index()
    print(distribucion_fechas)
    
    # Elegimos el día con más incendios automáticamente para analizar
    dia_pico = distribucion_fechas.idxmax()
    print(f"\nEl día con mayor actividad es: {dia_pico} (Focos: {distribucion_fechas.max()})")
    
    # Filtrar el dataframe solo para ese día
    df_dia = df[df['acq_date'] == dia_pico]
    
    # Guardar este subconjunto en un archivo nuevo para trabajar más rápido
    df_dia.to_csv('output/incendios_dia_pico.csv', index=False)
    print(f"Subconjunto del día guardado con éxito como 'incendios_dia_pico.csv'")

    
except FileNotFoundError:
    print(f"Esperando el archivo... Asegúrate de guardarlo como '{nombre_archivo}' en esta misma carpeta.")