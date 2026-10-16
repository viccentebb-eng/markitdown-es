import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QThread, Signal


def convert_isolated(source: Path, output: Path) -> tuple[str, str]:
    with TemporaryDirectory(prefix="markitdown-es-") as temporary:
        report = Path(temporary) / "result.json"
        command = [sys.executable]
        if getattr(sys, "frozen", False):
            command += ["--convert-one"]
        else:
            command += ["-m", "markitdown_es.convert_one"]
        command += [str(source), str(output.resolve()), str(report)]
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if not report.is_file():
                return (
                    "",
                    "El motor se cerró al leer este documento. Los demás archivos continuarán.",
                )
            result = json.loads(report.read_text(encoding="utf-8"))
            if completed.returncode != 0 and not result["error"]:
                return "", "El motor terminó con un error. Reintenta este documento."
            return result["destination"], result["error"]
        except subprocess.TimeoutExpired:
            return "", "La conversión superó los 5 minutos. Prueba con un documento más pequeño."
        except (OSError, ValueError, KeyError):
            return "", "No se pudo iniciar el motor o leer su resultado."


class BatchWorker(QThread):
    started_file = Signal(int)
    result = Signal(int, str, str)

    def __init__(self, jobs: list[tuple[int, Path]], output: Path, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.output = output

    def run(self):
        for index, source in self.jobs:
            if self.isInterruptionRequested():
                break
            self.started_file.emit(index)
            destination, error = convert_isolated(source, self.output)
            self.result.emit(index, destination, error)
