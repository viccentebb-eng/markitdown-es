from unittest.mock import patch

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from markitdown_es.window import MainWindow, SafePreview


@pytest.fixture
def window(qtbot, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings)
    window.output.setText(str(tmp_path / "salida"))
    qtbot.addWidget(window)
    window.show()
    yield window
    if window.worker:
        window.worker.requestInterruption()
        window.worker.wait(30000)


def test_file_picker_multi_selection_and_duplicates(window, tmp_path):
    paths = [tmp_path / "uno.txt", tmp_path / "dos.txt"]
    for path in paths:
        path.write_text("Contenido", encoding="utf-8")
    with patch(
        "markitdown_es.window.QFileDialog.getOpenFileNames",
        return_value=([str(p) for p in paths], ""),
    ):
        window.add_button.click()
    window.add_paths(paths)
    assert len(window.jobs) == 2
    assert window.convert_button.isEnabled()


def test_actual_drag_drop_accepts_only_local_files(window, tmp_path, qtbot):
    source = tmp_path / "documento.txt"
    source.write_text("Hola", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(source))])
    enter = QDragEnterEvent(
        QPoint(50, 50),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, enter)
    assert enter.isAccepted()
    drop = QDropEvent(
        QPointF(50, 50),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, drop)
    assert len(window.jobs) == 1
    mime.setUrls([QUrl("https://example.com/file.pdf")])
    remote = QDragEnterEvent(
        QPoint(50, 50),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, remote)
    assert not remote.isAccepted()


def test_batch_continues_after_error_and_preview_copies(window, qtbot, tmp_path):
    broken = tmp_path / "desaparecido.txt"
    broken.write_text("Temporal", encoding="utf-8")
    good = tmp_path / "nota.html"
    good.write_text("<h1>Proyecto Aurora</h1><p>Información útil</p>", encoding="utf-8")
    window.add_paths([broken, good])
    broken.unlink()
    window.convert_button.click()
    assert not window.clear_button.isEnabled()
    assert not window.output.isEnabled()
    qtbot.waitUntil(lambda: not window.busy(), timeout=60000)
    assert window.jobs[0].error
    assert window.jobs[1].destination.is_file()
    assert window.progress.value() == 2
    assert "1 error" in window.summary.text()
    assert window.library.folder.text() == window.output.text()
    assert window.statusBar().currentMessage() == window.summary.text()
    qtbot.waitUntil(lambda: window.library.worker is None, timeout=10000)
    assert window.library.results.topLevelItemCount() == 1
    window.queue.setCurrentItem(window.jobs[1].row)
    assert "Proyecto Aurora" in window.preview.toPlainText()
    window.copy_button.click()
    assert "Información útil" in QApplication.clipboard().text()
    # A retry includes only failed/pending files and preserves successful outputs.
    original_output = window.jobs[1].destination
    broken.write_text("<h1>Reparado</h1>", encoding="utf-8")
    window.start_batch()
    qtbot.waitUntil(lambda: not window.busy(), timeout=60000)
    assert window.jobs[1].destination == original_output
    assert not (original_output.parent / "nota (2).md").exists()


def test_cancel_stops_before_next_document(window, qtbot, tmp_path):
    from threading import Event

    from markitdown_es.worker import BatchWorker

    entered, release = Event(), Event()
    sources = [tmp_path / "uno.txt", tmp_path / "dos.txt"]
    for source in sources:
        source.write_text("Hola", encoding="utf-8")

    def slow_convert(source, output):
        entered.set()
        release.wait(10)
        return str(output / source.with_suffix(".md").name), ""

    worker = BatchWorker(list(enumerate(sources)), tmp_path)
    results = []
    worker.result.connect(lambda *args: results.append(args))
    with patch("markitdown_es.engine.ConversionSession.convert", side_effect=slow_convert):
        worker.start()
        qtbot.waitUntil(entered.is_set, timeout=30000)
        worker.requestInterruption()
        release.set()
        qtbot.waitUntil(lambda: not worker.isRunning(), timeout=30000)
        qtbot.waitUntil(lambda: len(results) == 1)
    assert results[0][0] == 0


def test_output_picker_remove_clear_and_unavailable_preview(window, tmp_path):
    folder = tmp_path / "destino"
    with patch("markitdown_es.window.QFileDialog.getExistingDirectory", return_value=str(folder)):
        window.browse_button.click()
    assert window.output.text() == str(folder)
    source = tmp_path / "nota.txt"
    source.write_text("Hola", encoding="utf-8")
    window.add_paths([source])
    window.queue.setCurrentItem(window.jobs[0].row)
    window.jobs[0].destination = tmp_path / "missing.md"
    window.show_preview()
    assert "no se puede leer" in window.preview.toPlainText()
    window.remove_button.click()
    assert not window.jobs
    window.add_paths([source])
    window.clear_button.click()
    assert window.queue.topLevelItemCount() == 0
    assert not window.convert_button.isEnabled()


def test_preview_does_not_load_local_or_remote_resources(qapp):
    preview = SafePreview()
    assert preview.loadResource(2, QUrl("file:///C:/private.png")) is None
    assert preview.loadResource(2, QUrl("https://example.com/tracker.png")) is None
    assert not preview.openLinks()
    assert not preview.openExternalLinks()
