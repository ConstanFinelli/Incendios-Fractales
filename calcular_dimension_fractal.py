import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import binary_erosion
import os

def extraer_perimetro(matriz_binaria):
    matriz_erosionada = binary_erosion(matriz_binaria)
    perimetro = matriz_binaria.astype(int) - matriz_erosionada.astype(int)
    
    if np.sum(perimetro) == 0 and np.sum(matriz_binaria) > 0:
        return (matriz_binaria > 0).astype(int)
        
    return perimetro

def calcular_box_counting(matriz_binaria):
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
            bloques = matriz_binaria.reshape(n // tamano, tamano, n // tamano, tamano).any(axis=(1, 3))
            contador = np.count_nonzero(bloques)
            
        tamanos_caja.append(tamano)
        conteos_cajas.append(contador)
        tamano = tamano // 2
        
    x = np.log(1.0 / np.array(tamanos_caja))
    y = np.log(np.maximum(conteos_cajas, 1))
    
    coeficientes = np.polyfit(x, y, 1)
    dimension_fractal = coeficientes[0]
    
    return dimension_fractal, x, y, tamanos_caja, conteos_cajas

def calcular_dimension_fractal_directa(matriz_binaria):
    if not np.any(matriz_binaria):
        return 0.0
    try:
        D, *_ = calcular_box_counting(matriz_binaria > 0)
        return float(D)
    except Exception:
        return 1.0
    
if __name__ == "__main__":
    fecha_elegida = input("Escribí la fecha a procesar (ejemplo: 2024-08-30): ").strip()
    nombre_archivo = f'matriz_objetivo_limpia_{fecha_elegida}.npy'
    #nombre_archivo = f'matriz_simulada_prueba.npy' #para probar con matriz de automata
    
    try:
        ruta_archivo = os.path.join('output', 'npy', nombre_archivo)
        if not os.path.exists(ruta_archivo):
            ruta_archivo = os.path.join('output', nombre_archivo)
        print(f"Cargando {ruta_archivo}...")
        matriz_limpia = np.load(ruta_archivo)
        
        perimetro = extraer_perimetro(matriz_limpia)
        
        D, log_x, log_y, sizes, counts = calcular_box_counting(perimetro)
        print(f"\n--- RESULTADOS ---")
        print(f"Dimensión Fractal (D) calculada: {D:.4f}")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        ax1.imshow(perimetro, cmap='binary', origin='lower')
        ax1.set_title("Perímetro del Incendio")
        
        ax2.plot(log_x, log_y, 'ro-', label='Puntos (Cajas vs Tamaño)')
        tendencia_y = D * log_x + (log_y[0] - D * log_x[0]) 
        ax2.plot(log_x, tendencia_y, 'b--', label=f'Ajuste Lineal (Pendiente D={D:.4f})')
        
        ax2.set_title("Gráfico Log-Log (Box-Counting)")
        ax2.set_xlabel("[Tamaño Inverso de Caja]")
        ax2.set_ylabel("[Cantidad de Cajas]")
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        os.makedirs('output', exist_ok=True)
        ruta_salida = os.path.join('output', f'reporte_fractal_{fecha_elegida}.png')
        plt.savefig(ruta_salida, dpi=300)
        print(f"Gráfico guardado como '{ruta_salida}'")
        plt.show()

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {nombre_archivo}. Asegurate de correr el script anterior primero.")
