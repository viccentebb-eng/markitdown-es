"""Visor Markdown local, búsqueda en documento y lectura sin reconversión."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImageReader, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

MAX_VIEW_BYTES = 10 * 1024 * 1024


class SafePreview(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.root = None
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setAcceptDrops(False)
        self.setAccessibleName("Documento Markdown")
        self.document().setDefaultStyleSheet(
            "h1, h2, h3 { color: #16394b; } pre { background: #f2f5f7; } th, td { padding: 6px; }"
        )
        self.anchorClicked.connect(self.follow_anchor)

    def follow_anchor(self, url):
        if not url.scheme() and not url.path() and url.fragment():
            self.scrollToAnchor(url.fragment())

    def loadResource(self, resource_type, name):
        if not self.root or resource_type != QTextDocument.ResourceType.ImageResource:
            return None
        if name.scheme() not in {"", "file"} or name.host():
            return None
        path = Path(name.toLocalFile()) if name.isLocalFile() else self.root / name.path()
        try:
            path = path.resolve(strict=True)
            if not path.is_relative_to(self.root) or path.stat().st_size > 20 * 1024 * 1024:
                return None
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}:
                return None
            reader = QImageReader(str(path))
            size = reader.size()
            if size.width() <= 0 or size.height() <= 0 or size.width() * size.height() > 16_000_000:
                return None
            return reader.read()
        except OSError:
            return None


class DocumentViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.path = None
        self.text = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        tools = QHBoxLayout()
        self.title = QLabel("Selecciona un archivo convertido o abre un Markdown")
        self.title.setWordWrap(True)
        tools.addWidget(self.title, 1)
        self.copy = QPushButton("Copiar")
        self.copy.clicked.connect(lambda: QApplication.clipboard().setText(self.text))
        self.copy.setEnabled(False)
        tools.addWidget(self.copy)
        for caption, amount in (("A−", -1), ("A+", 1)):
            control = QPushButton(caption)
            control.setAccessibleName("Reducir texto" if amount < 0 else "Ampliar texto")
            control.clicked.connect(lambda checked=False, step=amount: self.zoom(step))
            tools.addWidget(control)
        layout.addLayout(tools)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar dentro del documento · Enter para siguiente")
        self.search.setAccessibleName("Buscar dentro del documento")
        self.search.returnPressed.connect(self.find_next)
        search_row.addWidget(self.search, 1)
        for text, callback in (
            ("Anterior", lambda: self.find_next(True)),
            ("Siguiente", self.find_next),
        ):
            control = QPushButton(text)
            control.clicked.connect(callback)
            search_row.addWidget(control)
        self.match_status = QLabel("")
        search_row.addWidget(self.match_status)
        layout.addLayout(search_row)
        self.tabs = QTabWidget()
        self.preview = SafePreview()
        self.source = QPlainTextEdit()
        self.source.setReadOnly(True)
        self.source.setAcceptDrops(False)
        self.source.setAccessibleName("Código Markdown completo")
        self.tabs.addTab(self.preview, "Documento")
        self.tabs.addTab(self.source, "Markdown")
        layout.addWidget(self.tabs, 1)

    def zoom(self, amount):
        self.preview.zoomIn(amount)
        self.source.zoomIn(amount)

    def message(self, text):
        self.path = None
        self.text = ""
        self.copy.setEnabled(False)
        self.preview.root = None
        self.preview.setPlainText(text)
        self.source.clear()
        self.title.setText("Visor de documentos")

    def open_path(self, path: Path):
        try:
            path = path.resolve(strict=True)
            if path.stat().st_size > MAX_VIEW_BYTES:
                raise ValueError("El visor admite documentos de texto de hasta 10 MB.")
            if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".xml", ".html", ".htm"}:
                raise ValueError(
                    "Añade este documento a Conversión para leer su resultado Markdown."
                )
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError, ValueError) as error:
            self.message(
                str(error)
                if isinstance(error, ValueError)
                else "El archivo no se puede leer o no es texto UTF-8."
            )
            return False
        self.path, self.text = path, text
        self.preview.root = path.parent
        self.preview.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + "/"))
        if path.suffix.lower() == ".md":
            self.preview.setMarkdown(text)
        else:
            self.preview.setPlainText(text)
        self.source.setPlainText(text)
        self.title.setText(path.name)
        self.title.setToolTip(str(path))
        self.copy.setEnabled(True)
        self.match_status.clear()
        return True

    def find_next(self, backward=False):
        query = self.search.text()
        if not query:
            self.match_status.clear()
            return False
        editor = self.preview if self.tabs.currentIndex() == 0 else self.source
        flags = QTextDocument.FindFlag.FindBackward if backward else QTextDocument.FindFlag(0)
        found = editor.find(query, flags)
        if not found:
            editor.moveCursor(
                QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
            )
            found = editor.find(query, flags)
        self.match_status.setText("Coincidencia" if found else "Sin resultados")
        return found
