from unittest.mock import MagicMock, patch

from markitdown_es.__main__ import main


def test_file_argument_opens_markdown_without_conversion(tmp_path):
    source = tmp_path / "documento con espacios.md"
    source.write_text("# Informe", encoding="utf-8")
    app, window = MagicMock(), MagicMock()
    app.exec.return_value = 0
    with (
        patch("sys.argv", ["MarkItDown-ES.exe", str(source)]),
        patch("markitdown_es.__main__.create_app", return_value=app),
        patch("markitdown_es.__main__.MainWindow", return_value=window),
    ):
        assert main() == 0
    window.open_document.assert_called_once_with(source)
    window.start_batch.assert_not_called()
