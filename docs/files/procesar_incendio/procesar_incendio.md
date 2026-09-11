# Documentación: `procesar_incendio.py`

## 1. Propósito General del Módulo
`procesar_incendio.py` es un script de exploración y análisis inicial de datos satelitales brutos. Su objetivo principal es inspeccionar el archivo de registro histórico provisto por el sensor VIIRS (Visible Infrared Imaging Radiometer Suite) a bordo del satélite Suomi NPP de la NASA, identificar las variables disponibles, contabilizar los focos de calor y detectar automáticamente el día con mayor actividad ígnea (día pico) para aislarlo en un archivo CSV independiente de acceso rápido.

---

## 2. Rol en la Arquitectura del Sistema
Este módulo actúa como una herramienta exploratoria preliminar (data exploration) dentro del ciclo de vida del proyecto:
- Permite verificar la integridad estructural del dataset satelital (`.json`).
- Diagnostica si la información viene estructurada como un GeoJSON estándar (con colección de `features` y `properties`) o como un arreglo de objetos tabular plano.
- Provee un mecanismo automático para extraer el subconjunto de datos correspondiente al evento más crítico de la temporada para análisis rápidos o calibraciones puntuales sin necesidad de reprocesar el archivo histórico masivo completo.

---

## 3. Entradas y Salidas
### Entradas:
- **Archivo de datos satelitales:** `./DL_FIRE_SV-C2_788988/fire_archive_SV-C2_788988.json` (Archivo provisto por NASA FIRMS con registros de anomalías térmicas y puntos de calor).

### Salidas:
- **Salida en consola:** Conteo total de registros, listado de columnas disponibles, histograma tabular de incendios por fecha (`acq_date`) y reporte del día pico de incendios.
- **Archivo CSV exportado:** `output/incendios_dia_pico.csv` (contiene únicamente las detecciones térmicas correspondientes a la fecha con mayor número de focos).

---

## 4. Dependencias y Librerías
- **Librerías estándar:** `json`.
- **Librerías de análisis de datos:** `pandas`.

---

## 5. Lógica y Flujo de Ejecución Detallado
1. **Carga y parseo JSON:** Abre el archivo JSON de FIRMS y determina la estructura subyacente. Si detecta la clave `'features'`, desanida los diccionarios de propiedades (`properties`) convirtiéndolos en un `pandas.DataFrame`. Caso contrario, interpreta el JSON como una tabla plana directa.
2. **Diagnóstico general:** Imprime la cantidad total de puntos de calor registrados y la lista de columnas (tales como `latitude`, `longitude`, `brightness`, `scan`, `track`, `acq_date`, `acq_time`, `confidence`, `frp`, etc.).
3. **Análisis de distribución temporal:** Aplica `df['acq_date'].value_counts().sort_index()` para generar la serie histórica de frecuencia diaria de incendios.
4. **Detección del día pico:** Mediante `distribucion_fechas.idxmax()`, identifica la fecha con el mayor número absoluto de detecciones térmicas.
5. **Filtrado y persistencia:** Filtra el DataFrame original preservando únicamente los registros del día pico y los exporta a `output/incendios_dia_pico.csv` sin índice.
6. **Manejo de excepciones:** Captura `FileNotFoundError` en caso de que el archivo masivo de la NASA aún no haya sido descargado o ubicado en la ruta esperada.

