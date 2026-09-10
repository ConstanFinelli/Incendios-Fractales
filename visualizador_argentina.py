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
from PIL import Image
import folium
from folium import raster_layers, plugins

# Constantes geográficas de la zona de estudio (Corrientes, Argentina)
LAT_MIN, LAT_MAX = -30.8, -27.2
LON_MIN, LON_MAX = -59.8, -55.6

# Límites continentales de la República Argentina
ARG_LAT_MIN, ARG_LAT_MAX = -55.5, -21.5
ARG_LON_MIN, ARG_LON_MAX = -74.0, -53.0

# Límites de la región Litoral / Centro-Norte (foco regional)
REG_LAT_MIN, REG_LAT_MAX = -33.5, -25.0
REG_LON_MIN, REG_LON_MAX = -62.5, -53.5

RUTA_GEOJSON_ARGENTINA = 'data/provincias_argentina.json'

def cargar_geometria_argentina():
    """
    Carga el GeoDataFrame de las 24 provincias/jurisdicciones de la República Argentina.
    Si el archivo local no existe, descarga los departamentos oficiales, los disuelve
    por provincia, optimiza la topología y almacena la capa simplificada en caché local.
    """
    if os.path.exists(RUTA_GEOJSON_ARGENTINA):
        try:
            return gpd.read_file(RUTA_GEOJSON_ARGENTINA)
        except Exception as e:
            print(f"Advertencia al leer GeoJSON local de Argentina: {e}")
            
    url = 'https://raw.githubusercontent.com/mgaitan/departamentos_argentina/master/departamentos-argentina.json'
    try:
        print("Descargando geometrías provinciales oficiales de la República Argentina...")
        os.makedirs('data', exist_ok=True)
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            
        gdf_deptos = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
        gdf_provincias = gdf_deptos.dissolve(by='provincia').reset_index()[['provincia', 'geometry']]
        # Simplificación topológica para alto rendimiento y bajo peso
        gdf_provincias['geometry'] = gdf_provincias['geometry'].simplify(tolerance=0.01, preserve_topology=True)
        gdf_provincias.to_file(RUTA_GEOJSON_ARGENTINA, driver='GeoJSON')
        print(f" -> Geometrías de Argentina guardadas en {RUTA_GEOJSON_ARGENTINA}")
        return gdf_provincias
    except Exception as e:
        print(f"Error descargando geometrías de Argentina: {e}")
        return None

def _crear_data_uri_rgba_argentina(matriz, color_rgb=(231, 76, 60), alfa=220):
    """
    Convierte una matriz binaria (256x256) en una imagen RGBA codificada en base64 Data URI
    compatible con folium ImageOverlay de forma completamente autónoma y portable.
    """
    tamano = matriz.shape[0]
    rgba = np.zeros((tamano, tamano, 4), dtype=np.uint8)
    mascara = matriz > 0
    
    # Importar máscara provincial de Corrientes si existe para evitar desbordes fluviales
    try:
        from visualizador_corrientes import cargar_mascara_provincia
        mascara_prov = cargar_mascara_provincia(tamano)
        mascara = np.logical_and(mascara, mascara_prov)
    except Exception:
        pass
        
    rgba[mascara, 0] = color_rgb[0]
    rgba[mascara, 1] = color_rgb[1]
    rgba[mascara, 2] = color_rgb[2]
    rgba[mascara, 3] = alfa
    
    # Folium espera que la fila 0 sea la latitud máxima (Norte)
    rgba_orientada = np.flipud(rgba)
    img = Image.fromarray(rgba_orientada)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def generar_mapa_estatico_argentina(matriz_inicial, matriz_futura, mapa_riesgo,
                                    fecha_inicial="T0", fecha_final="T_final",
                                    mejores_variables=None, pasos_futuros=100,
                                    ruta_salida="output/mapa_argentina_prediccion.png"):
    """
    Genera un mapa cartográfico GIS de alta resolución (300 DPI) para la República Argentina
    estructurado en 3 paneles análogos a los de Corrientes, manteniendo la misma vista nacional
    completa sin acercamiento ni cambio de enfoque:
      Panel 1: Foco Inicial Observado en la República Argentina
      Panel 2: Predicción del Avance Proyectado (+N ciclos) en la República Argentina
      Panel 3: Mapa de Riesgo Predictivo Integrado sobre el Territorio Nacional
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_arg = cargar_geometria_argentina()
    extent_fuego = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    tamano = matriz_inicial.shape[0]
    
    # Aplicar máscara provincial de Corrientes para evitar desbordes irreales
    try:
        from visualizador_corrientes import cargar_mascara_provincia
        mascara_prov = cargar_mascara_provincia(tamano)
    except Exception:
        mascara_prov = np.ones((tamano, tamano), dtype=bool)
        
    fuego_inicial_clean = np.logical_and(matriz_inicial > 0, mascara_prov).astype(int)
    fuego_futuro_clean = np.logical_and(matriz_futura > 0, mascara_prov).astype(int)
    fuego_avance_clean = np.logical_and(fuego_futuro_clean > 0, fuego_inicial_clean == 0).astype(int)
    
    riesgo_clean = np.zeros_like(matriz_inicial)
    riesgo_clean[fuego_futuro_clean > 0] = 2
    riesgo_clean[fuego_inicial_clean > 0] = 1
    
    # Colores armónicos idénticos a los de Corrientes
    color_foco_inicial = '#d35400'     # Ámbar intenso
    color_avance_rojo = '#e74c3c'      # Rojo carmesí alerta
    color_foco_base = '#2c3e50'        # Azul noche/carbón
    
    fig, axes = plt.subplots(1, 3, figsize=(21, 10.5), dpi=300)
    
    subtitulo_clima = ""
    if mejores_variables is not None:
        v_vel, v_dir, hum, comb = mejores_variables
        subtitulo_clima = f"Condiciones: Viento {v_vel:.1f} km/h @ {v_dir:.0f}° | Humedad {hum:.1f}% | Combustible {comb:.2f}"
    
    provincias_principales = [
        'BUENOS AIRES', 'CORDOBA', 'SANTA FE', 'MENDOZA', 'SALTA',
        'TUCUMAN', 'CHACO', 'MISIONES', 'ENTRE RIOS', 'RIO NEGRO',
        'CHUBUT', 'SANTA CRUZ', 'CORRIENTES', 'NEUQUEN', 'LA PAMPA',
        'SAN JUAN', 'SANTIAGO DEL ESTERO', 'JUJUY', 'CATAMARCA', 'LA RIOJA',
        'FORMOSA', 'SAN LUIS'
    ]
    
    gdf_corrientes = None
    if gdf_arg is not None:
        gdf_corrientes = gdf_arg[gdf_arg['provincia'] == 'CORRIENTES']
        
    # Renderizar mapa base de Argentina en los 3 paneles (mismo encuadre nacional completo)
    for ax in axes:
        if gdf_arg is not None:
            gdf_arg.plot(ax=ax, color='#f7f9fa', edgecolor='#bdc3c7', linewidth=0.7, zorder=1)
            if gdf_corrientes is not None and len(gdf_corrientes) > 0:
                gdf_corrientes.plot(ax=ax, color='#fff9e6', edgecolor='#d35400', linewidth=1.3, zorder=2)
                
            for _, row in gdf_arg.iterrows():
                prov_nombre = row['provincia']
                if prov_nombre in provincias_principales:
                    centroid = row.geometry.centroid
                    if ARG_LAT_MIN <= centroid.y <= ARG_LAT_MAX and ARG_LON_MIN <= centroid.x <= ARG_LON_MAX:
                        texto_label = prov_nombre.title().replace(' De ', ' de ')
                        if prov_nombre == 'CORRIENTES':
                            ax.text(centroid.x, centroid.y, f"★ {texto_label}", fontsize=7.2,
                                    color='#b94a00', ha='center', va='center', weight='bold', zorder=6,
                                    path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])
                        else:
                            ax.text(centroid.x, centroid.y, texto_label, fontsize=5.8,
                                    color='#555555', ha='center', va='center', alpha=0.85, zorder=6,
                                    path_effects=[pe.withStroke(linewidth=2.0, foreground='white')])
                                    
        # Recuadro delimitador en la zona del foco (Corrientes)
        rect_corrientes = mpatches.Rectangle(
            (LON_MIN, LAT_MIN), LON_MAX - LON_MIN, LAT_MAX - LAT_MIN,
            linewidth=1.2, edgecolor='#c0392b', facecolor='none', linestyle='--', zorder=5
        )
        ax.add_patch(rect_corrientes)
        
        ax.set_xlim(ARG_LON_MIN - 0.5, ARG_LON_MAX + 0.5)
        ax.set_ylim(ARG_LAT_MIN - 0.5, ARG_LAT_MAX + 0.5)
        ax.set_xlabel("Longitud Oeste", fontsize=9.5)
        ax.set_ylabel("Latitud Sur", fontsize=9.5)
        ax.grid(True, linestyle=':', alpha=0.3, color='#95a5a6', zorder=2)
        
    # -------------------------------------------------------------
    # PANEL 1: Foco Inicial Observado en Argentina
    # -------------------------------------------------------------
    axes[0].set_title(f"1. Foco Inicial Observado\n({fecha_inicial})", fontsize=11.5, fontweight='bold', pad=10)
    m1 = np.ma.masked_where(fuego_inicial_clean == 0, fuego_inicial_clean)
    axes[0].imshow(m1, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_inicial]), alpha=0.95, zorder=4)
                   
    p_arg1 = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#bdc3c7', label='Territorio Nacional')
    p_corr1 = mpatches.Patch(facecolor='#fff9e6', edgecolor='#d35400', label='Provincia de Corrientes (Foco)')
    p_obs = mpatches.Patch(color=color_foco_inicial, label=f'Foco Satelital Observado ({fecha_inicial})')
    axes[0].legend(handles=[p_arg1, p_corr1, p_obs], loc='lower left', framealpha=0.92, fontsize=8.2)
    
    # -------------------------------------------------------------
    # PANEL 2: Predicción del Avance Proyectado en Argentina
    # -------------------------------------------------------------
    axes[1].set_title(f"2. Predicción del Avance Proyectado\n(+{pasos_futuros} Ciclos del Autómata Celular)",
                      fontsize=11.5, fontweight='bold', pad=10)
    m2_base = np.ma.masked_where(fuego_inicial_clean == 0, fuego_inicial_clean)
    m2_avance = np.ma.masked_where(fuego_avance_clean == 0, fuego_avance_clean)
    
    axes[1].imshow(m2_base, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_base]), alpha=0.60, zorder=3)
    axes[1].imshow(m2_avance, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_avance_rojo]), alpha=0.95, zorder=4)
                   
    p_arg2 = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#bdc3c7', label='Territorio Nacional')
    p_base = mpatches.Patch(color=color_foco_base, label=f'Foco Inicial Observado ({fecha_inicial})')
    p_pred = mpatches.Patch(color=color_avance_rojo, label=f'Avance Proyectado (+{pasos_futuros} ciclos)')
    axes[1].legend(handles=[p_arg2, p_base, p_pred], loc='lower left', framealpha=0.92, fontsize=8.2)
    
    # -------------------------------------------------------------
    # PANEL 3: Mapa de Riesgo Predictivo Integrado en Argentina
    # -------------------------------------------------------------
    axes[2].set_title("3. Mapa de Riesgo Predictivo Integrado\n(Superposición sobre Territorio Nacional)",
                      fontsize=11.5, fontweight='bold', pad=10)
    cmap_riesgo = ListedColormap([color_foco_base, color_avance_rojo])
    m3_riesgo = np.ma.masked_where(riesgo_clean == 0, riesgo_clean)
    axes[2].imshow(m3_riesgo, extent=extent_fuego, origin='lower',
                   cmap=cmap_riesgo, vmin=1, vmax=2, alpha=0.90, zorder=4)
                   
    p_arg3 = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#bdc3c7', label='Territorio Nacional')
    p_r1 = mpatches.Patch(color=color_foco_base, label='Foco Consolidado')
    p_r2 = mpatches.Patch(color=color_avance_rojo, label='Riesgo de Avance Futuro')
    axes[2].legend(handles=[p_arg3, p_r1, p_r2], loc='lower left', framealpha=0.92, fontsize=8.2)
    
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.suptitle(
        f"Transposición Cartográfica del Incendio en la República Argentina\n{subtitulo_clima}",
        fontsize=14, fontweight='bold', y=0.985
    )
    
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> [GIS Argentina] Mapa de Argentina guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapa_interactivo_argentina(matriz_inicial, matriz_futura, mapa_riesgo,
                                       fecha_inicial="T0", fecha_final="T_final",
                                       mejores_variables=None, pasos_futuros=100,
                                       ruta_salida="output/mapa_argentina_interactivo.html"):
    """
    Genera un mapa web interactivo en Folium para la República Argentina con:
      - Centrado nacional y regional con capas base (CartoDB Positron, OpenStreetMap, Esri Satélite).
      - Capa GeoJSON vectorial con las 24 provincias de Argentina y tooltips interactivos.
      - Provincia de Corrientes destacada con contorno diferenciado.
      - Capas raster georreferenciadas autónomas (Data URI Base64) del foco inicial y avance.
      - Control de capas y leyenda flotante profesional.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_arg = cargar_geometria_argentina()
    
    # Centro geográfico nacional (Córdoba / La Pampa)
    centro_lat = -38.4
    centro_lon = -63.6
    bounds_fuego = [[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]]
    
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=5,
        tiles=None,
        control_scale=True
    )
    
    # 1. Capas Base Intercambiables
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
    
    # 2. Capa Vectorial de Provincias de Argentina
    if gdf_arg is not None:
        def estilo_provincia(feature):
            nombre = feature['properties'].get('provincia', '')
            if nombre == 'CORRIENTES':
                return {
                    'fillColor': '#f39c12',
                    'fillOpacity': 0.15,
                    'color': '#d35400',
                    'weight': 2.5,
                    'dashArray': 'none'
                }
            return {
                'fillColor': '#34495e',
                'fillOpacity': 0.03,
                'color': '#7f8c8d',
                'weight': 1.3,
                'dashArray': '3, 3'
            }
            
        folium.GeoJson(
            gdf_arg,
            name='División Provincial (República Argentina)',
            style_function=estilo_provincia,
            highlight_function=lambda x: {'fillColor': '#3498db', 'fillOpacity': 0.25, 'weight': 2.5},
            tooltip=folium.GeoJsonTooltip(
                fields=['provincia'],
                aliases=['Provincia:'],
                style="background-color: white; color: #2c3e50; font-family: sans-serif; font-size: 12px; padding: 6px; border-radius: 4px;"
            )
        ).add_to(mapa)
        
    # 3. Capas Raster Georreferenciadas Autónomas (Data URI Base64)
    data_uri_inicial = _crear_data_uri_rgba_argentina(matriz_inicial, color_rgb=(211, 84, 0), alfa=215)
    solo_avance = np.logical_and(matriz_futura > 0, matriz_inicial == 0).astype(int)
    data_uri_avance = _crear_data_uri_rgba_argentina(solo_avance, color_rgb=(231, 76, 60), alfa=230)
    
    raster_layers.ImageOverlay(
        image=data_uri_inicial,
        bounds=bounds_fuego,
        opacity=0.88,
        name=f'🔥 Foco Inicial Satelital ({fecha_inicial})',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_avance,
        bounds=bounds_fuego,
        opacity=0.92,
        name=f'⚡ Predicción de Avance (+{pasos_futuros} ciclos)',
        interactive=True
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
            <b>Humedad:</b> {hum:.1f}% | <b>Combustible:</b> {comb:.2f}
        </div>
        """
        
    leyenda_html = f"""
    <div style="
        position: fixed; 
        bottom: 25px; right: 25px; width: 270px;
        background-color: rgba(255, 255, 255, 0.96);
        border: 2px solid #2c3e50;
        border-radius: 8px;
        padding: 12px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        z-index: 9999;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    ">
        <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 13px;">
            <b>🇦🇷 Simulación Incendio - Argentina</b>
        </h4>
        <div style="margin-bottom: 5px;">
            <span style="background: #fff9e6; border: 1.5px solid #d35400; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Provincia Afectada:</b> Corrientes
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #d35400; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Foco Inicial:</b> {fecha_inicial}
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #e74c3c; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Avance Proyectado:</b> +{pasos_futuros} ciclos
        </div>
        <div style="margin-bottom: 5px;">
            <span style="border: 1px dashed #7f8c8d; width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 6px;"></span>
            Límites Interprovinciales
        </div>
        {clima_html}
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))
    
    mapa.save(ruta_salida)
    print(f" -> [Web Argentina] Mapa interactivo guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapas_argentina(matriz_inicial, matriz_futura, mapa_riesgo,
                            fecha_inicial="T0", fecha_final="T_final",
                            mejores_variables=None, pasos_futuros=100):
    """
    Función orquestadora principal que genera tanto el mapa estático GIS como el interactivo HTML
    para la República Argentina, ubicando la catástrofe en el contexto territorial nacional.
    """
    print("\n" + "="*65)
    print("TRANSPOSICIÓN ESPACIAL: PROYECTANDO FRACTALES SOBRE MAPA DE ARGENTINA")
    print("="*65)
    print(f"Límites Nacionales: Lat [{ARG_LAT_MIN} a {ARG_LAT_MAX}] | Lon [{ARG_LON_MIN} a {ARG_LON_MAX}]")
    print(f"Ubicación del Foco (Corrientes): Lat [{LAT_MIN} a {LAT_MAX}] | Lon [{LON_MIN} a {LON_MAX}]")
    
    ruta_estatico = generar_mapa_estatico_argentina(
        matriz_inicial=matriz_inicial,
        matriz_futura=matriz_futura,
        mapa_riesgo=mapa_riesgo,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        mejores_variables=mejores_variables,
        pasos_futuros=pasos_futuros
    )
    
    ruta_interactivo = generar_mapa_interactivo_argentina(
        matriz_inicial=matriz_inicial,
        matriz_futura=matriz_futura,
        mapa_riesgo=mapa_riesgo,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        mejores_variables=mejores_variables,
        pasos_futuros=pasos_futuros
    )
    
    return {
        'mapa_estatico_argentina': ruta_estatico,
        'mapa_interactivo_argentina': ruta_interactivo
    }
