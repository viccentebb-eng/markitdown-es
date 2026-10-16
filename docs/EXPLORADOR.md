# Markdown como documento en Windows

## Doble clic: abrir con MarkItDown ES

Extrae toda la carpeta del ZIP y ejecuta **Instalar-MarkItDown.cmd**. El asistente copia la aplicación a `%LOCALAPPDATA%\Programs\MarkItDownES`, crea un acceso directo y registra el visor para archivos `.md` únicamente para tu usuario. No requiere permisos de administrador.

Si todavía no hay una aplicación asociada a `.md`, se propone MarkItDown ES. Si ya elegiste otra, Windows conserva tu elección: haz clic derecho en un `.md` > **Abrir con > Elegir otra aplicación > MarkItDown ES > Siempre**. No se cambia el valor protegido `UserChoice` ni se usan herramientas para forzarlo.

Con doble clic, la aplicación carga el documento directamente en el visor: encabezados, tablas, listas, imágenes locales, búsqueda y zoom. No vuelve a convertir el archivo.

## Vista previa dentro del Explorador

Se utiliza [Microsoft PowerToys](https://github.com/microsoft/PowerToys), que ya implementa el controlador de vista previa de Markdown. Es una herramienta externa opcional; no se incluye dentro de nuestro ejecutable.

1. Instala PowerToys desde su [página oficial](https://learn.microsoft.com/windows/powertoys/install) o con `winget install --id Microsoft.PowerToys --source winget --scope user`.
2. Abre PowerToys > **Complementos del Explorador de archivos** y activa **Markdown** en la sección Panel de vista previa.
3. En el Explorador de Windows activa **Ver > Mostrar > Panel de vista previa**, o pulsa **Alt+P**.
4. Selecciona un archivo `.md`: verás el documento en el panel lateral. Con doble clic se abre el visor de MarkItDown ES si lo elegiste como aplicación predeterminada.

La vista previa es un panel de lectura, no una miniatura de portada del archivo. No es necesario activar los controladores PDF, SVG ni otros módulos de PowerToys para usar Markdown. Consulta la [documentación oficial del panel](https://learn.microsoft.com/windows/powertoys/file-explorer).

## Biblioteca y búsquedas en nuestra aplicación

En **Mis documentos**, elige una carpeta. Puedes buscar por nombre, tipo, tamaño y fecha de modificación (hoy, últimos 7/30 días o un intervalo). Incluye subcarpetas y ordena pulsando las columnas. La búsqueda ignora diferencias entre mayúsculas y acentos.

**Contiene texto** busca dentro de `.md`, `.txt`, `.csv`, `.json`, `.xml` y `.html`; convierte antes los documentos de Office o PDF para buscar en su resultado Markdown. La búsqueda se ejecuta en segundo plano. El visor permite buscar con Ctrl+F, Enter, Anterior y Siguiente, tanto en el documento como en el código Markdown.

El visor admite texto UTF-8 de hasta 10 MB completo, sin el antiguo recorte de 200 000 caracteres. Las imágenes solo se cargan desde la carpeta del documento o sus subcarpetas (hasta 20 MB y 16 megapíxeles). Los enlaces externos no se abren automáticamente. Los resultados de búsqueda muestran hasta 5000 archivos; si alcanzas ese límite, afina los filtros.
