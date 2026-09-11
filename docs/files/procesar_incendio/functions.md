# Funciones de `procesar_incendio.py`

## 1. Funciones Definidas en este Archivo

*Este archivo no define funciones explícitas mediante `def`.* 

Su arquitectura es puramente procedural y secuencial (scripting directo), concebida para ejecución interactiva o por lotes en una terminal. A continuación se desglosan los bloques lógicos de procesamiento que componen su flujo de ejecución:

<a id="bloque-1"></a>
### Bloque 1: Carga y Detección de Esquema JSON
- **Operación:** Lectura de archivo en disco y normalización estructural.
- **Detalle:** Lee el archivo `./DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json`. Evalúa si la clave `'features'` está presente para extraer la lista de atributos de cada punto geográfico, instanciando un `pandas.DataFrame`.

<a id="bloque-2"></a>
### Bloque 2: Diagnóstico y Auditoría de Datos
- **Operación:** Conteo e inspección de metadatos.
- **Detalle:** Imprime la dimensionalidad del dataset y los nombres de las columnas satelitales (coordenadas, potencia radiativa del fuego FRP, nivel de confianza, fecha y hora).

<a id="bloque-3"></a>
### Bloque 3: Agrupación Temporal y Detección de Máximos
- **Operación:** Frecuencia por fecha y selección de evento extremo.
- **Detalle:** Ejecuta `value_counts()` sobre el campo `acq_date` ordenado cronológicamente y localiza el índice máximo (`idxmax()`), que representa el día con mayor severidad del siniestro.

<a id="bloque-4"></a>
### Bloque 4: Filtrado y Exportación
- **Operación:** Serialización CSV.
- **Detalle:** Segmenta el DataFrame por la fecha pico y lo almacena en `output/incendios_dia_pico.csv` para acelerar análisis posteriores.

---

## 2. Funciones y Constantes Importadas de Otros Módulos del Proyecto

*Este archivo no importa funciones ni constantes de otros módulos del proyecto.* Es un script independiente y autosuficiente que únicamente depende de las librerías externas `json` y `pandas`.

