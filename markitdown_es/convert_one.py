"""Punto de entrada interno: un documento por proceso para aislar fallos nativos."""

import json
import sys
from pathlib import Path

from .conversion import convert_file, friendly_error


def main(source: str, output: str, report: str):
    result = {"destination": "", "error": ""}
    try:
        from markitdown import MarkItDown

        converter = MarkItDown(enable_plugins=False)
        result["destination"] = str(convert_file(Path(source), Path(output), converter))
    except Exception as error:  # noqa: BLE001 - process boundary reports document failures
        result["error"] = friendly_error(error)
    Path(report).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 1 if result["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
