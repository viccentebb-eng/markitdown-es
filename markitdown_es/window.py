from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .conversion import EXTENSIONS, friendly_error, validate_source
from .worker import BatchWorker

PREVIEW_LIMIT = 200_000


@dataclass
class Job:
    source: Path
    row: QTreeWidgetItem
    destination: Path | None = None
    error: str = ""


class SafePreview(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setAccessibleName("Vista previa del documento Markdown")
        self.document().setDefaultStyleSheet(
            "body { color: #172b3a; } h1, h2, h3 { color: #16394b; } "
            "pre { background: #f2f5f7; } th, td { padding: 6px; }"
        )

    def loadResource(self, resource_type, name):
        # Document images/links must not read other local files or call the network.
        return None


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
        self.completed = 0
        self.total = 0
        self.setWindowTitle("MarkItDown · Documentos a Markdown")
        self.resize(1180, 800)
        self.setMinimumSize(900, 680)
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
        splitter.addWidget(left)

        right = QFrame()
        right.setObjectName("panel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 16)
        right_layout.setSpacing(12)
        preview_top = QHBoxLayout()
        preview_top.addWidget(label("Vista previa", "section"), 1)
        self.copy_button = button("Copiar Markdown", self.copy_markdown)
        self.copy_button.setEnabled(False)
        preview_top.addWidget(self.copy_button)
        right_layout.addLayout(preview_top)
        self.preview_name = label("Selecciona un archivo convertido", "muted")
        self.preview_name.setMinimumHeight(32)
        right_layout.addWidget(self.preview_name)
        self.tabs = QTabWidget()
        self.preview = SafePreview()
        self.source = QPlainTextEdit()
        self.source.setReadOnly(True)
        self.source.setAccessibleName("Código fuente Markdown")
        self.tabs.addTab(self.preview, "Documento")
        self.tabs.addTab(self.source, "Markdown")
        right_layout.addWidget(self.tabs, 1)
        right_layout.addWidget(
            label(
                "Encabezados, listas y tablas. Las imágenes y enlaces externos no se abren en la vista previa.",
                "muted",
            )
        )
        splitter.addWidget(right)
        splitter.setSizes([560, 540])
        layout.addWidget(splitter, 1)

        output_panel = QFrame()
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
        layout.addLayout(footer)
        self.statusBar().showMessage(
            "MarkItDown ES 1.0 · Aplicación independiente basada en Microsoft MarkItDown"
        )
        self.shortcuts = [QShortcut(QKeySequence("Ctrl+O"), self, activated=self.choose_files)]
        self.show_preview()
        self.update_controls()

    def busy(self):
        return self.worker is not None

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
        self.completed, self.total = 0, len(pending)
        self.progress.setRange(0, self.total)
        self.progress.setValue(0)
        for index, _ in pending:
            self.jobs[index].error = ""
            self.jobs[index].row.setText(1, "Pendiente")
        self.summary.setText("Preparando el motor de conversión…")
        self.worker = BatchWorker(pending, output, self)
        self.worker.started_file.connect(self.file_started)
        self.worker.result.connect(self.file_result)
        self.worker.finished.connect(self.batch_finished)
        self.update_controls()
        self.worker.start()

    def file_started(self, index):
        job = self.jobs[index]
        job.row.setText(1, "Convirtiendo…")
        self.summary.setText(f"{self.completed}/{self.total} completados · {job.source.name}")

    def file_result(self, index, destination, error):
        job = self.jobs[index]
        job.destination = Path(destination) if destination else None
        job.error = error
        job.row.setText(1, "Error" if error else "Listo")
        job.row.setToolTip(1, error or destination)
        self.completed += 1
        self.progress.setValue(self.completed)
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
        self.update_controls()

    def selected_job(self):
        current = self.queue.currentItem()
        return next((job for job in self.jobs if job.row is current), None)

    def show_preview(self, *_):
        job = self.selected_job()
        self.copy_button.setEnabled(False)
        if job and job.destination:
            try:
                with job.destination.open(encoding="utf-8") as handle:
                    text = handle.read(PREVIEW_LIMIT + 1)
                truncated = len(text) > PREVIEW_LIMIT
                text = text[:PREVIEW_LIMIT]
                self.preview.setMarkdown(text)
                self.source.setPlainText(text)
                suffix = " · Vista limitada a 200 000 caracteres" if truncated else ""
                self.preview_name.setText(job.destination.name + suffix)
                self.copy_button.setEnabled(True)
                return
            except OSError:
                message = "El archivo de salida se movió o no se puede leer."
        elif job and job.error:
            message = job.error
        else:
            message = "Tu documento aparecerá aquí después de convertirlo."
        self.preview_name.setText(job.source.name if job else "Selecciona un archivo convertido")
        self.preview.setPlainText(message)
        self.source.setPlainText("")

    def copy_markdown(self):
        job = self.selected_job()
        if job and job.destination:
            try:
                QApplication.clipboard().setText(job.destination.read_text(encoding="utf-8"))
                self.statusBar().showMessage("Markdown completo copiado al portapapeles.", 4000)
            except OSError:
                QMessageBox.warning(
                    self, "No se pudo copiar", "El archivo de salida no está disponible."
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
            event.accept()
