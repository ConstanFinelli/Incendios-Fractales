import os
import json
import io
import base64
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import ListedColormap
from shapely.geometry import Point
from shapely.ops import unary_union
from PIL import Image
import folium
from folium import raster_layers, plugins

# Coordenadas de Corrientes
LAT_MIN, LAT_MAX = -30.8, -27.2
LON_MIN, LON_MAX = -59.8, -55.6

RUTA_GEOJSON_CORRIENTES = 'data/departamentos_corrientes.json'
RUTA_MASCARA_PROVINCIA = 'data/mascara_corrientes_256.npy'

def cargar_geometria_corrientes():
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
    lat = lat_min + (row / (tamano - 1)) * (lat_max - lat_min)
    lon = lon_min + (col / (tamano - 1)) * (lon_max - lon_min)
    return lat, lon

def identificar_departamentos_afectados(matriz_fuego, gdf_corrientes=None, tamano=256, lat_min=LAT_MIN, lat_max=LAT_MAX, lon_min=LON_MIN, lon_max=LON_MAX):
    if gdf_corrientes is None:
        gdf_corrientes = cargar_geometria_corrientes()
        
    if gdf_corrientes is None:
        return []
        
    mascara_prov = cargar_mascara_provincia (tamano)
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
    
    rgba_orientada = np.flipud(rgba)
    img = Image.fromarray(rgba_orientada)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def generar_mapa_estatico_corrientes(matriz_inicial, matriz_futura, mapa_riesgo,
                                     fecha_inicial="T0", fecha_final="T_final",
                                     mejores_variables=None, pasos_futuros=90,
                                     ruta_salida="output/mapa_corrientes_prediccion.png",
                                     matriz_final=None):
    if matriz_final is None:
        matriz_final = matriz_inicial

    if isinstance(matriz_futura, dict):
        m_24h = matriz_futura.get('24h', matriz_final)
        m_48h = matriz_futura.get('48h', m_24h)
        m_72h = matriz_futura.get('72h', m_48h)
    else:
        m_24h = m_48h = m_72h = matriz_futura

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_corrientes = cargar_geometria_corrientes()
    tamano = matriz_inicial.shape[0]
    mascara_prov = cargar_mascara_provincia(tamano)
    
    fuego_base_prov = np.logical_and(matriz_final > 0, mascara_prov).astype(int)
    fuego_24h_prov = np.logical_and(m_24h > 0, mascara_prov).astype(int)
    fuego_48h_prov = np.logical_and(m_48h > 0, mascara_prov).astype(int)
    fuego_72h_prov = np.logical_and(m_72h > 0, mascara_prov).astype(int)
    
    avance_24h_prov = np.logical_and(fuego_24h_prov > 0, fuego_base_prov == 0).astype(int)
    avance_48h_prov = np.logical_and(fuego_48h_prov > 0, fuego_24h_prov == 0).astype(int)
    avance_72h_prov = np.logical_and(fuego_72h_prov > 0, fuego_48h_prov == 0).astype(int)
    
    fig, axes = plt.subplots(1, 4, figsize=(28, 7.8), dpi=300)
    extent = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    
    subtitulo_clima = ""
    if mejores_variables is not None:
        v_vel, v_dir, hum, comb = mejores_variables
        subtitulo_clima = f"Condiciones: Viento {v_vel:.1f} km/h @ {v_dir:.0f}° | Humedad {hum:.1f}% | Combustible {comb:.2f}"
    
    for ax in axes:
        if gdf_corrientes is not None:
            gdf_corrientes.plot(ax=ax, color='#f7f9fa', zorder=1)
            
        ax.set_xlim(LON_MIN - 0.1, LON_MAX + 0.1)
        ax.set_ylim(LAT_MIN - 0.1, LAT_MAX + 0.1)
        ax.set_xlabel("Longitud Oeste", fontsize=9.5)
        ax.set_ylabel("Latitud Sur", fontsize=9.5)
        ax.grid(True, linestyle=':', alpha=0.35, color='#95a5a6', zorder=2)
    
    color_foco_base = '#2c3e50'
    color_tac_24h = '#f39c12'
    color_prev_48h = '#e67e22'
    color_est_72h = '#e74c3c'

    p_prov = mpatches.Patch(facecolor='#f7f9fa', edgecolor='#2c3e50', label='Provincia de Corrientes')
    p_base = mpatches.Patch(color=color_foco_base, label=f'Focos Activos Base ({fecha_final})')
    p_24h = mpatches.Patch(color=color_tac_24h, label='Avance Táctico (+24h)')
    p_48h = mpatches.Patch(color=color_prev_48h, label='Avance Preventivo (+48h)')
    p_72h = mpatches.Patch(color=color_est_72h, label='Avance Estratégico (+72h)')
    

    # Focos activos observados
    axes[0].set_title(f"1. Focos Activos Observados\n({fecha_final})", fontsize=11.5, fontweight='bold', pad=10)
    m1 = np.ma.masked_where(fuego_base_prov == 0, fuego_base_prov)
    axes[0].imshow(m1, extent=extent, origin='lower', cmap=ListedColormap([color_foco_base]), alpha=0.90, zorder=3)
    axes[0].legend(handles=[p_prov, p_base], loc='lower right', framealpha=0.92, fontsize=8.5)
    
    # Predicción a +24 Horas
    axes[1].set_title("2. Predicción a +24 Horas\n(+30 Ciclos | Nivel Táctico)", fontsize=11.5, fontweight='bold', pad=10)
    m2_base = np.ma.masked_where(fuego_base_prov == 0, fuego_base_prov)
    m2_av24 = np.ma.masked_where(avance_24h_prov == 0, avance_24h_prov)
    axes[1].imshow(m2_base, extent=extent, origin='lower', cmap=ListedColormap([color_foco_base]), alpha=0.60, zorder=3)
    axes[1].imshow(m2_av24, extent=extent, origin='lower', cmap=ListedColormap([color_tac_24h]), alpha=0.92, zorder=4)
    axes[1].legend(handles=[p_base, p_24h], loc='lower right', framealpha=0.92, fontsize=8.5)

    # Predicción a +48 Horas
    axes[2].set_title("3. Predicción a +48 Horas\n(+60 Ciclos | Nivel Preventivo)", fontsize=11.5, fontweight='bold', pad=10)
    m3_av48 = np.ma.masked_where(avance_48h_prov == 0, avance_48h_prov)
    axes[2].imshow(m2_base, extent=extent, origin='lower', cmap=ListedColormap([color_foco_base]), alpha=0.60, zorder=3)
    axes[2].imshow(m2_av24, extent=extent, origin='lower', cmap=ListedColormap([color_tac_24h]), alpha=0.85, zorder=4)
    axes[2].imshow(m3_av48, extent=extent, origin='lower', cmap=ListedColormap([color_prev_48h]), alpha=0.92, zorder=5)
    axes[2].legend(handles=[p_base, p_24h, p_48h], loc='lower right', framealpha=0.92, fontsize=8.2)
    
    # Predicción a +72 Horas
    axes[3].set_title("4. Predicción a +72 Horas e Isócronas\n(+90 Ciclos | Nivel Estratégico)", fontsize=11.5, fontweight='bold', pad=10)
    m4_av72 = np.ma.masked_where(avance_72h_prov == 0, avance_72h_prov)
    axes[3].imshow(m2_base, extent=extent, origin='lower', cmap=ListedColormap([color_foco_base]), alpha=0.60, zorder=3)
    axes[3].imshow(m2_av24, extent=extent, origin='lower', cmap=ListedColormap([color_tac_24h]), alpha=0.85, zorder=4)
    axes[3].imshow(m3_av48, extent=extent, origin='lower', cmap=ListedColormap([color_prev_48h]), alpha=0.85, zorder=5)
    axes[3].imshow(m4_av72, extent=extent, origin='lower', cmap=ListedColormap([color_est_72h]), alpha=0.92, zorder=6)
    axes[3].legend(handles=[p_base, p_24h, p_48h, p_72h], loc='lower right', framealpha=0.92, fontsize=7.8)
    
    for ax in axes:
        if gdf_corrientes is not None:
            gdf_corrientes.plot(ax=ax, color='none', edgecolor='#7f8c8d', linewidth=0.75, linestyle='--', zorder=7)
            gdf_corrientes.dissolve().plot(ax=ax, color='none', edgecolor='#1a252f', linewidth=1.6, zorder=8)
            
            for _, row in gdf_corrientes.iterrows():
                centroid = row.geometry.centroid
                ax.text(
                    centroid.x, centroid.y, row['departamento'],
                    fontsize=6.0, color='#2c3e50', ha='center', va='center', weight='bold', zorder=9,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground='white')]
                )
    
    plt.suptitle(
        f"Transposición Cartográfica y Modelado Predictivo Multi-Horizonte (24h, 48h, 72h) en Corrientes\n{subtitulo_clima}",
        fontsize=13.5, fontweight='bold', y=0.99
    )
    
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> [GIS Estático] Mapa Multi-Horizonte de Corrientes guardado con éxito en: {ruta_salida}")
    return ruta_salida

def generar_mapa_interactivo_corrientes(matriz_inicial, matriz_futura, mapa_riesgo,
                                        fecha_inicial="T0", fecha_final="T_final",
                                        mejores_variables=None, pasos_futuros=90,
                                        ruta_salida="output/mapa_corrientes_interactivo.html",
                                        matriz_final=None):
    if matriz_final is None:
        matriz_final = matriz_inicial

    if isinstance(matriz_futura, dict):
        m_24h = matriz_futura.get('24h', matriz_final)
        m_48h = matriz_futura.get('48h', m_24h)
        m_72h = matriz_futura.get('72h', m_48h)
    else:
        m_24h = m_48h = m_72h = matriz_futura

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    gdf_corrientes = cargar_geometria_corrientes()
    
    centro_lat = (LAT_MIN + LAT_MAX) / 2.0
    centro_lon = (LON_MIN + LON_MAX) / 2.0
    bounds_overlay = [[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]]
    
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=7,
        tiles=None,
        control_scale=True
    )
    
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
    
    data_uri_base = _crear_data_uri_rgba(
        matriz_final, color_rgb=(44, 62, 80), alfa=210, aplicar_mascara_provincia=True
    )
    avance_24h = np.logical_and(m_24h > 0, matriz_final == 0).astype(int)
    avance_48h = np.logical_and(m_48h > 0, m_24h == 0).astype(int)
    avance_72h = np.logical_and(m_72h > 0, m_48h == 0).astype(int)
    
    data_uri_24h = _crear_data_uri_rgba(avance_24h, color_rgb=(243, 156, 18), alfa=230, aplicar_mascara_provincia=True)
    data_uri_48h = _crear_data_uri_rgba(avance_48h, color_rgb=(230, 126, 34), alfa=230, aplicar_mascara_provincia=True)
    data_uri_72h = _crear_data_uri_rgba(avance_72h, color_rgb=(231, 76, 60), alfa=235, aplicar_mascara_provincia=True)
    
    avance_total = np.logical_and(m_72h > 0, matriz_final == 0).astype(int)
    data_uri_total = _crear_data_uri_rgba(avance_total, color_rgb=(192, 57, 43), alfa=220, aplicar_mascara_provincia=True)
    
    raster_layers.ImageOverlay(
        image=data_uri_base,
        bounds=bounds_overlay,
        opacity=0.88,
        name=f'🔥 Focos Activos Observados ({fecha_final})',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_24h,
        bounds=bounds_overlay,
        opacity=0.90,
        name='🟡 Predicción +24 Horas (Día 1 - Táctico)',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_48h,
        bounds=bounds_overlay,
        opacity=0.90,
        name='🟠 Predicción +48 Horas (Día 2 - Preventivo)',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_72h,
        bounds=bounds_overlay,
        opacity=0.92,
        name='🔴 Predicción +72 Horas (Día 3 - Estratégico)',
        interactive=True
    ).add_to(mapa)
    
    raster_layers.ImageOverlay(
        image=data_uri_total,
        bounds=bounds_overlay,
        opacity=0.85,
        name='⚠️ Avance Total Acumulado (+72h)',
        interactive=True,
        show=False
    ).add_to(mapa)
    
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
    
    plugins.MiniMap(toggle_display=True, tile_layer='CartoDB Positron', position='bottomleft').add_to(mapa)
    folium.LayerControl(position='topright', collapsed=False).add_to(mapa)
    
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
        bottom: 25px; right: 25px; width: 280px;
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
            <b>Simulador Multi-Horizonte Corrientes</b>
        </h4>
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
                             mejores_variables=None, pasos_futuros=90,
                             matriz_final=None):
    if matriz_final is None:
        matriz_final = matriz_inicial

    if isinstance(matriz_futura, dict):
        m_24h = matriz_futura.get('24h', matriz_final)
        m_48h = matriz_futura.get('48h', m_24h)
        m_72h = matriz_futura.get('72h', m_48h)
    else:
        m_24h = m_48h = m_72h = matriz_futura

    print("\n" + "="*65)
    print("TRANSPOSICIÓN ESPACIAL: PROYECTANDO HORIZONTES SOBRE CORRIENTES")
    print("="*65)
    print(f"Límites Geográficos: Lat [{LAT_MIN} a {LAT_MAX}] | Lon [{LON_MIN} a {LON_MAX}]")
    
    avance_24h = np.logical_and(m_24h > 0, matriz_final == 0).astype(int)
    avance_48h = np.logical_and(m_48h > 0, m_24h == 0).astype(int)
    avance_72h = np.logical_and(m_72h > 0, m_48h == 0).astype(int)
    
    ranking_24h = identificar_departamentos_afectados(avance_24h)
    ranking_48h = identificar_departamentos_afectados(avance_48h)
    ranking_72h = identificar_departamentos_afectados(avance_72h)
    
    print("\n--- IMPACTO DEPARTAMENTAL DESGLOSADO POR HORIZONTE ---")
    print(" [HORIZONTE TÁCTICO +24h (Día 1)]")
    if ranking_24h:
        for idx, item in enumerate(ranking_24h[:4], 1):
            print(f"   {idx}. {item['departamento']}: {item['celdas']} celdas ({item['porcentaje']:.1f}% del frente)")
    else:
        print("   -> Sin avance significativo sobre nuevas celdas.")
        
    print(" [HORIZONTE PREVENTIVO +48h (Día 2)]")
    if ranking_48h:
        for idx, item in enumerate(ranking_48h[:4], 1):
            print(f"   {idx}. {item['departamento']}: {item['celdas']} celdas ({item['porcentaje']:.1f}% del frente)")
    else:
        print("   -> Sin avance significativo sobre nuevas celdas.")
        
    print(" [HORIZONTE ESTRATÉGICO +72h (Día 3)]")
    if ranking_72h:
        for idx, item in enumerate(ranking_72h[:4], 1):
            print(f"   {idx}. {item['departamento']}: {item['celdas']} celdas ({item['porcentaje']:.1f}% del frente)")
    else:
        print("   -> Sin avance significativo sobre nuevas celdas.")
        
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
        'departamentos_afectados': {
            '24h': ranking_24h,
            '48h': ranking_48h,
            '72h': ranking_72h
        }
    }
