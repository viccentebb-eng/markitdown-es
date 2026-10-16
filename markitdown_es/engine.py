"""Motor residente fuera de la interfaz. Un único modelo por sesión, recuperable."""

import json
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from .conversion import convert_file, friendly_error


class ConversionSession:
    def __init__(self):
        self.process = None
        self.temporary = None
        self.sequence = 0

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process = None
        if self.temporary:
            self.temporary.cleanup()
            self.temporary = None

    def start(self):
        if self.process and self.process.poll() is None:
            return
        self.close()
        self.temporary = TemporaryDirectory(prefix="markitdown-es-")
        command = [sys.executable]
        command += ["--serve"] if getattr(sys, "frozen", False) else ["-m", "markitdown_es.engine"]
        command.append(self.temporary.name)
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

    def convert(self, source: Path, output: Path, timeout=300) -> tuple[str, str]:
        try:
            self.start()
            self.sequence += 1
            directory = Path(self.temporary.name)
            report = directory / f"result-{self.sequence}.json"
            request = {
                "id": self.sequence,
                "source": str(source.resolve()),
                "output": str(output.resolve()),
            }
            temporary = directory / "request.tmp"
            temporary.write_text(json.dumps(request), encoding="utf-8")
            temporary.replace(directory / "request.json")
            deadline = time.monotonic() + timeout
            while not report.exists():
                if self.process.poll() is not None:
                    return (
                        "",
                        "El motor se cerró al leer este documento. Los demás archivos continuarán.",
                    )
                if time.monotonic() >= deadline:
                    self.close()
                    return (
                        "",
                        "La conversión superó los 5 minutos. Prueba con un documento más pequeño.",
                    )
                time.sleep(0.02)
            result = json.loads(report.read_text(encoding="utf-8"))
            report.unlink()
            return result["destination"], result["error"]
        except (OSError, ValueError, KeyError):
            self.close()
            return "", "No se pudo iniciar el motor o leer su resultado."


def serve(directory: str):
    folder = Path(directory)
    converter = None
    last_activity = time.monotonic()
    # Idle workers exit after one minute, including after an unexpected GUI exit.
    while folder.exists() and time.monotonic() - last_activity < 60:
        request_file = folder / "request.json"
        if not request_file.exists():
            time.sleep(0.02)
            continue
        request = json.loads(request_file.read_text(encoding="utf-8"))
        request_file.unlink()
        result = {"destination": "", "error": ""}
        try:
            source = Path(request["source"])
            if converter is None and source.suffix.lower() not in {".txt", ".md"}:
                from markitdown import MarkItDown

                converter = MarkItDown(enable_plugins=False)
            result["destination"] = str(convert_file(source, Path(request["output"]), converter))
        except Exception as error:  # noqa: BLE001 - recover a document error at the process boundary
            result["error"] = friendly_error(error)
        report = folder / f"result-{request['id']}.tmp"
        report.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        report.replace(report.with_suffix(".json"))
        last_activity = time.monotonic()
    return 0


if __name__ == "__main__":
    raise SystemExit(serve(sys.argv[1]))
