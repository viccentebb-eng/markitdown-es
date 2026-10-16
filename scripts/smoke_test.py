"""Prueba del .exe: interfaz, motor y recursos empaquetados en un proceso real."""

import json
import time
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer

from markitdown_es.__main__ import create_app
from markitdown_es.window import MainWindow


def run(inputs: str, output: str):
    started_at = time.perf_counter()
    app = create_app()
    directory = Path(output).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    window = MainWindow(QSettings(str(directory / "settings.ini"), QSettings.Format.IniFormat))
    window.output.setText(str(directory))
    window.add_paths(sorted(Path(inputs).resolve().glob("ejemplo.*")))
    if len(window.jobs) < 7:
        raise RuntimeError("Se necesitan las siete muestras de tests/fixtures.")
    window.show()
    window.start_batch()

    def finish():
        if window.busy():
            return
        timer.stop()
        results = [
            {"file": job.source.name, "output": str(job.destination), "error": job.error}
            for job in window.jobs
        ]
        success = all(
            job.destination
            and "Proyecto Aurora" in " ".join(job.destination.read_text(encoding="utf-8").split())
            for job in window.jobs
        )
        window.queue.setCurrentItem(
            next(job.row for job in window.jobs if job.source.suffix == ".html")
        )
        window.resize(1280, 900)
        window.output.setText("C:\\Documentos\\Markdown")
        app.processEvents()
        window.grab().save(str(directory / "interfaz.png"))
        # Exercise the viewer and asynchronous library in the actual frozen application.
        window.viewer.search.setText("equipo")
        viewer_ok = window.viewer.find_next()
        window.library.folder.setText(str(directory))
        window.library.name.setText("ejemplo")
        window.library.kind.setCurrentText("Markdown")
        window.library.refresh()
        window.navigation.setCurrentIndex(1)
        from PySide6.QtCore import QEventLoop

        loop = QEventLoop()
        window.library.worker.finished.connect(loop.quit)
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        library_ok = window.library.results.topLevelItemCount() == 7
        success = success and viewer_ok and library_ok
        window.library.folder.setText("C:\\Documentos\\Markdown")
        window.library.timer.stop()
        app.processEvents()
        window.grab().save(str(directory / "biblioteca.png"))
        (directory / "smoke.json").write_text(
            json.dumps(
                {
                    "ok": bool(success),
                    "results": results,
                    "viewer_search": viewer_ok,
                    "library": library_ok,
                    "seconds": round(time.perf_counter() - started_at, 3),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        timer.stop()
        window.close()
        app.exit(0 if success else 1)

    timer = QTimer()
    timer.setSingleShot(False)
    timer.timeout.connect(finish)
    timer.start(100)
    QTimer.singleShot(120000, lambda: app.exit(2))
    return app.exec()
