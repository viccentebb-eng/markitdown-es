"""Biblioteca de documentos con filtros y búsqueda de texto fuera del hilo de interfaz."""

import os
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .conversion import EXTENSIONS, MAX_INPUT_BYTES

TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".xml", ".html", ".htm"}
TYPES = {
    "Todos": EXTENSIONS,
    "Markdown": {".md"},
    "PDF": {".pdf"},
    "Word": {".docx"},
    "Excel": {".xlsx", ".xls"},
    "PowerPoint": {".pptx"},
    "Texto": TEXT_EXTENSIONS,
}


def normalized(value):
    return "".join(
        c for c in unicodedata.normalize("NFD", value.casefold()) if not unicodedata.combining(c)
    )


@dataclass(frozen=True)
class SearchQuery:
    root: Path
    name: str = ""
    content: str = ""
    kind: str = "Todos"
    since: date | None = None
    until: date | None = None
    size: int = 0
    recursive: bool = True


def contains_text(path, query, interrupted):
    needle = normalized(query)
    carry = ""
    with path.open(encoding="utf-8-sig", errors="replace") as stream:
        while chunk := stream.read(65536):
            if interrupted():
                return False
            text = carry + normalized(chunk)
            if needle in text:
                return True
            carry = text[-len(needle) :]
    return False


def search_files(query: SearchQuery, interrupted=lambda: False):
    if not query.root.is_dir():
        return
    for directory, folders, files in os.walk(query.root, followlinks=False):
        folders[:] = [name for name in folders if not (Path(directory) / name).is_symlink()]
        for name in files:
            if interrupted():
                return
            path = Path(directory) / name
            try:
                if path.is_symlink() or path.suffix.lower() not in TYPES[query.kind]:
                    continue
                if normalized(query.name) not in normalized(name):
                    continue
                info = path.stat()
                modified = datetime.fromtimestamp(info.st_mtime)
                if query.since and modified.date() < query.since:
                    continue
                if query.until and modified.date() > query.until:
                    continue
                if query.size == 1 and info.st_size >= 1024 * 1024:
                    continue
                if query.size == 2 and not 1024 * 1024 <= info.st_size <= 10 * 1024 * 1024:
                    continue
                if query.size == 3 and info.st_size <= 10 * 1024 * 1024:
                    continue
                if query.content and (
                    path.suffix.lower() not in TEXT_EXTENSIONS
                    or info.st_size > MAX_INPUT_BYTES
                    or not contains_text(path, query.content, interrupted)
                ):
                    continue
                yield path, modified, info.st_size
            except OSError:
                continue
        if not query.recursive:
            return


class SearchWorker(QThread):
    found = Signal(object)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        for index, item in enumerate(search_files(self.query, self.isInterruptionRequested)):
            if index >= 5000:
                break
            self.found.emit(item)


class FileRow(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        return self.data(column, Qt.ItemDataRole.UserRole) < other.data(
            column, Qt.ItemDataRole.UserRole
        )


class FileLibrary(QWidget):
    selected = Signal(object)
    convert_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.worker = None
        self.refresh_pending = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        filters = QGridLayout()
        self.folder = QLineEdit()
        self.folder.setPlaceholderText("Carpeta de documentos")
        self.folder.setAccessibleName("Carpeta donde buscar archivos")
        choose = QPushButton("Carpeta…")
        choose.clicked.connect(self.choose_folder)
        filters.addWidget(self.folder, 0, 0, 1, 2)
        filters.addWidget(choose, 0, 2)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Buscar nombre de archivo…")
        self.name.setAccessibleName("Buscar por nombre")
        filters.addWidget(self.name, 1, 0, 1, 3)
        self.content = QLineEdit()
        self.content.setPlaceholderText("Contiene texto · Markdown y archivos de texto…")
        self.content.setAccessibleName("Buscar dentro de los archivos de texto")
        filters.addWidget(self.content, 2, 0, 1, 3)
        self.kind = QComboBox()
        self.kind.addItems(list(TYPES))
        self.kind.setAccessibleName("Filtrar por tipo")
        self.size = QComboBox()
        self.size.addItems(["Cualquier tamaño", "Menos de 1 MB", "De 1 a 10 MB", "Más de 10 MB"])
        self.size.setAccessibleName("Filtrar por tamaño")
        filters.addWidget(self.kind, 3, 0)
        filters.addWidget(self.size, 3, 1, 1, 2)
        self.dates = QComboBox()
        self.dates.addItems(
            ["Cualquier fecha", "Hoy", "Últimos 7 días", "Últimos 30 días", "Intervalo"]
        )
        self.dates.setAccessibleName("Fecha de modificación")
        self.since = QDateEdit(QDate.currentDate().addDays(-7))
        self.until = QDateEdit(QDate.currentDate())
        for edit, name in ((self.since, "Desde"), (self.until, "Hasta")):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd/MM/yyyy")
            edit.setAccessibleName(name)
        filters.addWidget(self.dates, 4, 0)
        filters.addWidget(self.since, 4, 1)
        filters.addWidget(self.until, 4, 2)
        self.recursive = QCheckBox("Incluir subcarpetas")
        self.recursive.setChecked(True)
        filters.addWidget(self.recursive, 5, 0, 1, 2)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        filters.addWidget(refresh, 5, 2)
        layout.addLayout(filters)
        self.results = QTreeWidget()
        self.results.setHeaderLabels(["ARCHIVO", "MODIFICACIÓN", "TIPO", "TAMAÑO"])
        self.results.setRootIsDecorated(False)
        self.results.setSortingEnabled(True)
        self.results.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.results.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):
            self.results.header().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.results.setAccessibleName("Resultados de archivos; ordena pulsando las columnas")
        self.results.currentItemChanged.connect(self.open_selected)
        layout.addWidget(self.results, 1)
        convert = QPushButton("Añadir seleccionado a conversión")
        convert.clicked.connect(self.request_conversion)
        layout.addWidget(convert)
        self.status = QLabel(
            "Elige una carpeta. La búsqueda de contenido examina Markdown y texto."
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.refresh)
        for control in (self.folder, self.name, self.content):
            control.textChanged.connect(self.schedule)
        for control in (self.kind, self.size, self.dates):
            control.currentIndexChanged.connect(self.schedule)
        for control in (self.since, self.until):
            control.dateChanged.connect(self.schedule)
        self.recursive.toggled.connect(self.schedule)
        self.schedule()

    def schedule(self, *_):
        custom = self.dates.currentIndex() == 4
        self.since.setEnabled(custom)
        self.until.setEnabled(custom)
        self.timer.start()

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Explorar documentos", self.folder.text())
        if path:
            self.folder.setText(path)

    def query(self):
        period = self.dates.currentIndex()
        since = until = None
        if period == 4:
            since, until = self.since.date().toPython(), self.until.date().toPython()
        elif period:
            until = date.today()
            since = QDate.currentDate().addDays({1: 0, 2: -6, 3: -29}[period]).toPython()
        return SearchQuery(
            Path(self.folder.text()),
            self.name.text(),
            self.content.text(),
            self.kind.currentText(),
            since,
            until,
            self.size.currentIndex(),
            self.recursive.isChecked(),
        )

    def refresh(self):
        self.timer.stop()
        if self.worker:
            self.refresh_pending = True
            self.worker.requestInterruption()
            return
        if not self.folder.text().strip():
            return
        query = self.query()
        self.results.clear()
        if not query.root.is_dir() or (query.since and query.until and query.since > query.until):
            self.status.setText("Elige una carpeta válida y un intervalo de fechas correcto.")
            return
        self.status.setText("Buscando… puedes seguir utilizando el visor.")
        self.worker = SearchWorker(query, self)
        self.worker.found.connect(self.add_result)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def add_result(self, result):
        if self.refresh_pending:
            return
        path, modified, size = result
        values = [
            path.name,
            modified.strftime("%d/%m/%Y %H:%M"),
            path.suffix.upper().lstrip("."),
            f"{size / 1024:.1f} KB",
        ]
        row = FileRow(values)
        for column, value in enumerate(
            [normalized(path.name), modified.timestamp(), path.suffix, size]
        ):
            row.setData(column, Qt.ItemDataRole.UserRole, value)
        row.setData(0, Qt.ItemDataRole.UserRole + 1, str(path))
        row.setToolTip(0, str(path))
        self.results.addTopLevelItem(row)

    def search_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.status.setText(
            f"{self.results.topLevelItemCount()} archivo(s). Máximo 5000; afina los filtros si hay más."
        )
        if self.refresh_pending:
            self.refresh_pending = False
            self.refresh()

    def current_path(self):
        row = self.results.currentItem()
        return Path(row.data(0, Qt.ItemDataRole.UserRole + 1)) if row else None

    def open_selected(self, *_):
        if path := self.current_path():
            self.selected.emit(path)

    def request_conversion(self):
        if path := self.current_path():
            self.convert_requested.emit(path)

    def stop(self):
        self.timer.stop()
        self.refresh_pending = False
        if self.worker:
            self.worker.requestInterruption()
            return self.worker.wait(3000)
        return True
