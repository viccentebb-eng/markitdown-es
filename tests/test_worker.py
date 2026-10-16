from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from markitdown_es.engine import ConversionSession


def test_native_crash_and_timeout_are_document_errors(tmp_path):
    for exit_code, timeout, expected in ((-1, 300, "motor se cerró"), (None, 0, "5 minutos")):
        session = ConversionSession()
        session.temporary = TemporaryDirectory()
        session.process = MagicMock()
        session.process.poll.return_value = exit_code
        with patch.object(session, "start"):
            destination, error = session.convert(Path("documento.pdf"), tmp_path, timeout=timeout)
        assert not destination
        assert expected in error
        session.close()


def test_real_engine_reuses_process_and_recovers_after_crash(tmp_path):
    source = tmp_path / "nota.txt"
    source.write_text("Información útil", encoding="utf-8")
    session = ConversionSession()
    try:
        first, error = session.convert(source, tmp_path / "salida")
        assert not error
        pid = session.process.pid
        second, error = session.convert(source, tmp_path / "salida")
        assert not error
        assert session.process.pid == pid
        assert first != second
        session.process.kill()
        session.process.wait()
        third, error = session.convert(source, tmp_path / "salida")
        assert not error
        assert session.process.pid != pid
        assert Path(third).read_text(encoding="utf-8") == "Información útil"
    finally:
        session.close()
