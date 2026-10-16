"""Conversión local y escritura sin sobrescribir archivos existentes."""

from pathlib import Path

EXTENSIONS = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".xls",
        ".html",
        ".htm",
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".xml",
        ".epub",
    }
)
MAX_INPUT_BYTES = 100 * 1024 * 1024


def validate_source(path: Path) -> Path:
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError("Selecciona archivos individuales, no carpetas.")
    if path.suffix.lower() not in EXTENSIONS:
        raise ValueError("Formato no compatible con esta edición.")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("El archivo supera el límite de 100 MB.")
    signatures = {
        ".pdf": b"%PDF-",
        ".docx": b"PK\x03\x04",
        ".pptx": b"PK\x03\x04",
        ".xlsx": b"PK\x03\x04",
        ".epub": b"PK\x03\x04",
        ".xls": b"\xd0\xcf\x11\xe0",
    }
    if signature := signatures.get(path.suffix.lower()):
        with path.open("rb") as handle:
            header = handle.read(1024)
        valid = (
            signature in header if path.suffix.lower() == ".pdf" else header.startswith(signature)
        )
        if not valid:
            raise ValueError(
                "El contenido no corresponde al formato del archivo; puede estar dañado."
            )
    return path


def convert_file(source: Path, output: Path, converter) -> Path:
    source = validate_source(source)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Local-only entry point: never interpret a filename as a URL.
    if source.suffix.lower() in {".txt", ".md"}:
        try:
            markdown = source.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            from charset_normalizer import from_path

            detected = from_path(source).best()
            if detected is None:
                raise ValueError("No se reconoce la codificación del texto.") from None
            markdown = str(detected)
    else:
        result = converter.convert_local(str(source))
        markdown = result.markdown
    if not markdown.strip():
        raise ValueError("No se encontró texto. Si es un PDF escaneado, requiere OCR externo.")
    # Exclusive creation protects existing files, even across concurrent instances.
    number = 1
    while True:
        suffix = "" if number == 1 else f" ({number})"
        destination = output / f"{source.stem}{suffix}.md"
        try:
            handle = destination.open("x", encoding="utf-8", newline="\n")
        except FileExistsError:
            number += 1
            continue
        try:
            with handle:
                handle.write(markdown)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
        return destination


def friendly_error(error: Exception) -> str:
    if isinstance(error, FileNotFoundError):
        return "El archivo ya no existe o la carpeta no está disponible."
    if isinstance(error, PermissionError):
        return "Sin permiso de lectura o escritura. Elige otra carpeta o cierra el archivo."
    if isinstance(error, ValueError):
        return str(error)
    return "No se pudo convertir. Comprueba que el documento no esté dañado ni protegido."
