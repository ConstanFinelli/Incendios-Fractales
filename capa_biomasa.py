import os
import json
import ssl
import urllib.request
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patheffects as pe
import geopandas as gpd
from shapely.ops import unary_union
import shapely

# Coordenadas de la provincia de Corrientes
LAT_MIN, LAT_MAX = -30.8, -27.2
LON_MIN, LON_MAX = -59.8, -55.6
TAMANO_GRID = 256

# Rutas de almacenamiento local
DIR_DATA = 'data'
DIR_OUTPUT = 'output'
RUTA_GEOJSON_AGUAS = os.path.join(DIR_DATA, 'ign_aguas_perenne.geojson')
RUTA_GEOJSON_HIDROFILA = os.path.join(DIR_DATA, 'ign_vegetacion_hidrofila.geojson')
RUTA_GEOJSON_FORESTACION = os.path.join(DIR_DATA, 'ign_plantaciones_forestales.geojson')
RUTA_MASCARA_PROVINCIA = os.path.join(DIR_DATA, 'mascara_corrientes_256.npy')
RUTA_MAPA_COMBUSTIBLE = os.path.join(DIR_DATA, 'mapa_combustible_256.npy')
RUTA_CATEGORIAS_COBERTURA = os.path.join(DIR_DATA, 'categorias_cobertura_256.npy')
RUTA_GEOJSON_CORRIENTES = os.path.join(DIR_DATA, 'departamentos_corrientes.json')

# Categorías y valores de combustible base
CAT_EXTERIOR = 0
CAT_AGUA = 1
CAT_HIDROFILA = 2
CAT_PASTIZAL = 3
CAT_FORESTAL = 4

COMBUSTIBLE_VALORES = {
    CAT_EXTERIOR: 0.0,
    CAT_AGUA: 0.0,
    CAT_HIDROFILA: 0.2,
    CAT_PASTIZAL: 0.6,
    CAT_FORESTAL: 1.0
}

_mapa_combustible_cache = None
_categorias_cobertura_cache = None


def descargar_capas_ign_si_faltan():
    os.makedirs(DIR_DATA, exist_ok=True)
    ctx = ssl._create_unverified_context()
    
    capas = {
        'aguas': ('ign:areas_de_aguas_continentales_perenne', RUTA_GEOJSON_AGUAS),
        'hidrofila': ('ign:vegetacion_hidrofila_ED020', RUTA_GEOJSON_HIDROFILA),
        'forestacion': ('ign:vegetacion_arborea_060301', RUTA_GEOJSON_FORESTACION)
    }
    
    for nombre, (tipo_wfs, ruta_local) in capas.items():
        if not os.path.exists(ruta_local):
            url = (
                f'https://wms.ign.gob.ar/geoserver/ows?service=WFS&version=1.0.0'
                f'&request=GetFeature&typeName={tipo_wfs}&outputFormat=application/json'
                f'&bbox={LON_MIN},{LAT_MIN},{LON_MAX},{LAT_MAX},EPSG:4326'
            )
            print(f"Descargando capa IGN de {nombre}...")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                with open(ruta_local, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                print(f"Capa {nombre} guardada exitosamente ({len(data.get('features', []))} geometrías).")
            except Exception as e:
                print(f"Aviso: no se pudo descargar capa IGN ({nombre}): {e}")


def cargar_o_generar_mapa_combustible(tamano=TAMANO_GRID, recalcular=False):
    global _mapa_combustible_cache, _categorias_cobertura_cache
    
    if not recalcular and _mapa_combustible_cache is not None:
        if _mapa_combustible_cache.shape == (tamano, tamano):
            return _mapa_combustible_cache, _categorias_cobertura_cache

    if not recalcular and os.path.exists(RUTA_MAPA_COMBUSTIBLE) and os.path.exists(RUTA_CATEGORIAS_COBERTURA):
        try:
            mapa_c = np.load(RUTA_MAPA_COMBUSTIBLE)
            cat_c = np.load(RUTA_CATEGORIAS_COBERTURA)
            if mapa_c.shape == (tamano, tamano) and cat_c.shape == (tamano, tamano):
                _mapa_combustible_cache = mapa_c
                _categorias_cobertura_cache = cat_c
                return mapa_c, cat_c
        except Exception:
            pass

    print("\nGenerando Capa Raster de Cobertura de Suelo y Biomasa...")
    descargar_capas_ign_si_faltan()
    
    if os.path.exists(RUTA_MASCARA_PROVINCIA):
        mascara_prov = np.load(RUTA_MASCARA_PROVINCIA)
    else:
        from visualizador_corrientes import cargar_mascara_provincia
        mascara_prov = cargar_mascara_provincia(tamano)
        
    lats = np.linspace(LAT_MIN, LAT_MAX, tamano)
    lons = np.linspace(LON_MIN, LON_MAX, tamano)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    pts_x = lon_grid.ravel()
    pts_y = lat_grid.ravel()
    
    categorias = np.zeros((tamano, tamano), dtype=int)
    mapa_combustible = np.zeros((tamano, tamano), dtype=float)
    
    categorias[mascara_prov] = CAT_PASTIZAL
    mapa_combustible[mascara_prov] = COMBUSTIBLE_VALORES[CAT_PASTIZAL]
    
    if os.path.exists(RUTA_GEOJSON_FORESTACION):
        try:
            gdf_f = gpd.read_file(RUTA_GEOJSON_FORESTACION)
            if len(gdf_f) > 0:
                union_f = unary_union(gdf_f.geometry)
                is_forest = shapely.contains_xy(union_f, pts_x, pts_y).reshape((tamano, tamano))
                mask_f = np.logical_and(mascara_prov, is_forest)
                categorias[mask_f] = CAT_FORESTAL
                mapa_combustible[mask_f] = COMBUSTIBLE_VALORES[CAT_FORESTAL]
        except Exception as e:
            print(f"Aviso al procesar plantaciones forestales: {e}")

    if os.path.exists(RUTA_GEOJSON_HIDROFILA):
        try:
            gdf_h = gpd.read_file(RUTA_GEOJSON_HIDROFILA)
            if len(gdf_h) > 0:
                union_h = unary_union(gdf_h.geometry)
                is_hidro = shapely.contains_xy(union_h, pts_x, pts_y).reshape((tamano, tamano))
                mask_h = np.logical_and(mascara_prov, is_hidro)
                categorias[mask_h] = CAT_HIDROFILA
                mapa_combustible[mask_h] = COMBUSTIBLE_VALORES[CAT_HIDROFILA]
        except Exception as e:
            print(f"Aviso al procesar vegetación hidrófila: {e}")

    if os.path.exists(RUTA_GEOJSON_AGUAS):
        try:
            gdf_a = gpd.read_file(RUTA_GEOJSON_AGUAS)
            if len(gdf_a) > 0:
                union_a = unary_union(gdf_a.geometry)
                is_agua = shapely.contains_xy(union_a, pts_x, pts_y).reshape((tamano, tamano))
                mask_a = np.logical_and(mascara_prov, is_agua)
                categorias[mask_a] = CAT_AGUA
                mapa_combustible[mask_a] = COMBUSTIBLE_VALORES[CAT_AGUA]
        except Exception as e:
            print(f"Aviso al procesar aguas continentales: {e}")

    try:
        np.save(RUTA_MAPA_COMBUSTIBLE, mapa_combustible)
        np.save(RUTA_CATEGORIAS_COBERTURA, categorias)
        print(f"Capas persistidas en {RUTA_MAPA_COMBUSTIBLE} y {RUTA_CATEGORIAS_COBERTURA}")
    except Exception as e:
        print(f"Aviso al guardar matrices de biomasa: {e}")

    _mapa_combustible_cache = mapa_combustible
    _categorias_cobertura_cache = categorias
    
    total_prov = max(1, np.sum(mascara_prov))
    n_agua = np.sum(categorias == CAT_AGUA)
    n_hidro = np.sum(categorias == CAT_HIDROFILA)
    n_past = np.sum(categorias == CAT_PASTIZAL)
    n_forest = np.sum(categorias == CAT_FORESTAL)
    
    print(f"Resumen de Cobertura Terrestre (Corrientes {tamano}x{tamano}):")
    print(f"  - Cuerpos de Agua y Esteros (C=0.0): {n_agua:5d} celdas ({n_agua/total_prov*100:4.1f}%)")
    print(f"  - Bañados y Vegetación Hidrófila (C=0.2): {n_hidro:5d} celdas ({n_hidro/total_prov*100:4.1f}%)")
    print(f"  - Pastizales y Sabanas (C=0.6): {n_past:5d} celdas ({n_past/total_prov*100:4.1f}%)")
    print(f"  - Plantaciones Forestales (C=1.0): {n_forest:5d} celdas ({n_forest/total_prov*100:4.1f}%)")
    
    return mapa_combustible, categorias


def obtener_mapa_combustible(tamano=TAMANO_GRID):
    mapa_c, _ = cargar_o_generar_mapa_combustible(tamano)
    return mapa_c


def generar_mapa_cobertura_grafico(tamano=TAMANO_GRID, ruta_salida=os.path.join(DIR_OUTPUT, "mapa_cobertura_combustible.png")):
    os.makedirs(DIR_OUTPUT, exist_ok=True)
    mapa_comb, categorias = cargar_o_generar_mapa_combustible(tamano)
    gdf_deptos = None
    if os.path.exists(RUTA_GEOJSON_CORRIENTES):
        try:
            gdf_deptos = gpd.read_file(RUTA_GEOJSON_CORRIENTES)
        except Exception:
            pass
    colores = ['#f4f6f7', '#2980b9', '#1abc9c', '#f39c12', '#1e8449']
    cmap = ListedColormap(colores)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)

    fig, ax = plt.subplots(figsize=(11, 10), dpi=300)
    extent = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    
    im = ax.imshow(categorias, origin='lower', extent=extent, cmap=cmap, norm=norm, zorder=1)
    
    if gdf_deptos is not None:
        gdf_deptos.boundary.plot(ax=ax, color='#2c3e50', linewidth=0.8, linestyle='--', zorder=3)
        for _, fila in gdf_deptos.iterrows():
            c = fila.geometry.centroid
            nombre = str(fila.get('departamento', '')).title()
            ax.text(
                c.x, c.y, nombre, fontsize=6.5, fontweight='bold', color='#1a252f',
                ha='center', va='center', zorder=5,
                path_effects=[pe.withStroke(linewidth=2.0, foreground='white')]
            )

    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.grid(True, linestyle=':', alpha=0.5, color='#7f8c8d', zorder=2)
    ax.set_xlabel("Longitud Oeste", fontsize=9, labelpad=5)
    ax.set_ylabel("Latitud Sur", fontsize=9, labelpad=5)
    
    mascara_prov = (categorias > 0)
    total_prov = max(1, np.sum(mascara_prov))
    pct_agua = np.sum(categorias == CAT_AGUA) / total_prov * 100
    pct_hidro = np.sum(categorias == CAT_HIDROFILA) / total_prov * 100
    pct_past = np.sum(categorias == CAT_PASTIZAL) / total_prov * 100
    pct_forest = np.sum(categorias == CAT_FORESTAL) / total_prov * 100

    ax.set_title(
        "PROVINCIA DE CORRIENTES - MAPA DE COBERTURA DE SUELO Y BIOMASA\n"
        "Heterogeneidad Espacial para Modelado Físico en Autómata Celular (IGN Argentina)",
        fontsize=11, fontweight='bold', pad=12, color='#1a252f'
    )

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2980b9', edgecolor='#1b4f72', label=f'Cuerpos de Agua y Esteros Profundos (C = 0.0 - Incombustible) [{pct_agua:.1f}%]'),
        Patch(facecolor='#1abc9c', edgecolor='#117a65', label=f'Bañados y Vegetación Hidrófila / Pajonales (C = 0.2 - Muy Baja Ignición) [{pct_hidro:.1f}%]'),
        Patch(facecolor='#f39c12', edgecolor='#b9770e', label=f'Pastizales, Sabanas y Malezas (C = 0.6 - Propagación Base) [{pct_past:.1f}%]'),
        Patch(facecolor='#1e8449', edgecolor='#145a32', label=f'Plantaciones Forestales de Pino / Eucalipto (C = 1.0 - Máxima Carga) [{pct_forest:.1f}%]'),
        Patch(facecolor='#f4f6f7', edgecolor='#bdc3c7', label='Límites Exteriores / Ríos Paraná y Uruguay (C = 0.0)')
    ]
    
    ax.legend(
        handles=legend_elements, loc='lower right', frameon=True, facecolor='white',
        edgecolor='#95a5a6', framealpha=0.95, fontsize=8, title="Clasificación Biofísica de Combustible",
        title_fontsize=8.5
    )

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Mapa de cobertura de biomasa generado en: {ruta_salida}")
    return ruta_salida


if __name__ == '__main__':
    mapa_c, cat_c = cargar_o_generar_mapa_combustible(recalcular=True)
    generar_mapa_cobertura_grafico()
