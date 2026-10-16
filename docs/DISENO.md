# Decisiones de interfaz

Pantalla única orientada a convertir documentos. Acción principal: Convertir a Markdown. La lista y la vista previa comparten la ventana; el divisor permite cambiar su proporción. El destino y los controles del lote permanecen visibles.

Sin una identidad ni referencias visuales aportadas, se adopta una interfaz de productividad sobria: fondo claro, paneles blancos, texto azul oscuro, acento verde petróleo, Segoe UI, espaciado de 4/8 px y bordes discretos. Tamaño mínimo 900 × 680; ventana inicial 1180 × 800. No se fuerza un diseño móvil en una aplicación de escritorio.

Estados verificables: vacío, documentos pendientes, conversión activa, resultado, error, cancelación y salida no disponible. Los estados usan texto, además de color. Controles nativos con foco de teclado y nombres accesibles; Ctrl+O abre selección múltiple. Los nombres de archivos y los mensajes se muestran como texto plano.

Vista previa con QTextBrowser, sin JavaScript, sin navegación automática y con carga de recursos desactivada. Fuente Markdown de solo lectura. No se interpreta contenido de documentos como instrucciones para la aplicación.
