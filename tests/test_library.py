import os
from datetime import date, datetime

from markitdown_es.library import SearchQuery, search_files


def test_name_date_type_size_and_content_filters(tmp_path):
    recent = tmp_path / "Información.md"
    recent.write_text("# Proyecto\n\nLa contraseña del ejemplo es Aurora.", encoding="utf-8")
    old = tmp_path / "viejo.md"
    old.write_text("Aurora", encoding="utf-8")
    timestamp = datetime(2020, 1, 1).timestamp()
    os.utime(old, (timestamp, timestamp))
    (tmp_path / "otro.txt").write_text("Texto distinto", encoding="utf-8")
    results = list(
        search_files(
            SearchQuery(
                tmp_path,
                name="informacion",
                content="CONTRASENA",
                kind="Markdown",
                since=date(2026, 1, 1),
                size=1,
            )
        )
    )
    assert [result[0] for result in results] == [recent]
    assert not list(search_files(SearchQuery(tmp_path, kind="PDF")))
    assert not list(search_files(SearchQuery(tmp_path, size=3)))


def test_recursive_content_across_chunk_boundary_and_cancellation(tmp_path):
    folder = tmp_path / "subcarpeta"
    folder.mkdir()
    source = folder / "texto.md"
    source.write_text("a" * 65534 + "Proyecto Aurora", encoding="utf-8")
    assert len(list(search_files(SearchQuery(tmp_path, content="proyecto aurora")))) == 1
    assert not list(search_files(SearchQuery(tmp_path, recursive=False)))
    assert not list(search_files(SearchQuery(tmp_path), interrupted=lambda: True))
