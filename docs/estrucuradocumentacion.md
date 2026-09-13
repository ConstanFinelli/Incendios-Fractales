# Protocolo y Estructura Estándar de Documentación del Proyecto (`estrucuradocumentacion.md`)

Este documento define la **norma obligatoria y estándar de documentación** para todos los desarrolladores y agentes de inteligencia artificial que colaboren en el proyecto. 

Su propósito es garantizar una trazabilidad arquitectónica completa, modular, navegable y coherente entre el código fuente en Python y los documentos explicativos.

---

## 1. Regla Fundamental de Organización de Archivos

Por cada archivo fuente Python (`<nombre_modulo>.py`) presente en la raíz del proyecto, **DEBE** existir una carpeta homónima dentro del directorio `docs/files/`:

```
Incendios-Fractales/
├── <nombre_modulo>.py
└── docs/
    └── files/
        └── <nombre_modulo>/
            ├── <nombre_modulo>.md     <-- Documento 1: Descripción y Justificación
            └── functions.md          <-- Documento 2: Catálogo de Funciones y Referencias
```

---

## 2. Documento 1: `<nombre_modulo>.md` (Descripción y Justificación)

Este archivo responde a las preguntas: **¿Qué hace este archivo?**, **¿Por qué existe?** y **¿Cómo interactúa con el resto del sistema?**.

### Estructura Obligatoria:

1. **Título del Módulo:** `# Documentación: <nombre_modulo>.py`
2. **Propósito General:** Explicación conceptual y técnica de la responsabilidad del archivo.
3. **Justificación de su Existencia:**
   * ¿Qué problema puntual resuelve?
   * ¿Por qué existe como un archivo independiente en lugar de estar integrado en otro módulo?
   * ¿Qué ventajas de modularidad, mantenimiento o separación de responsabilidades aporta?
4. **Rol en la Arquitectura del Sistema:**
   * En qué fase del pipeline interviene (Fase 1: Preprocesamiento Satelital, Fase 2: Optimización Inversa AG, Fase 3: Predicción Prospectiva, Fase 4: Validación Científica).
   * Diagrama esquemático (ASCII o Mermaid) del flujo de datos.
5. **Entradas y Salidas:**
   * **Entradas:** Parámetros de entrada, tipos de datos, archivos leídos (`.json`, `.csv`, `.npy`, etc.).
   * **Salidas:** Estructuras retornadas, artefactos persistidos en disco (`output/*.png`, `output/*.csv`, matrices `.npy`).
6. **Dependencias y Librerías:** Librerías estándar, científicas (`numpy`, `scipy`, `matplotlib`, `pandas`) y módulos locales importados.

---

## 3. Documento 2: `functions.md` (Catálogo de Funciones y Referencias Cruzadas)

Este archivo responde a las preguntas: **¿Qué funciones define este archivo?** y **¿Qué funciones externas invoca y dónde están documentadas?**.

### Estructura Obligatoria:

### Sección 1: Funciones Definidas en este Archivo
Para **cada una** de las funciones y métodos implementados en `<nombre_modulo>.py`:
* **Nombre y Firma:** `### nombre_funcion(param1, param2, ...)`
* **Motivo y Descripción:** Explicación detallada de la lógica algorítmica, consideraciones matemáticas/físicas y decisiones de diseño.
* **Parámetros:** Lista detallada indicando:
  * `nombre_parametro` (*tipo*): Significado semántico, valores por defecto y rangos admisibles.
* **Retorno:** Tipo de dato retornado (`float`, `np.ndarray`, `tuple`, `None`, etc.) y descripción de su contenido.

### Sección 2: Funciones Invocadas desde Otros Módulos (Trazabilidad Cruzada)
Si el módulo realiza llamadas a funciones definidas en otros archivos `.py` del proyecto, **DEBE** incluir una tabla o lista de trazabilidad que indique:
* **Función Invocada:** Nombre de la función llamada.
* **Módulo de Origen:** Archivo `.py` donde reside la función.
* **Enlace a la Documentación:** Enlace relativo markdown al `<modulo_origen>.md` (o `functions.md` del módulo) donde está definida y explicada formalmente.
* **Motivo de la Invocación:** Por qué se requiere esa función externa en este flujo.

---

## 4. Plantillas de Referencia para Agentes

### Plantilla para `<nombre_modulo>.md`:
```markdown
# Documentación: `<nombre_modulo>.py`

## 1. Propósito General del Módulo
[Descripción técnica y conceptual del módulo]

## 2. Justificación de su Existencia
- **Problema que resuelve:** [Problema específico]
- **Motivo de separación:** [Por qué es un módulo independiente]
- **Ventajas de diseño:** [Modularidad, testeabilidad, paralelismo, etc.]

## 3. Rol en la Arquitectura del Sistema
[Explicación del rol y diagrama de flujo]

## 4. Entradas y Salidas
- **Entradas:** [Formatos y tipos]
- **Salidas:** [Objetos y archivos generados]

## 5. Dependencias
- [Librerías externas y módulos internos]
```

### Plantilla para `functions.md`:
```markdown
# Funciones de `<nombre_modulo>.py`

## 1. Funciones Definidas en este Archivo

### `nombre_funcion(param1, param2=default)`
- **Firma:** `def nombre_funcion(param1, param2=default):`
- **Descripción:** [Explicación detallada]
- **Parámetros:**
  - `param1` (*tipo*): [Descripción]
  - `param2` (*tipo*, opcional): [Descripción]
- **Retorno:** `tipo` - [Descripción del retorno]

---

## 2. Funciones Invocadas desde Otros Módulos

| Función Invocada | Módulo de Origen | Archivo de Documentación | Motivo de la Invocación |
| :--- | :--- | :--- | :--- |
| `otra_funcion` | `otro_modulo.py` | [`otro_modulo.md`](../otro_modulo/otro_modulo.md) | [Razón del uso] |
```

---

## 5. Regla de Sincronización para Modificaciones de Código

Siempre que un desarrollador o agente:
1. **Cree un nuevo archivo `.py`:** Debe crear inmediatamente su carpeta `docs/files/<nuevo_modulo>/` con sus dos archivos `.md`.
2. **Modifique una función existente o agregue una nueva:** Debe actualizar inmediatamente el `functions.md` correspondiente.
3. **Agregue una dependencia o llamada a otro módulo:** Debe registrar la referencia cruzada con el enlace al `.md` del módulo importado.
