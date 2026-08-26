import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_erosion

def extraer_perimetro(matriz_binaria):
    """
    Extrae el borde del incendio. La dimensión fractal del fuego se mide 
    sobre su perímetro rugoso, no sobre el área sólida.
    """
    matriz_erosionada = binary_erosion(matriz_binaria)
    perimetro = matriz_binaria.astype(int) - matriz_erosionada.astype(int)
    return perimetro

def calcular_box_counting(matriz_perimetro):
    """
    Aplica el algoritmo de Box-Counting de alta velocidad (Vectorizado 100% NumPy).
    Retorna la dimensión fractal (D), los tamaños de caja y los conteos.
    """
    n = min(matriz_perimetro.shape)
    
    tamanos_caja = []
    conteos_cajas = []
    
    tamano = n
    while tamano >= 1:
        if tamano == n:
            contador = 1 if np.any(matriz_perimetro) else 0
        elif tamano == 1:
            contador = np.count_nonzero(matriz_perimetro)
        else:
            # Reshape matricial en bloques 2D sin bucles Python (Ultra rápido en C)
            bloques = matriz_perimetro.reshape(n // tamano, tamano, n // tamano, tamano).any(axis=(1, 3))
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

if __name__ == "__main__":
    fecha_elegida = input("Escribí la fecha a procesar (ejemplo: 2022-02-18): ").strip()
    nombre_archivo = f'matriz_objetivo_limpia_{fecha_elegida}.npy'
    
    try:
        print(f"Cargando {nombre_archivo}...")
        matriz_limpia = np.load('output/' + nombre_archivo)
        
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
        
        ax2.set_title("Gráfico Log-Log (Box-Counting Vectorizado)")
        ax2.set_xlabel("[Tamaño Inverso de Caja]")
        ax2.set_ylabel("[Cantidad de Cajas]")
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        plt.savefig(f'reporte_fractal_{fecha_elegida}.png', dpi=300)
        print(f"Gráfico guardado como 'reporte_fractal_{fecha_elegida}.png'")
        plt.show()

    except FileNotFoundError:
        print(f"No se encontró el archivo 'output/{nombre_archivo}'. Procesá primero la fecha con ver_mapa_filtrado.py")
