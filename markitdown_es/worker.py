from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .engine import ConversionSession


class BatchWorker(QThread):
    started_file = Signal(int)
    result = Signal(int, str, str)

    def __init__(self, jobs: list[tuple[int, Path]], output: Path, parent=None, session=None):
        super().__init__(parent)
        self.jobs = jobs
        self.output = output
        self.session = session or ConversionSession()
        self.owns_session = session is None

    def run(self):
        try:
            for index, source in self.jobs:
                if self.isInterruptionRequested():
                    break
                self.started_file.emit(index)
                destination, error = self.session.convert(source, self.output)
                self.result.emit(index, destination, error)
        finally:
            if self.owns_session:
                self.session.close()
