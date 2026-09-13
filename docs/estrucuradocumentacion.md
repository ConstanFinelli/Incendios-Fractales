# Protocolo y Estándar de Documentación del Proyecto (`estrucuradocumentacion.md`)

Este documento establece la **guía obligatoria de documentación modular** para desarrolladores y agentes de inteligencia artificial que trabajen en este repositorio. 

Se basa estrictamente en la convención ya implementada en la carpeta [`docs/files/`](files/) para los módulos del sistema.

---

## 1. Regla de Organización de Archivos

Por cada archivo de código fuente Python (`<nombre_modulo>.py`) presente en el proyecto, **DEBE existir obligatoriamente una carpeta homónima dentro de `docs/files/`**, la cual contendrá exactamente **dos archivos Markdown**:

```
Incendios-Fractales/
├── <nombre_modulo>.py
└── docs/
    └── files/
        └── <nombre_modulo>/
            ├── <nombre_modulo>.md     <-- Documento 1: Propósito, Justificación y Arquitectura
            └── functions.md          <-- Documento 2: Catálogo de Funciones y Referencias Cruzadas
```

### Módulos ya documentados bajo esta norma (referencias de ejemplo):
- [`docs/files/algoritmo_genetico/`](files/algoritmo_genetico/) (`algoritmo_genetico.md` y `functions.md`)
- [`docs/files/automata_celular/`](files/automata_celular/) (`automata_celular.md` y `functions.md`)
- [`docs/files/calcular_dimension_fractal/`](files/calcular_dimension_fractal/) (`calcular_dimension_fractal.md` y `functions.md`)
- [`docs/files/capa_biomasa/`](files/capa_biomasa/) (`capa_biomasa.md` y `functions.md`)
- [`docs/files/ver_mapa_filtrado/`](files/ver_mapa_filtrado/) (`ver_mapa_filtrado.md` y `functions.md`)
- [`docs/files/simulador_predictivo/`](files/simulador_predictivo/) (`simulador_predictivo.md` y `functions.md`)
- [`docs/files/validacion_walk_forward/`](files/validacion_walk_forward/) (`validacion_walk_forward.md` y `functions.md`)
- [`docs/files/main/`](files/main/) (`main.md` y `functions.md`)

---

## 2. Documento 1: `<nombre_modulo>.md` (Propósito, Justificación y Arquitectura)

Este archivo responde a: **¿Qué hace el archivo?**, **¿Por qué existe?** y **¿Cuál es su rol en el sistema?**.

### Estructura Obligatoria y Secciones:

1. **Título Principal:** `# Documentación: <nombre_modulo>.py`
2. **`## 1. Propósito General del Módulo`**
   - Descripción conceptual y funcional de lo que implementa el archivo.
3. **`## 2. Justificación de su Existencia`**
   - **Problema puntual que resuelve:** Qué necesidad técnica, biofísica o algorítmica atiende.
   - **Motivo de separación:** Por qué constituye un archivo `.py` independiente y no fue colocado dentro de otro módulo.
   - **Ventajas de diseño:** Beneficios de modularidad, testeabilidad aislada, paralelización o mantenimiento.
4. **`## 3. Rol en la Arquitectura del Sistema`**
   - Fase del pipeline en la que interviene (Fase 1: Preprocesamiento, Fase 2: Inversión AG, Fase 3: Predicción, Fase 4: Validación).
   - Diagrama esquemático en ASCII o Mermaid ilustrando el flujo de datos.
5. **`## 4. Entradas y Salidas`**
   - **Entradas:** Parámetros por consola/función, archivos consumidos (`.json`, `.npy`, `.csv`).
   - **Salidas:** Objetos retornados y artefactos generados en `output/` (`.png`, `.csv`, `.npy`).
6. **`## 5. Dependencias y Librerías`**
   - Librerías estándar (`os`, `sys`, `csv`, `random`), científicas (`numpy`, `scipy`, `matplotlib`, `pandas`) y módulos internos importados.
7. **`## 6. Fundamentos Matemáticos / Físicos`** *(si aplica)*
   - Ecuaciones, probabilidades anisotrópicas, métricas de error o fórmulas utilizadas.

---

## 3. Documento 2: `functions.md` (Catálogo de Funciones y Referencias Cruzadas)

Este archivo responde a: **¿Qué funciones implementa?** y **¿Qué funciones externas invoca y dónde están documentadas?**.

### Estructura Obligatoria y Secciones:

### `## 1. Funciones Definidas en este Archivo`
Por **cada una** de las funciones y métodos implementados en `<nombre_modulo>.py`:
* **Ancla HTML y Encabezado:** `<a id="nombre_funcion"></a>` seguido de `### nombre_funcion(param1, param2=...)`
* **Firma:** `- **Firma:** def nombre_funcion(...)`
* **Descripción:** Explicación técnica de la lógica interna, manejo de matrices y casos límite.
* **Parámetros:** Lista en viñetas detallando:
  * `nombre_parametro` (*tipo*[, opcional]): Significado semántico, valores por defecto y rangos válidos.
* **Retorno:** `- **Retorno:** tipo` con la descripción de la estructura devuelta.

---

### `## 2. Funciones y Constantes Importadas de Otros Módulos`
Si el módulo realiza llamadas a funciones o utiliza constantes definidas en otros archivos `.py` del proyecto, **DEBE** incluir una tabla o lista de trazabilidad con la siguiente estructura:

| Función / Constante Invocada | Módulo de Origen | Archivo de Documentación | Motivo de la Invocación |
| :--- | :--- | :--- | :--- |
| `nombre_funcion_externa` | `<modulo_origen>.py` | [`<modulo_origen>.md`](../<modulo_origen>/<modulo_origen>.md) | Razón técnica y funcional por la cual se utiliza en este módulo. |

> [!IMPORTANT]
> **Enlace Markdown Relativo Obligatorio:** Siempre debe apuntar al archivo `<modulo_origen>.md` (o a su `functions.md#nombre_funcion` correspondiente) dentro de `docs/files/<modulo_origen>/`.

---

## 4. Guía Rápida para Agentes y Desarrolladores

Al programar un nuevo archivo Python o modificar uno existente:
1. **Nuevo archivo `.py`:** Crear inmediatamente `docs/files/<nombre>/<nombre>.md` y `docs/files/<nombre>/functions.md`.
2. **Nueva función o cambio de parámetros:** Actualizar el `functions.md` correspondiente.
3. **Nueva llamada entre módulos:** Agregar la fila correspondiente en la tabla de *Funciones Importadas* con su enlace relativo.
