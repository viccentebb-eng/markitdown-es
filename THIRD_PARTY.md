# Componentes de terceros

Este proyecto usa bibliotecas sin modificar. No representa un producto oficial de Microsoft ni de The Qt Company.

| Componente | Proyecto y código fuente | Licencia declarada por el proyecto |
| --- | --- | --- |
| Microsoft MarkItDown | https://github.com/microsoft/markitdown | MIT |
| PySide6 / Shiboken6 | https://code.qt.io/cgit/pyside/pyside-setup.git/ | LGPLv3 / GPLv3 / comercial |
| Qt | https://code.qt.io/cgit/qt/ | LGPLv3 / GPLv3 / comercial, según módulo |
| PyInstaller | https://github.com/pyinstaller/pyinstaller | GPL con excepción para aplicaciones empaquetadas |

Se utilizan QtCore, QtGui y QtWidgets mediante bibliotecas dinámicas. La distribución en carpeta conserva DLL y bindings separados y reemplazables; no se impone ninguna restricción adicional a su modificación ni a la ingeniería inversa necesaria para depurar cambios en esas bibliotecas. Las versiones concretas de todas las dependencias están en `requirements.lock`.

El empaquetado incluye los directorios de metadatos y licencias disponibles de las distribuciones instaladas en `_internal/third_party_licenses`, además de los avisos integrados que recopila PyInstaller. Revisa esos textos para los componentes transitivos, como pandas, NumPy, ONNX Runtime, pdfminer, pdfplumber, Pillow, lxml y los conversores de Office. Los enlaces anteriores permiten obtener el código fuente correspondiente; la versión de Qt/PySide6 usada es 6.12.0.
