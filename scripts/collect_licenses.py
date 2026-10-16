"""Copia avisos de las distribuciones instaladas sin credenciales ni rutas locales."""

from importlib.metadata import distributions
from pathlib import Path
from shutil import copy2

target = Path("build/third-party-notices")
for distribution in distributions():
    name = distribution.metadata["Name"]
    for entry in distribution.files or []:
        lowered = str(entry).lower()
        if ".." in entry.parts:
            continue
        if entry.suffix in {".py", ".pyc", ".pyd", ".dll"}:
            continue
        if (
            any(token in lowered for token in ("license", "copying", "notice"))
            or entry.name == "METADATA"
        ):
            source = Path(distribution.locate_file(entry))
            if source.is_file():
                destination = target / name / entry
                destination.parent.mkdir(parents=True, exist_ok=True)
                copy2(source, destination)
print("Avisos de terceros recopilados.")
