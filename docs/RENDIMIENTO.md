# Rendimiento del motor

La versión 1.0 iniciaba un proceso, importaba los conversores e inicializaba el modelo Magika por cada archivo. Se conserva el proceso separado para que un fallo nativo no cierre la interfaz, pero en 1.1 se reutiliza un único motor entre archivos y entre lotes. El motor se cierra tras 60 segundos inactivo y se reinicia cuando hace falta.

TXT y Markdown se copian como texto, con detección de codificación cuando no son UTF-8; no necesitan cargar el modelo. Abrir un Markdown en el visor tampoco lo convierte ni genera archivos adicionales.

La comparación utiliza la misma PC y siete muestras TXT, HTML, CSV, DOCX, XLSX, PPTX y PDF, con tres ejecuciones completas del ejecutable, incluyendo apertura de interfaz y comprobación del resultado. La mediana inicial de 1.0 fue **13,098 segundos** (14,308; 13,098; 12,406). La mediana de 1.1 fue **2,474 segundos** (2,628; 2,474; 2,310): aproximadamente **5,3 veces más rápido**, o un **81 % menos de tiempo** en este lote de archivos pequeños. La prueba de 1.1 también comprueba la búsqueda del visor y la biblioteca.

La mejora mide principalmente el coste de iniciar el motor repetidamente. No predice cuánto tardará un PDF grande o un documento complejo. Las pruebas de regresión comprueban que el PID del proceso se conserva entre documentos y que un proceso cerrado se recrea sin perder el resultado siguiente.
