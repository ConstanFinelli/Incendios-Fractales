import os
import json
import io
import base64
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import ListedColormap
from shapely.geometry import Point
from shapely.ops import unary_union
from PIL import Image
import folium
from folium import raster_layers, plugins

# Constantes geográficas de la Provincia de Corrientes, Argentina
LAT_MIN, LAT_MAX = -30.8, -27.2
LON_MIN, LON_MAX = -59.8, -55.6

RUTA_GEOJSON_CORRIENTES = 'data/departamentos_corrientes.json'
RUTA_MASCARA_PROVINCIA = 'data/mascara_corrientes_256.npy'

def cargar_geometria_corrientes():
    """
    Carga el GeoDataFrame de los 25 departamentos de la provincia de Corrientes.
    Si el archivo local no existe, intenta descargarlo automáticamente.
    """
    if os.path.exists(RUTA_GEOJSON_CORRIENTES):
        try:
            return gpd.read_file(RUTA_GEOJSON_CORRIENTES)
        except Exception as e:
            print(f"Advertencia al leer GeoJSON local: {e}")
            
    url = 'https://raw.githubusercontent.com/mgaitan/departamentos_argentina/master/departamentos-corrientes.json'
    try:
        print("Descargando geometrías oficiales de Corrientes...")
        os.makedirs('data', exist_ok=True)
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        with open(RUTA_GEOJSON_CORRIENTES, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return gpd.read_file(RUTA_GEOJSON_CORRIENTES)
    except Exception as e:
        print(f"Error descargando geometrías: {e}")
        return None

def cargar_mascara_provincia(tamano=256):
    """
    Carga o calcula una máscara binaria 2D que indica qué píxeles de la grilla
    caen exactamente dentro del polígono de la provincia de Corrientes.
    Permite evitar desbordamientos del fuego sobre provincias vecinas o ríos.
    """
    if os.path.exists(RUTA_MASCARA_PROVINCIA):
        try:
            mascara = np.load(RUTA_MASCARA_PROVINCIA)
            if mascara.shape == (tamano, tamano):
                return mascara
        except Exception:
            pass
            
    gdf = cargar_geometria_corrientes()
    if gdf is None:
        return np.ones((tamano, tamano), dtype=bool)
        
    try:
        corrientes_geom = unary_union(gdf.geometry)
        lats = np.linspace(LAT_MIN, LAT_MAX, tamano)
        lons = np.linspace(LON_MIN, LON_MAX, tamano)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        puntos = [Point(x, y) for x, y in zip(lon_grid.ravel(), lat_grid.ravel())]
        gdf_grid = gpd.GeoDataFrame(geometry=puntos, crs='EPSG:4326')
        mascara = gdf_grid.within(corrientes_geom).values.reshape((tamano, tamano))
        os.makedirs('data', exist_ok=True)
        np.save(RUTA_MASCARA_PROVINCIA, mascara)
        return mascara
    except Exception as e:
        print(f"Advertencia al calcular máscara de Corrientes: {e}")
        return np.ones((tamano, tamano), dtype=bool)

def matriz_a_coordenadas(row, col, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX):
    """Convierte índices de matriz (row, col) a coordenadas geográficas (lat, lon)."""
    lat = lat_min + (row / (tamano - 1)) * (lat_max - lat_min)
    lon = lon_min + (col / (tamano - 1)) * (lon_max - lon_min)
    return lat, lon

def identificar_departamentos_afectados(matriz_fuego, gdf_corrientes=None, tamano=256,
                                       lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX):
    """
    Analiza la intersección espacial entre las celdas encendidas de una matriz
    y los departamentos de Corrientes. Retorna un ranking de departamentos afectados.
    """
    if gdf_corrientes is None:
        gdf_corrientes = cargar_geometria_corrientes()
        
    if gdf_corrientes is None:
        return []
        
    mascara_prov = cargar_mascara_provincia(tamano)
    matriz_filtrada = np.logical_and(matriz_fuego > 0, mascara_prov)
    
    filas, cols = np.where(matriz_filtrada)
    if len(filas) == 0:
        return []
        
    puntos_fuego = []
    for r, c in zip(filas, cols):
        lat, lon = matriz_a_coordenadas(r, c, tamano, lat_min, lat_max, lon_min, lon_max)
        puntos_fuego.append(Point(lon, lat))
        
    gdf_puntos = gpd.GeoDataFrame(geometry=puntos_fuego, crs="EPSG:4326")
    join_spatial = gpd.sjoin(gdf_puntos, gdf_corrientes, how="inner", predicate="within")
    
    if len(join_spatial) == 0:
        return []
        
    resumen = join_spatial['departamento'].value_counts()
    total_puntos = len(join_spatial)
    
    ranking = []
    for depto, celdas in resumen.items():
        porcentaje = (celdas / total_puntos) * 100
        ranking.append({
            'departamento': depto,
            'celdas': int(celdas),
            'porcentaje': porcentaje
        })
        
    return ranking

def _crear_data_uri_rgba(matriz, color_rgb=(231, 76, 60), alfa=220, aplicar_mascara_provincia=True):
    """
    Convierte una matriz binaria (256x256) en una imagen RGBA codificada en base64 Data URI
    compatible con folium ImageOverlay de forma completamente autónoma y portable.
    Aplica np.flipud para alinear la fila 0 (Sur en numpy) con el Norte en el formato de imagen.
    """
    tamano = matriz.shape[0]
    rgba = np.zeros((tamano, tamano, 4), dtype=np.uint8)
    
    mascara = matriz > 0
    if aplicar_mascara_provincia:
        mascara_prov = cargar_mascara_provincia(tamano)
        mascara = np.logical_and(mascara, mascara_prov)
        
    rgba[mascara, 0] = color_rgb[0]
    rgba[mascara, 1] = color_rgb[1]
    rgba[mascara, 2] = color_rgb[2]
    rgba[mascara, 3] = alfa
    
    # Folium espera que la fila 0 de la imagen sea la latitud máxima (Norte)
    rgba_orientada = np.flipud(rgba)
    img = Image.fromarray(rgba_orientada)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def generar_mapa_estatico_corrientes(matriz_inicial, matriz_futura, mapa_riesgo,
                                     fecha_inicial="T0", fecha_final="T_final",
                                     mejores_variables=None, pasos_futuros=100,
                                     ruta_salida="output/mapa_corrientes_prediccion.png",
                                     matriz_final=None):
    """
    Genera un mapa cartográfico GIS de alta resolución (300 DPI) con 3 paneles:
      Panel 1: Incendio Inicial Observado en Corrientes (fecha_inicial)
      Panel 2: Foco Final Expandido Observado (fecha_final, sin rojo de predicción)
      Panel 3: Mapa de Riesgo Predictivo Integrado (+N ciclos proyectados a partir del foco final)
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_corrientes = cargar_geometria_corrientes()
    tamano = matriz_inicial.shape[0]
    mascara_prov = cargar_mascara_provincia(tamano)
    
    # Filtrar fuegos para que respeten la silueta geográfica de Corrientes
    fuego_inicial_prov = np.logical_and(matriz_inicial > 0, mascara_prov).astype(int)
    fuego_final_prov = np.logical_and(matriz_final > 0, mascara_prov).astype(int)
    fuego_futuro_prov = np.logical_and(matriz_futura > 0, mascara_prov).astype(int)
    
    # El avance predictivo es la propagación hacia el futuro más allá de los focos finales observados
    fuego_avance_prov = np.logical_and(fuego_futuro_prov > 0, fuego_final_prov == 0).astype(int)
    
    # Construir mapa de riesgo acotado a la provincia
    riesgo_prov = np.zeros_like(matriz_inicial)
    riesgo_prov[fuego_futuro_prov > 0] = 2
    riesgo_prov[fuego_final_prov > 0] = 1
    
    fig, axes = plt.subplots(1, 3, figsize=(22, 7.8), dpi=300)
    extent = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    
    subtitulo_clima = ""
    if mejores_variables is not None:
        v_vel, v_dir, hum, comb = mejores_variables
        subtitulo_clima = f"Condiciones: Viento {v_vel:.1f} km/h @ {v_dir:.0f}° | Humedad {hum:.1f}% | Combustible {comb:.2f}"
    
    for ax in axes:
        # 1. Base poligonal de departamentos
        if gdf_corrientes is not None:
            gdf_corrientes.plot(ax=ax, color='#f7f9fa', zorder=1)
            
        ax.set_xlim(LON_MIN - 0.1, LON_MAX + 0.1)
        ax.set_ylim(LAT_MIN - 0.1, LAT_MAX + 0.1)
        ax.set_xlabel("Longitud Oeste", fontsize=10)
        ax.set_ylabel("Latitud Sur", fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.35, color='#95a5a6', zorder=2)
    
    # Colores definidos
    color_foco_inicial = '#d35400'     # Ámbar intenso
    color_avance_rojo = '#e74c3c'      # Rojo carmesí alerta
    color_foco_base = '#2c3e50'        # Azul noche/carbón consolidado
    
    # -------------------------------------------------------------
    # PANEL 1: Incendio Inicial Observado
    # -------------------------------------------------------------
    axes[0].set_title(f"1. Foco Inicial Observado\n({fecha_inicial})", fontsize=12, fontweight='bold', pad=10)
    m1 = np.ma.masked_where(fuego_inicial_prov == 0, fuego_inicial_prov)
    cmap_p1 = ListedColormap([color_foco_inicial])
    axes[0].imshow(m1, extent=extent, origin='lower', cmap=cmap_p1, alpha=0.85, zorder=3)
    p_obs = mpatches.Patch(color=color_foco_inicial, label=f'Foco Satelital Inicial ({fecha_inicial})')
    p_prov = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#2c3e50', label='Provincia de Corrientes')
    axes[0].legend(handles=[p_prov, p_obs], loc='lower right', framealpha=0.92)
    
    # -------------------------------------------------------------
    # PANEL 2: Foco Final Expandido Observado (Sin Rojo de Predicción)
    # -------------------------------------------------------------
    axes[1].set_title(f"2. Foco Final Expandido Observado\n({fecha_final})",
                     fontsize=12, fontweight='bold', pad=10)
    m2_final = np.ma.masked_where(fuego_final_prov == 0, fuego_final_prov)
    cmap_final = ListedColormap([color_foco_base])
    axes[1].imshow(m2_final, extent=extent, origin='lower', cmap=cmap_final, alpha=0.88, zorder=3)
    
    p_final = mpatches.Patch(color=color_foco_base, label=f'Foco Observado Consolidado ({fecha_final})')
    axes[1].legend(handles=[p_prov, p_final], loc='lower right', framealpha=0.92)
    
    # -------------------------------------------------------------
    # PANEL 3: Mapa de Riesgo Predictivo Integrado (+Pasos Futuros)
    # -------------------------------------------------------------
    axes[2].set_title(f"3. Mapa de Riesgo Predictivo Integrado\n(+{pasos_futuros} Ciclos del Autómata Celular)",
                     fontsize=12, fontweight='bold', pad=10)
    
    m3_base = np.ma.masked_where(fuego_final_prov == 0, fuego_final_prov)
    m3_avance = np.ma.masked_where(fuego_avance_prov == 0, fuego_avance_prov)
    
    cmap_base = ListedColormap([color_foco_base])
    cmap_avance = ListedColormap([color_avance_rojo])
    
    axes[2].imshow(m3_base, extent=extent, origin='lower', cmap=cmap_base, alpha=0.65, zorder=3)
    axes[2].imshow(m3_avance, extent=extent, origin='lower', cmap=cmap_avance, alpha=0.90, zorder=4)
    
    p_r1 = mpatches.Patch(color=color_foco_base, label=f'Foco Base Observado ({fecha_final})')
    p_r2 = mpatches.Patch(color=color_avance_rojo, label=f'Riesgo de Avance Proyectado (+{pasos_futuros} ciclos)')
    axes[2].legend(handles=[p_r1, p_r2], loc='lower right', framealpha=0.92)
    
    # DIBUJAR LÍMITES Y ETIQUETAS DE DEPARTAMENTOS POR ENCIMA DEL FUEGO
    for ax in axes:
        if gdf_corrientes is not None:
            # Límites departamentales
            gdf_corrientes.plot(ax=ax, color='none', edgecolor='#7f8c8d', linewidth=0.75, linestyle='--', zorder=4)
            # Límite provincial consolidado
            gdf_corrientes.dissolve().plot(ax=ax, color='none', edgecolor='#1a252f', linewidth=1.6, zorder=5)
            
            # Nombres de departamentos con halo blanco para máxima legibilidad
            for _, row in gdf_corrientes.iterrows():
                centroid = row.geometry.centroid
                ax.text(
                    centroid.x, centroid.y, row['departamento'],
                    fontsize=6.2, color='#2c3e50', ha='center', va='center', weight='bold', zorder=6,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground='white')]
                )
    
    # Título General Superior
    plt.suptitle(
        f"Transposición de Incendio y Modelado Predictivo en la Provincia de Corrientes\n{subtitulo_clima}",
        fontsize=14, fontweight='bold', y=0.99
    )
    
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> [GIS Estático] Mapa de Corrientes guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapa_interactivo_corrientes(matriz_inicial, matriz_futura, mapa_riesgo,
                                        fecha_inicial="T0", fecha_final="T_final",
                                        mejores_variables=None, pasos_futuros=100,
                                        ruta_salida="output/mapa_corrientes_interactivo.html",
                                        matriz_final=None):
    """
    Genera un mapa web interactivo en Folium con:
      - Capas base intercambiables (Positron, OpenStreetMap, Satélite ESRI).
      - Polígonos de los 25 departamentos de Corrientes con tooltips informativos.
      - Capa raster georreferenciada del Incendio Inicial (Data URI Base64).
      - Capa raster georreferenciada del Foco Final Observado (Data URI Base64).
      - Capa raster georreferenciada de la Predicción del Avance Futuro (Data URI Base64).
      - Control de capas y leyenda flotante elegante.
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_corrientes = cargar_geometria_corrientes()
    
    # Centro geográfico de Corrientes
    centro_lat = (LAT_MIN + LAT_MAX) / 2.0
    centro_lon = (LON_MIN + LON_MAX) / 2.0
    bounds_overlay = [[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]]
    
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=7,
        tiles=None,
        control_scale=True
    )
    
    # 1. Capas Base
    folium.TileLayer(
        tiles='CartoDB Positron',
        name='Mapa Claro (CartoDB Positron)',
        control=True
    ).add_to(mapa)
    
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Topográfico (OpenStreetMap)',
        control=True
    ).add_to(mapa)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satélite (Esri World Imagery)',
        control=True
    ).add_to(mapa)
    
    # 2. Capas Raster Georreferenciadas Autónomas (Data URI Base64)
    data_uri_inicial = _crear_data_uri_rgba(
        matriz_inicial, color_rgb=(211, 84, 0), alfa=210, aplicar_mascara_provincia=True
    )
    data_uri_final = _crear_data_uri_rgba(
        matriz_final, color_rgb=(44, 62, 80), alfa=200, aplicar_mascara_provincia=True
    )
    solo_avance = np.logical_and(matriz_futura > 0, matriz_final == 0).astype(int)
    data_uri_avance = _crear_data_uri_rgba(
        solo_avance, color_rgb=(231, 76, 60), alfa=230, aplicar_mascara_provincia=True
    )
    
    raster_layers.ImageOverlay(
        image=data_uri_inicial,
        bounds=bounds_overlay,
        opacity=0.85,
        name=f'🔥 Foco Inicial Observado ({fecha_inicial})',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_final,
        bounds=bounds_overlay,
        opacity=0.85,
        name=f'🛰️ Foco Final Expandido ({fecha_final})',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_avance,
        bounds=bounds_overlay,
        opacity=0.90,
        name=f'⚡ Predicción de Avance (+{pasos_futuros} ciclos)',
        interactive=True
    ).add_to(mapa)
    
    # 3. Capa Vectorial de Departamentos de Corrientes
    if gdf_corrientes is not None:
        estilo_depto = {
            'fillColor': '#34495e',
            'fillOpacity': 0.04,
            'color': '#2c3e50',
            'weight': 1.8,
            'dashArray': '4, 4'
        }
        folium.GeoJson(
            gdf_corrientes,
            name='División Departamental (Corrientes)',
            style_function=lambda x: estilo_depto,
            highlight_function=lambda x: {'fillColor': '#f39c12', 'fillOpacity': 0.25, 'weight': 2.8},
            tooltip=folium.GeoJsonTooltip(
                fields=['departamento', 'cabecera'],
                aliases=['Departamento:', 'Cabecera:'],
                style="background-color: white; color: #2c3e50; font-family: sans-serif; font-size: 12px; padding: 6px; border-radius: 4px;"
            )
        ).add_to(mapa)
    
    # 4. MiniMapa y Selector de Capas
    plugins.MiniMap(toggle_display=True, tile_layer='CartoDB Positron', position='bottomleft').add_to(mapa)
    folium.LayerControl(position='topright', collapsed=False).add_to(mapa)
    
    # 5. Leyenda Flotante HTML Profesional
    clima_html = ""
    if mejores_variables is not None:
        v_vel, v_dir, hum, comb = mejores_variables
        clima_html = f"""
        <div style="font-size: 11px; margin-top: 6px; color: #555; border-top: 1px solid #eee; padding-top: 5px;">
            <b>Viento:</b> {v_vel:.1f} km/h @ {v_dir:.0f}°<br>
            <b>Humedad:</b> {hum:.1f}% | <b>Comb:</b> {comb:.2f}
        </div>
        """
        
    leyenda_html = f"""
    <div style="
        position: fixed; 
        bottom: 25px; right: 25px; width: 270px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 2px solid #2c3e50;
        border-radius: 8px;
        padding: 12px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        z-index: 9999;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    ">
        <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 13px;">
            <b>Simulador Predictivo Corrientes</b>
        </h4>
        <div style="margin-bottom: 5px;">
            <span style="background: #d35400; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Foco Inicial:</b> {fecha_inicial}
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #2c3e50; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Foco Final Observado:</b> {fecha_final}
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #e74c3c; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Avance Proyectado:</b> +{pasos_futuros} ciclos
        </div>
        <div style="margin-bottom: 5px;">
            <span style="border: 1px dashed #2c3e50; width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 6px;"></span>
            Límite Departamental
        </div>
        {clima_html}
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))
    
    mapa.save(ruta_salida)
    print(f" -> [Web Interactivo] Mapa de Corrientes guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapas_corrientes(matriz_inicial, matriz_futura, mapa_riesgo,
                             fecha_inicial="T0", fecha_final="T_final",
                             mejores_variables=None, pasos_futuros=100,
                             matriz_final=None):
    """
    Función orquestadora principal que genera tanto el mapa estático GIS como el interactivo HTML,
    y realiza el análisis de departamentos en riesgo en la provincia de Corrientes.
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    print("\n" + "="*65)
    print("TRANSPOSICIÓN ESPACIAL: PROYECTANDO FRACTALES SOBRE MAPA DE CORRIENTES")
    print("="*65)
    print(f"Límites Geográficos: Lat [{LAT_MIN} a {LAT_MAX}] | Lon [{LON_MIN} a {LON_MAX}]")
    
    # 1. Análisis de departamentos afectados (foco en el nuevo avance predictivo)
    fuego_avance = np.logical_and(matriz_futura > 0, matriz_final == 0).astype(int)
    matriz_analisis = fuego_avance if np.sum(fuego_avance) > 0 else matriz_futura
    ranking = identificar_departamentos_afectados(matriz_analisis)
    if len(ranking) > 0:
        print("\n--- DEPARTAMENTOS DE CORRIENTES CON RIESGO DE AVANCE ---")
        for idx, item in enumerate(ranking[:6], 1):
            print(f" {idx}. {item['departamento']}: {item['celdas']} celdas en riesgo ({item['porcentaje']:.1f}% de la masa proyectada)")
    else:
        print(" -> No se detectaron celdas dentro del polígono departamental analizado.")
        
    # 2. Generar mapa estático PNG
    ruta_estatico = generar_mapa_estatico_corrientes(
        matriz_inicial=matriz_inicial,
        matriz_final=matriz_final,
        matriz_futura=matriz_futura,
        mapa_riesgo=mapa_riesgo,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        mejores_variables=mejores_variables,
        pasos_futuros=pasos_futuros
    )
    
    # 3. Generar mapa interactivo HTML
    ruta_interactivo = generar_mapa_interactivo_corrientes(
        matriz_inicial=matriz_inicial,
        matriz_final=matriz_final,
        matriz_futura=matriz_futura,
        mapa_riesgo=mapa_riesgo,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        mejores_variables=mejores_variables,
        pasos_futuros=pasos_futuros
    )
    
    return {
        'mapa_estatico': ruta_estatico,
        'mapa_interactivo': ruta_interactivo,
        'departamentos_afectados': ranking
    }
