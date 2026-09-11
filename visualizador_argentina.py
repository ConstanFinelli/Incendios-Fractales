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
                                    mejores_variables=None, pasos_futuros=90,
                                    ruta_salida="output/mapa_argentina_prediccion.png",
                                    matriz_final=None):
    """
    Genera un mapa cartográfico GIS de alta resolución (300 DPI) para la República Argentina
    estructurado en 4 paneles análogos a los de Corrientes a escala nacional completa:
      Panel 1: Foco Base Observado en la República Argentina (fecha_final, sin rojo de predicción)
      Panel 2: Predicción a +24 Horas (+30 ciclos | Nivel Táctico)
      Panel 3: Predicción a +48 Horas (+60 ciclos | Nivel Preventivo)
      Panel 4: Predicción a +72 Horas y Riesgo Isócrono (+90 ciclos | Nivel Estratégico)
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    if isinstance(matriz_futura, dict):
        m_24h = matriz_futura.get('24h', matriz_final)
        m_48h = matriz_futura.get('48h', m_24h)
        m_72h = matriz_futura.get('72h', m_48h)
    else:
        m_24h = m_48h = m_72h = matriz_futura

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
        
    fuego_base_clean = np.logical_and(matriz_final > 0, mascara_prov).astype(int)
    fuego_24h_clean = np.logical_and(m_24h > 0, mascara_prov).astype(int)
    fuego_48h_clean = np.logical_and(m_48h > 0, mascara_prov).astype(int)
    fuego_72h_clean = np.logical_and(m_72h > 0, mascara_prov).astype(int)
    
    avance_24h_clean = np.logical_and(fuego_24h_clean > 0, fuego_base_clean == 0).astype(int)
    avance_48h_clean = np.logical_and(fuego_48h_clean > 0, fuego_24h_clean == 0).astype(int)
    avance_72h_clean = np.logical_and(fuego_72h_clean > 0, fuego_48h_clean == 0).astype(int)
    
    # Colores isócronos idénticos a los de Corrientes
    color_foco_base = '#2c3e50'    # Azul noche/carbón consolidado
    color_tac_24h = '#f39c12'      # Ámbar/dorado táctico
    color_prev_48h = '#e67e22'     # Naranja preventivo
    color_est_72h = '#e74c3c'      # Rojo carmesí estratégico
    
    fig, axes = plt.subplots(1, 4, figsize=(28, 10.5), dpi=300)
    
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
        
    # Renderizar mapa base de Argentina en los 4 paneles (mismo encuadre nacional completo)
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
                            ax.text(centroid.x, centroid.y, f"★ {texto_label}", fontsize=6.8,
                                    color='#b94a00', ha='center', va='center', weight='bold', zorder=6,
                                    path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])
                        else:
                            ax.text(centroid.x, centroid.y, texto_label, fontsize=5.5,
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
        ax.set_xlabel("Longitud Oeste", fontsize=9.0)
        ax.set_ylabel("Latitud Sur", fontsize=9.0)
        ax.grid(True, linestyle=':', alpha=0.3, color='#95a5a6', zorder=2)
        
    p_arg = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#bdc3c7', label='Territorio Nacional')
    p_corr = mpatches.Patch(facecolor='#fff9e6', edgecolor='#d35400', label='Provincia de Corrientes (Foco)')
    p_base = mpatches.Patch(color=color_foco_base, label=f'Foco Satelital Base ({fecha_final})')
    p_24h = mpatches.Patch(color=color_tac_24h, label='Avance Táctico (+24h)')
    p_48h = mpatches.Patch(color=color_prev_48h, label='Avance Preventivo (+48h)')
    p_72h = mpatches.Patch(color=color_est_72h, label='Avance Estratégico (+72h)')

    # -------------------------------------------------------------
    # PANEL 1: Foco Base Observado en Argentina (Sin Rojo de Predicción)
    # -------------------------------------------------------------
    axes[0].set_title(f"1. Foco Base Observado en Argentina\n({fecha_final})", fontsize=11.0, fontweight='bold', pad=10)
    m1 = np.ma.masked_where(fuego_base_clean == 0, fuego_base_clean)
    axes[0].imshow(m1, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_base]), alpha=0.92, zorder=4)
    axes[0].legend(handles=[p_arg, p_corr, p_base], loc='lower left', framealpha=0.92, fontsize=7.8)
    
    # -------------------------------------------------------------
    # PANEL 2: Predicción a +24 Horas en Argentina (Táctico)
    # -------------------------------------------------------------
    axes[1].set_title("2. Predicción a +24 Horas\n(+30 Ciclos | Nivel Táctico)", fontsize=11.0, fontweight='bold', pad=10)
    m2_base = np.ma.masked_where(fuego_base_clean == 0, fuego_base_clean)
    m2_av24 = np.ma.masked_where(avance_24h_clean == 0, avance_24h_clean)
    axes[1].imshow(m2_base, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_base]), alpha=0.65, zorder=3)
    axes[1].imshow(m2_av24, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_tac_24h]), alpha=0.95, zorder=4)
    axes[1].legend(handles=[p_arg, p_base, p_24h], loc='lower left', framealpha=0.92, fontsize=7.8)
    
    # -------------------------------------------------------------
    # PANEL 3: Predicción a +48 Horas en Argentina (Preventivo)
    # -------------------------------------------------------------
    axes[2].set_title("3. Predicción a +48 Horas\n(+60 Ciclos | Nivel Preventivo)", fontsize=11.0, fontweight='bold', pad=10)
    m3_av48 = np.ma.masked_where(avance_48h_clean == 0, avance_48h_clean)
    axes[2].imshow(m2_base, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_base]), alpha=0.65, zorder=3)
    axes[2].imshow(m2_av24, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_tac_24h]), alpha=0.85, zorder=4)
    axes[2].imshow(m3_av48, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_prev_48h]), alpha=0.95, zorder=5)
    axes[2].legend(handles=[p_arg, p_base, p_24h, p_48h], loc='lower left', framealpha=0.92, fontsize=7.5)
    
    # -------------------------------------------------------------
    # PANEL 4: Predicción a +72 Horas y Riesgo Isócrono en Argentina (Estratégico)
    # -------------------------------------------------------------
    axes[3].set_title("4. Predicción a +72 Horas e Isócronas\n(+90 Ciclos | Nivel Estratégico)", fontsize=11.0, fontweight='bold', pad=10)
    m4_av72 = np.ma.masked_where(avance_72h_clean == 0, avance_72h_clean)
    axes[3].imshow(m2_base, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_foco_base]), alpha=0.65, zorder=3)
    axes[3].imshow(m2_av24, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_tac_24h]), alpha=0.85, zorder=4)
    axes[3].imshow(m3_av48, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_prev_48h]), alpha=0.85, zorder=5)
    axes[3].imshow(m4_av72, extent=extent_fuego, origin='lower',
                   cmap=ListedColormap([color_est_72h]), alpha=0.95, zorder=6)
    axes[3].legend(handles=[p_arg, p_base, p_24h, p_48h, p_72h], loc='lower left', framealpha=0.92, fontsize=7.2)
    
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.suptitle(
        f"Transposición Cartográfica y Modelado Predictivo Multi-Horizonte (24h, 48h, 72h) en la República Argentina\n{subtitulo_clima}",
        fontsize=13.5, fontweight='bold', y=0.985
    )
    
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> [GIS Argentina] Mapa Multi-Horizonte de Argentina guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapa_interactivo_argentina(matriz_inicial, matriz_futura, mapa_riesgo,
                                       fecha_inicial="T0", fecha_final="T_final",
                                       mejores_variables=None, pasos_futuros=90,
                                       ruta_salida="output/mapa_argentina_interactivo.html",
                                       matriz_final=None):
    """
    Genera un mapa web interactivo en Folium para la República Argentina con:
      - Centrado nacional y regional con capas base (CartoDB Positron, OpenStreetMap, Esri Satélite).
      - Capa GeoJSON vectorial con las 24 provincias de Argentina y tooltips interactivos.
      - Provincia de Corrientes destacada con contorno diferenciado.
      - Capas raster georreferenciadas autónomas (Data URI Base64) del foco base, +24h, +48h y +72h.
      - Control de capas y leyenda flotante profesional.
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    if isinstance(matriz_futura, dict):
        m_24h = matriz_futura.get('24h', matriz_final)
        m_48h = matriz_futura.get('48h', m_24h)
        m_72h = matriz_futura.get('72h', m_48h)
    else:
        m_24h = m_48h = m_72h = matriz_futura

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
    data_uri_base = _crear_data_uri_rgba_argentina(matriz_final, color_rgb=(44, 62, 80), alfa=210)
    avance_24h = np.logical_and(m_24h > 0, matriz_final == 0).astype(int)
    avance_48h = np.logical_and(m_48h > 0, m_24h == 0).astype(int)
    avance_72h = np.logical_and(m_72h > 0, m_48h == 0).astype(int)
    
    data_uri_24h = _crear_data_uri_rgba_argentina(avance_24h, color_rgb=(243, 156, 18), alfa=230)
    data_uri_48h = _crear_data_uri_rgba_argentina(avance_48h, color_rgb=(230, 126, 34), alfa=230)
    data_uri_72h = _crear_data_uri_rgba_argentina(avance_72h, color_rgb=(231, 76, 60), alfa=235)
    
    raster_layers.ImageOverlay(
        image=data_uri_base,
        bounds=bounds_fuego,
        opacity=0.88,
        name=f'🔥 Foco Base Observado ({fecha_final})',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_24h,
        bounds=bounds_fuego,
        opacity=0.90,
        name='🟡 Predicción +24 Horas (Día 1 - Táctico)',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_48h,
        bounds=bounds_fuego,
        opacity=0.90,
        name='🟠 Predicción +48 Horas (Día 2 - Preventivo)',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_72h,
        bounds=bounds_fuego,
        opacity=0.92,
        name='🔴 Predicción +72 Horas (Día 3 - Estratégico)',
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
        bottom: 25px; right: 25px; width: 280px;
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
            <b>🇦🇷 Simulación Multi-Horizonte Argentina</b>
        </h4>
        <div style="margin-bottom: 5px;">
            <span style="background: #fff9e6; border: 1.5px solid #d35400; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Provincia:</b> Corrientes (Foco)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #2c3e50; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>Foco Base:</b> {fecha_final}
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #f39c12; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>+24h:</b> Nivel Táctico (Día 1)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #e67e22; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>+48h:</b> Nivel Preventivo (Día 2)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background: #e74c3c; width: 14px; height: 14px; display: inline-block; vertical-align: middle; border-radius: 2px; margin-right: 6px;"></span>
            <b>+72h:</b> Nivel Estratégico (Día 3)
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
                            mejores_variables=None, pasos_futuros=90,
                            matriz_final=None):
    """
    Función orquestadora principal que genera tanto el mapa estático GIS como el interactivo HTML
    para la República Argentina con los horizontes predictivos de 24h, 48h y 72h.
    """
    if matriz_final is None:
        matriz_final = matriz_inicial

    print("\n" + "="*65)
    print("TRANSPOSICIÓN ESPACIAL: PROYECTANDO HORIZONTES SOBRE ARGENTINA")
    print("="*65)
    print(f"Límites Nacionales: Lat [{ARG_LAT_MIN} a {ARG_LAT_MAX}] | Lon [{ARG_LON_MIN} a {ARG_LON_MAX}]")
    print(f"Ubicación del Foco (Corrientes): Lat [{LAT_MIN} a {LAT_MAX}] | Lon [{LON_MIN} a {LON_MAX}]")
    
    ruta_estatico = generar_mapa_estatico_argentina(
        matriz_inicial=matriz_inicial,
        matriz_final=matriz_final,
        matriz_futura=matriz_futura,
        mapa_riesgo=mapa_riesgo,
        fecha_inicial=fecha_inicial,
        fecha_final=fecha_final,
        mejores_variables=mejores_variables,
        pasos_futuros=pasos_futuros
    )
    
    ruta_interactivo = generar_mapa_interactivo_argentina(
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
        'mapa_estatico_argentina': ruta_estatico,
        'mapa_interactivo_argentina': ruta_interactivo
    }
