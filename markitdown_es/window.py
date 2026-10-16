from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .conversion import EXTENSIONS, friendly_error, validate_source
from .engine import ConversionSession
from .library import FileLibrary
from .viewer import DocumentViewer, SafePreview
from .worker import BatchWorker

__all__ = ["MainWindow", "SafePreview"]


@dataclass
class Job:
    source: Path
    row: QTreeWidgetItem
    destination: Path | None = None
    error: str = ""


def button(text, callback, name=""):
    control = QPushButton(text)
    control.setObjectName(name)
    control.clicked.connect(callback)
    return control


def label(text, name=""):
    control = QLabel(text)
    control.setObjectName(name)
    control.setWordWrap(True)
    control.setTextFormat(Qt.TextFormat.PlainText)
    return control


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings()
        self.jobs: list[Job] = []
        self.worker: BatchWorker | None = None
        self.session = ConversionSession()
        self.completed = 0
        self.total = 0
        self.setWindowTitle("MarkItDown ES · Convertir, explorar y leer")
        self.resize(1380, 920)
        self.setMinimumSize(1100, 780)
        self.setAcceptDrops(True)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 16)
        layout.setSpacing(20)

        header = QHBoxLayout()
        header.addWidget(label("M↓", "brand"))
        heading = QVBoxLayout()
        heading.addWidget(label("Documentos a Markdown", "title"))
        heading.addWidget(
            label("Tus archivos, listos para leer, compartir y usar con IA.", "subtitle")
        )
        header.addLayout(heading, 1)
        header.addWidget(label("Conversión local", "badge"))
        layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QFrame()
        left.setObjectName("panel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 16)
        left_layout.setSpacing(12)
        left_top = QHBoxLayout()
        self.count = label("Archivos · 0", "section")
        left_top.addWidget(self.count, 1)
        self.add_button = button("Añadir archivos", self.choose_files)
        left_top.addWidget(self.add_button)
        left_layout.addLayout(left_top)
        self.drop_button = button(
            "Arrastra tus documentos aquí\no haz clic para seleccionarlos",
            self.choose_files,
            "drop",
        )
        left_layout.addWidget(self.drop_button)
        left_layout.addWidget(
            label(
                "PDF · Word · Excel · PowerPoint · HTML · Texto\nHasta 100 MB por archivo", "muted"
            )
        )
        self.queue = QTreeWidget()
        self.queue.setHeaderLabels(["DOCUMENTO", "ESTADO"])
        self.queue.setRootIsDecorated(False)
        self.queue.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.queue.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.queue.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.queue.setAccessibleName("Cola de archivos. Selecciona uno para ver su resultado.")
        self.queue.currentItemChanged.connect(self.show_preview)
        left_layout.addWidget(self.queue, 1)
        actions = QHBoxLayout()
        self.remove_button = button("Quitar seleccionados", self.remove_selected)
        self.clear_button = button("Limpiar lista", self.clear_jobs)
        actions.addWidget(self.remove_button)
        actions.addWidget(self.clear_button)
        actions.addStretch()
        left_layout.addLayout(actions)
        self.navigation = QTabWidget()
        self.navigation.addTab(left, "Conversión")
        self.library = FileLibrary()
        self.library.selected.connect(self.open_document)
        self.library.convert_requested.connect(self.convert_from_library)
        self.navigation.addTab(self.library, "Mis documentos")
        splitter.addWidget(self.navigation)

        right = QFrame()
        right.setObjectName("panel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 16)
        right_layout.setSpacing(12)
        preview_top = QHBoxLayout()
        preview_top.addWidget(label("Visor de documentos", "section"), 1)
        preview_top.addWidget(button("Abrir Markdown…", self.choose_document))
        preview_top.addWidget(button("Explorador de Windows", self.windows_help))
        right_layout.addLayout(preview_top)
        self.viewer = DocumentViewer()
        self.preview, self.source = self.viewer.preview, self.viewer.source
        self.copy_button, self.preview_name = self.viewer.copy, self.viewer.title
        self.tabs = self.viewer.tabs
        right_layout.addWidget(self.viewer, 1)
        right_layout.addWidget(
            label(
                "Lee el documento, busca en su texto y explora tus resultados. Las imágenes locales se muestran; las remotas se bloquean.",
                "muted",
            )
        )
        splitter.addWidget(right)
        splitter.setSizes([560, 540])
        layout.addWidget(splitter, 1)

        output_panel = QFrame()
        self.output_panel = output_panel
        output_panel.setObjectName("panel")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(20, 16, 20, 16)
        output_layout.addWidget(label("Carpeta de salida", "section"))
        output_row = QHBoxLayout()
        documents = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        default = str(Path(documents or Path.home()) / "MarkItDown")
        self.output = QLineEdit(str(self.settings.value("output", default)))
        self.library.folder.setText(self.output.text())
        self.output.setAccessibleName("Carpeta donde se guardarán los archivos Markdown")
        output_row.addWidget(self.output, 1)
        self.browse_button = button("Elegir carpeta…", self.choose_output)
        self.open_button = button("Abrir carpeta", self.open_output)
        output_row.addWidget(self.browse_button)
        output_row.addWidget(self.open_button)
        output_layout.addLayout(output_row)
        output_layout.addWidget(
            label("Se conserva el original. Si un nombre ya existe, se añade un número.", "muted")
        )
        layout.addWidget(output_panel)
        footer = QHBoxLayout()
        progress_column = QVBoxLayout()
        self.summary = label("Añade documentos para comenzar.", "muted")
        progress_column.addWidget(self.summary)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Progreso del lote por archivos completados")
        progress_column.addWidget(self.progress)
        footer.addLayout(progress_column, 1)
        self.cancel_button = button("Detener después del actual", self.cancel_batch)
        self.cancel_button.setEnabled(False)
        footer.addWidget(self.cancel_button)
        self.convert_button = button("Convertir a Markdown", self.start_batch, "primary")
        footer.addWidget(self.convert_button)
        self.footer_panel = QWidget()
        self.footer_panel.setLayout(footer)
        layout.addWidget(self.footer_panel)
        self.navigation.currentChanged.connect(self.navigation_changed)
        self.statusBar().showMessage("MarkItDown ES 1.1.1 · Visor local · Motor reutilizable")
        self.shortcuts = [
            QShortcut(QKeySequence("Ctrl+O"), self, activated=self.choose_document),
            QShortcut(QKeySequence("Ctrl+F"), self, activated=self.viewer.search.setFocus),
        ]
        self.show_preview()
        self.update_controls()

    def busy(self):
        return self.worker is not None

    def navigation_changed(self, index):
        self.output_panel.setVisible(index == 0)
        self.footer_panel.setVisible(index == 0)

    def update_controls(self):
        busy = self.busy()
        for control in (
            self.add_button,
            self.drop_button,
            self.remove_button,
            self.clear_button,
            self.output,
            self.browse_button,
        ):
            control.setEnabled(not busy)
        self.convert_button.setEnabled(not busy and any(j.destination is None for j in self.jobs))
        self.cancel_button.setEnabled(busy)
        self.count.setText(f"Archivos · {len(self.jobs)}")

    def choose_files(self):
        if self.busy():
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Añadir documentos", "", f"Documentos ({patterns})"
        )
        self.add_paths(files)

    def add_paths(self, paths):
        if self.busy():
            return
        known = {job.source for job in self.jobs}
        rejected = []
        for value in paths:
            try:
                path = validate_source(Path(value))
                if path in known:
                    continue
                row = QTreeWidgetItem([path.name, "Pendiente"])
                row.setToolTip(0, str(path))
                self.queue.addTopLevelItem(row)
                self.jobs.append(Job(path, row))
                known.add(path)
            except (OSError, ValueError) as error:
                rejected.append(f"{Path(value).name}: {friendly_error(error)}")
        self.summary.setText(f"{len(self.jobs)} archivo(s) en la lista.")
        self.update_controls()
        if rejected:
            QMessageBox.warning(self, "Archivos no añadidos", "\n".join(rejected[:10]))

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if not self.busy() and urls and all(url.isLocalFile() for url in urls):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.busy():
            self.add_paths(
                [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            )
            event.acceptProposedAction()

    def remove_selected(self):
        if self.busy():
            return
        selected = self.queue.selectedItems()
        self.jobs = [job for job in self.jobs if job.row not in selected]
        for row in selected:
            self.queue.takeTopLevelItem(self.queue.indexOfTopLevelItem(row))
        self.update_controls()
        self.show_preview()

    def clear_jobs(self):
        if self.busy():
            return
        self.jobs.clear()
        self.queue.clear()
        self.progress.setValue(0)
        self.summary.setText("Añade documentos para comenzar.")
        self.update_controls()
        self.show_preview()

    def choose_output(self):
        selected = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta de salida", self.output.text()
        )
        if selected:
            self.output.setText(selected)

    def open_output(self):
        path = Path(self.output.text()).expanduser()
        if path.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
        else:
            QMessageBox.information(
                self, "Carpeta de salida", "La carpeta se creará al convertir el primer archivo."
            )

    def start_batch(self):
        if self.busy():
            return
        if not self.output.text().strip():
            QMessageBox.warning(self, "Elige una carpeta", "Indica dónde guardar los documentos.")
            return
        output = Path(self.output.text()).expanduser()
        try:
            output.mkdir(parents=True, exist_ok=True)
            if not output.is_dir():
                raise NotADirectoryError()
        except OSError:
            QMessageBox.warning(
                self, "Carpeta no disponible", "Elige una carpeta válida con permiso de escritura."
            )
            return
        pending = [(i, job.source) for i, job in enumerate(self.jobs) if job.destination is None]
        if not pending:
            return
        self.settings.setValue("output", str(output.resolve()))
        self.library.folder.setText(str(output.resolve()))
        self.completed, self.total = 0, len(pending)
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        for index, _ in pending:
            self.jobs[index].error = ""
            self.jobs[index].row.setText(1, "Pendiente")
        self.summary.setText("Preparando el motor de conversión…")
        self.worker = BatchWorker(pending, output, self, session=self.session)
        self.worker.started_file.connect(self.file_started)
        self.worker.result.connect(self.file_result)
        self.worker.finished.connect(self.batch_finished)
        self.update_controls()
        self.worker.start()

    def file_started(self, index):
        job = self.jobs[index]
        job.row.setText(1, "Convirtiendo…")
        self.summary.setText(f"{self.completed}/{self.total} completados · {job.source.name}")
        self.statusBar().showMessage(self.summary.text())

    def file_result(self, index, destination, error):
        job = self.jobs[index]
        job.destination = Path(destination) if destination else None
        job.error = error
        job.row.setText(1, "Error" if error else "Listo")
        job.row.setToolTip(1, error or destination)
        self.completed += 1
        self.progress.setValue(self.completed)
        if self.navigation.currentIndex() == 0:
            self.queue.setCurrentItem(job.row)
            self.show_preview()

    def cancel_batch(self):
        if self.worker:
            self.worker.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.summary.setText("Deteniendo: se terminará el archivo actual.")

    def batch_finished(self):
        stopped = self.worker.isInterruptionRequested()
        self.worker.deleteLater()
        self.worker = None
        errors = sum(bool(job.error) for job in self.jobs)
        done = sum(job.destination is not None for job in self.jobs)
        prefix = "Lote detenido" if stopped else "Lote terminado"
        self.summary.setText(f"{prefix} · {done} convertido(s) · {errors} error(es).")
        self.statusBar().showMessage(self.summary.text())
        self.update_controls()
        self.library.refresh()

    def selected_job(self):
        current = self.queue.currentItem()
        return next((job for job in self.jobs if job.row is current), None)

    def show_preview(self, *_):
        job = self.selected_job()
        if job and job.destination:
            self.viewer.open_path(job.destination)
            return
        elif job and job.error:
            message = job.error
        elif job and job.source.suffix.lower() in {".md", ".txt"}:
            self.viewer.open_path(job.source)
            return
        else:
            message = "Abre un Markdown o convierte documentos para leerlos aquí."
        self.viewer.message(message)

    def open_document(self, path):
        self.viewer.open_path(Path(path))

    def choose_document(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir documento",
            self.output.text(),
            "Markdown y texto (*.md *.txt *.csv *.json *.xml)",
        )
        if path:
            self.open_document(path)

    def convert_from_library(self, path):
        if not self.busy():
            self.add_paths([path])
            self.navigation.setCurrentIndex(0)

    def windows_help(self):
        QMessageBox.information(
            self,
            "Markdown en el Explorador de Windows",
            "Ejecuta Instalar-MarkItDown.cmd de la carpeta descargada para registrar el visor y abrir .md con doble clic.\n\n"
            "Para la vista previa en el Explorador: instala Microsoft PowerToys, activa Complementos del Explorador > Markdown y muestra el Panel de vista previa (Alt+P).\n\n"
            "La guía completa está en docs/EXPLORADOR.md.",
        )

    def closeEvent(self, event):
        if self.busy():
            self.cancel_batch()
            QMessageBox.information(
                self,
                "Conversión en curso",
                "Se terminará el archivo actual. Después podrás cerrar la aplicación.",
            )
            event.ignore()
        else:
            if not self.library.stop():
                event.ignore()
                return
            self.session.close()
            event.accept()
