import subprocess
from pathlib import Path
from unittest.mock import patch

from markitdown_es.worker import convert_isolated


def test_native_crash_is_reported_as_document_error(tmp_path):
    with patch(
        "markitdown_es.worker.subprocess.run", return_value=subprocess.CompletedProcess([], -1)
    ):
        destination, error = convert_isolated(Path("documento.pdf"), tmp_path)
    assert not destination
    assert "motor se cerró" in error


def test_timeout_does_not_escape_worker(tmp_path):
    with patch(
        "markitdown_es.worker.subprocess.run", side_effect=subprocess.TimeoutExpired([], 300)
    ):
        destination, error = convert_isolated(Path("documento.pdf"), tmp_path)
    assert not destination
    assert "5 minutos" in error
