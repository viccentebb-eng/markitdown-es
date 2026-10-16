import os
import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from .theme import STYLE
from .window import MainWindow


def create_app():
    app = QApplication.instance() or QApplication(sys.argv)
    # The offscreen Qt plugin on Windows does not discover system fonts.
    if sys.platform == "win32" and not QFontDatabase.families():
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
            QFontDatabase.addApplicationFont(str(fonts / name))
    app.setOrganizationName("MarkItDownES")
    app.setApplicationName("MarkItDown ES")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "app.png")))
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f2f5f7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#172b3a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#172b3a"))
    app.setPalette(palette)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLE)
    translator = QTranslator(app)
    translator.load("qtbase_es", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    app.installTranslator(translator)
    app.translator = translator
    return app


def main():
    app = create_app()
    window = MainWindow()
    for argument in sys.argv[1:]:
        if not argument.startswith("--"):
            window.open_document(Path(argument))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
