from pathlib import Path
from types import SimpleNamespace

import pytest
from markitdown import MarkItDown

from markitdown_es.conversion import convert_file, validate_source


@pytest.fixture(scope="module")
def converter():
    return MarkItDown(enable_plugins=False)


@pytest.mark.parametrize(
    "name",
    [
        "ejemplo.txt",
        "ejemplo.html",
        "ejemplo.csv",
        "ejemplo.docx",
        "ejemplo.xlsx",
        "ejemplo.pptx",
        "ejemplo.pdf",
    ],
)
def test_real_document_conversion(name, tmp_path, converter):
    source = Path(__file__).parent / "fixtures" / name
    result = convert_file(source, tmp_path, converter)
    assert "Proyecto Aurora" in " ".join(result.read_text(encoding="utf-8").split())


def test_collision_and_source_are_preserved(tmp_path, converter):
    source = tmp_path / "español.md"
    original = "# Español\n\nInformación útil."
    source.write_text(original, encoding="utf-8")
    second = convert_file(source, tmp_path, converter)
    third = convert_file(source, tmp_path, converter)
    assert source.read_text(encoding="utf-8") == original
    assert second.name == "español (2).md"
    assert third.name == "español (3).md"
    assert "Información útil" in second.read_text(encoding="utf-8")


def test_empty_conversion_does_not_create_output(tmp_path):
    source = tmp_path / "vacio.txt"
    source.touch()
    converter = SimpleNamespace(convert_local=lambda _: SimpleNamespace(markdown=" \n"))
    with pytest.raises(ValueError, match="No se encontró texto"):
        convert_file(source, tmp_path / "out", converter)
    assert not list((tmp_path / "out").glob("*.md"))


def test_invalid_missing_directory_and_oversize_inputs(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_source(tmp_path / "missing.pdf")
    with pytest.raises(ValueError, match="carpetas"):
        validate_source(tmp_path)
    invalid = tmp_path / "archivo.exe"
    invalid.touch()
    with pytest.raises(ValueError, match="Formato"):
        validate_source(invalid)
    large = tmp_path / "grande.txt"
    with large.open("wb") as handle:
        handle.truncate(100 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="100 MB"):
        validate_source(large)
    disguised = tmp_path / "falso.pdf"
    disguised.write_text("No es PDF", encoding="utf-8")
    with pytest.raises(ValueError, match="no corresponde"):
        validate_source(disguised)
