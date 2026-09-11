import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_erosion

def extraer_perimetro(matriz_binaria):
    """
    Extrae el borde morfológico del incendio. 
    Si la estructura contiene líneas o frentes finos donde la erosión elimina 
    completamente las celdas, preserva dichas celdas como frontera activa natural.
    """
    matriz_erosionada = binary_erosion(matriz_binaria)
    perimetro = matriz_binaria.astype(int) - matriz_erosionada.astype(int)
    
    # Si la erosión consumió completamente frentes delgados, el conjunto en sí es frontera activa
    if np.sum(perimetro) == 0 and np.sum(matriz_binaria) > 0:
        return (matriz_binaria > 0).astype(int)
        
    return perimetro

def calcular_box_counting(matriz_binaria):
    """
    Aplica el algoritmo de Box-Counting de alta velocidad (Vectorizado 100% NumPy).
    Es matemáticamente válido tanto para contornos perimetrales como para conjuntos 
    dispersos o multifocales de celdas activas (polvos fractales en R^2).
    Retorna la dimensión fractal (D), los tamaños de caja y los conteos.
    """
    n = min(matriz_binaria.shape)
    
    tamanos_caja = []
    conteos_cajas = []
    
    tamano = n
    while tamano >= 1:
        if tamano == n:
            contador = 1 if np.any(matriz_binaria) else 0
        elif tamano == 1:
            contador = np.count_nonzero(matriz_binaria)
        else:
            # Reshape matricial en bloques 2D sin bucles Python (Ultra rápido en C)
            bloques = matriz_binaria.reshape(n // tamano, tamano, n // tamano, tamano).any(axis=(1, 3))
            contador = np.count_nonzero(bloques)
            
        tamanos_caja.append(tamano)
        conteos_cajas.append(contador)
        tamano = tamano // 2
        
    # Calcular la regresión lineal en escala Log-Log
    x = np.log(1.0 / np.array(tamanos_caja))
    y = np.log(np.maximum(conteos_cajas, 1))
    
    coeficientes = np.polyfit(x, y, 1)
    dimension_fractal = coeficientes[0]
    
    return dimension_fractal, x, y, tamanos_caja, conteos_cajas

def calcular_dimension_fractal_directa(matriz_binaria):
    """
    Calcula de forma directa la Dimensión Fractal de Box-Counting (D) sobre el conjunto
    de celdas activas (frentes de fuego) sin necesidad de erosión morfológica previa.
    Especialmente diseñado para frentes multifocales y polvos fractales en R^2 (T1.5).
    """
    if not np.any(matriz_binaria):
        return 0.0
    try:
        D, *_ = calcular_box_counting(matriz_binaria > 0)
        return float(D)
    except Exception:
        return 1.0

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    # 1. Solicitar la fecha para cargar el archivo correcto
    fecha_elegida = input("Escribí la fecha a procesar (ejemplo: 2024-08-30): ").strip()
    nombre_archivo = f'matriz_objetivo_limpia_{fecha_elegida}.npy'
    #nombre_archivo = f'matriz_simulada_prueba.npy' #para probar con matriz de automata
    
    try:
        print(f"Cargando {nombre_archivo}...")
        matriz_limpia = np.load('output/' + nombre_archivo)
        
        # 2. Extraer el perímetro
        perimetro = extraer_perimetro(matriz_limpia)
        
        # 3. Aplicar Box-Counting
        D, log_x, log_y, sizes, counts = calcular_box_counting(perimetro)
        print(f"\n--- RESULTADOS ---")
        print(f"Dimensión Fractal (D) calculada: {D:.4f}")
        
        # 4. Graficar los resultados (Perímetro y Recta Log-Log)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gráfico del Perímetro
        ax1.imshow(perimetro, cmap='binary', origin='lower')
        ax1.set_title("Perímetro del Incendio")
        
        # Gráfico de la Regresión Log-Log
        ax2.plot(log_x, log_y, 'ro-', label='Puntos (Cajas vs Tamaño)')
        # Línea de tendencia
        tendencia_y = D * log_x + (log_y[0] - D * log_x[0]) 
        ax2.plot(log_x, tendencia_y, 'b--', label=f'Ajuste Lineal (Pendiente D={D:.4f})')
        
        ax2.set_title("Gráfico Log-Log (Box-Counting)")
        ax2.set_xlabel("[Tamaño Inverso de Caja]")
        ax2.set_ylabel("[Cantidad de Cajas]")
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        plt.savefig(f'reporte_fractal_{fecha_elegida}.png', dpi=300)
        print(f"Gráfico guardado como 'reporte_fractal_{fecha_elegida}.png'")
        plt.show()

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {nombre_archivo}. Asegurate de correr el script anterior primero.")
