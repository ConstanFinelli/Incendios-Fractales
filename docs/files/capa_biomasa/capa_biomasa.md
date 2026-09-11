# Módulo: `capa_biomasa.py`

## 1. Propósito y Responsabilidad del Módulo
El módulo `capa_biomasa.py` implementa la **heterogeneidad espacial biofísica** del terreno en la provincia de Corrientes (Tarea T2.1). Modela la variación en la carga de combustible y resistencia al avance del fuego según el tipo de cobertura del suelo, superando la limitación de modelar un combustible escalar homogéneo en toda la provincia.

## 2. Fuentes de Datos Geoespaciales Oficiales
El módulo consume directamente capas vectoriales oficiales del **Instituto Geográfico Nacional (IGN)** de la República Argentina a través de sus geoservicios WFS (`EPSG:4326`):
1. **`ign:areas_de_aguas_continentales_perenne`:** Lagunas, ríos principales y esteros profundos del macrosistema del Iberá.
2. **`ign:vegetacion_hidrofila_ED020`:** Bañados, pajonales, juncales y esteros con vegetación semi-sumergida.
3. **`ign:vegetacion_arborea_060301`:** Plantaciones forestales comerciales de especies resinosas (*Pinus elliottii*, *Pinus taeda*, *Eucalyptus grandis*).
4. **`data/mascara_corrientes_256.npy`:** Delimitación poligonal provincial para definir la condición de contorno.

## 3. Clasificación Biofísica de Combustible (4 Categorías)
La grilla de $256 \times 256$ se discretiza en cuatro categorías biofísicas de combustible ($C \in [0.0, 1.0]$):

| Categoría | Nombre de Cobertura | Coeficiente $C$ | Inflamabilidad y Comportamiento Físico | Proporción en Corrientes |
| :---: | :--- | :---: | :--- | :---: |
| **1** | **Cuerpos de Agua y Esteros Profundos** | $0.0$ | **Incombustible:** Barrera cortafuego natural absoluta. $P_{\text{ignición}} = 0$. | $\sim 1.2\%$ ($439$ celdas) |
| **2** | **Bañados y Vegetación Hidrófila** | $0.2$ | **Muy Baja:** Alta saturación hídrica. Requiere calor extremo para desecar el junco. | $\sim 4.1\%$ ($1,441$ celdas) |
| **3** | **Pastizales, Sabanas y Malezas** | $0.6$ | **Propagación Base:** Matriz biofísica dominante del pastizal correntino. | $\sim 91.8\%$ ($32,478$ celdas) |
| **4** | **Plantaciones Forestales Resinosas** | $1.0$ | **Máxima Inflamabilidad:** Alta carga de biomasa combustible y aceleración de copa. | $\sim 2.9\%$ ($1,024$ celdas) |
| **0** | **Límites Exteriores / Ríos Paraná y Uruguay** | $0.0$ | **Incombustible:** Condición de contorno Dirichlet para evitar desbordes. | Exterior |

## 4. Formulación Matemática en el Autómata Celular
En la función de transición estocástica de `automata_celular.py`:
$$\text{Combustible}_{\text{local}}(y, x) = M_{\text{comb}}(y, x) \times c_{\text{global}}$$
$$P_{\text{ignicion}}(y, x) = \min\left(0.95, \, \text{Combustible}_{\text{local}}(y, x) \cdot (1 - h/100) \cdot e^{0.05 \cdot v \cdot \cos(\Delta\theta)}\right)$$

- Si $M_{\text{comb}}(y, x) = 0.0$ (agua), la probabilidad de ignición es $0.0$, impidiendo que el fuego cruce lagunas o ríos.
- Si $M_{\text{comb}}(y, x) = 1.0$ (forestación), el frente avanza a la velocidad máxima permitida por el viento.

## 5. Salidas Generadas
- **`data/mapa_combustible_256.npy`:** Matriz float `(256, 256)` con coeficientes $C \in [0.0, 1.0]$.
- **`data/categorias_cobertura_256.npy`:** Matriz int `(256, 256)` con las etiquetas $\{0, 1, 2, 3, 4\}$.
- **`output/mapa_cobertura_combustible.png`:** Mapa cartográfico GIS a 300 DPI con división departamental y leyenda estadística.
