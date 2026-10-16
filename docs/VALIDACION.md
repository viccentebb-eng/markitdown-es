# Validación

La prueba automatizada de conversión abre muestras reales y sintéticas en TXT, HTML, CSV, DOCX, XLSX, PPTX y PDF y comprueba contenido extraído, no solo que no se produzca una excepción. También verifica conservación de originales, colisiones de nombres, UTF-8, límites de tamaño y documentos vacíos.

Las pruebas Qt comprueban selección múltiple, duplicados, eventos de arrastrar y soltar, rechazo de URLs, procesamiento tras un error, vista previa, portapapeles, reintentos, detención entre archivos, selector de salida, quitar y limpiar. La vista previa bloquea recursos locales y remotos.

La prueba del ejecutable abre la interfaz Qt, convierte los siete documentos con el motor empaquetado, verifica texto y genera `smoke.json` e `interfaz.png`. Se ejecuta en el mismo flujo que construye el ZIP. Esto comprueba los conversores y recursos incluidos en la distribución.

Límites de esta validación: no equivale a una auditoría de accesibilidad con lector de pantalla, ni a una prueba en todas las instalaciones de Windows. XLS y EPUB están habilitados por sus conversores, pero no forman parte de las siete muestras de regresión. No se garantiza extracción fiel de documentos complejos, dañados, protegidos ni escaneados.

Validación local del 16 de octubre de 2026: 18 pruebas aprobadas en Windows con Python 3.13, revisión Ruff aprobada y auditoría sin vulnerabilidades conocidas. Una mutación deliberada del límite de tamaño fue detectada por la prueba y se restauró antes de publicar. Dos avisos de deprecación proceden de la construcción de eventos de arrastre en las pruebas Qt.

La prueba integrada desde código convirtió los siete documentos y produjo una captura real de la ventana. El proceso de cada documento está separado del de la interfaz: se verifican también cierres nativos y tiempo máximo como errores recuperables.

El resultado de CI y la prueba del `.exe` se consultan en el flujo enlazado desde el repositorio; no deben inferirse de las pruebas locales.
