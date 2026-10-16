"""Prueba del .exe: interfaz, motor y recursos empaquetados en un proceso real."""

import json
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer

from markitdown_es.__main__ import create_app
from markitdown_es.window import MainWindow


def run(inputs: str, output: str):
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
        (directory / "smoke.json").write_text(
            json.dumps({"ok": bool(success), "results": results}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        timer.stop()
        window.close()
        app.exit(0 if success else 1)

    timer = QTimer()
    timer.timeout.connect(finish)
    timer.start(100)
    QTimer.singleShot(120000, lambda: app.exit(2))
    return app.exec()
