from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QTextDocument

from markitdown_es.viewer import DocumentViewer


def test_open_full_markdown_find_and_copy(qtbot, tmp_path, qapp):
    path = tmp_path / "documento.md"
    text = "# Documento\n\n" + "Texto de ejemplo.\n\n" * 12000 + "Último contenido Aurora"
    path.write_text(text, encoding="utf-8")
    viewer = DocumentViewer()
    qtbot.addWidget(viewer)
    assert viewer.open_path(path)
    assert "Último contenido" in viewer.preview.toPlainText()
    assert len(viewer.source.toPlainText()) > 200000
    viewer.search.setText("Aurora")
    assert viewer.find_next()
    assert viewer.preview.textCursor().selectedText() == "Aurora"
    viewer.copy.click()
    assert qapp.clipboard().text() == text
    viewer.tabs.setCurrentIndex(1)
    assert viewer.find_next()


def test_local_images_allowed_but_outside_and_network_blocked(qtbot, tmp_path):
    root = tmp_path / "documentos"
    root.mkdir()
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0)
    image.save(str(root / "local.png"))
    image.save(str(tmp_path / "privada.png"))
    path = root / "nota.md"
    path.write_text("# Nota\n\n![imagen](local.png)", encoding="utf-8")
    viewer = DocumentViewer()
    qtbot.addWidget(viewer)
    assert viewer.open_path(path)
    resource = QTextDocument.ResourceType.ImageResource
    assert not viewer.preview.loadResource(
        resource, QUrl.fromLocalFile(str(root / "local.png"))
    ).isNull()
    assert (
        viewer.preview.loadResource(resource, QUrl.fromLocalFile(str(tmp_path / "privada.png")))
        is None
    )
    assert viewer.preview.loadResource(resource, QUrl("https://example.com/tracker.png")) is None
