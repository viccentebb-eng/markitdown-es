from markitdown_es.library import FileLibrary


def test_library_filters_asynchronously_and_opens_selected(qtbot, tmp_path):
    first = tmp_path / "primero.md"
    first.write_text("# Informe\nInformación Aurora", encoding="utf-8")
    (tmp_path / "segundo.txt").write_text("Otro documento", encoding="utf-8")
    library = FileLibrary()
    qtbot.addWidget(library)
    library.folder.setText(str(tmp_path))
    library.content.setText("informacion")
    library.kind.setCurrentText("Markdown")
    library.refresh()
    qtbot.waitUntil(lambda: library.worker is None, timeout=10000)
    assert library.results.topLevelItemCount() == 1
    with qtbot.waitSignal(library.selected) as signal:
        library.results.setCurrentItem(library.results.topLevelItem(0))
    assert signal.args[0] == first
    library.name.setText("no-existe")
    library.refresh()
    qtbot.waitUntil(lambda: library.worker is None, timeout=10000)
    assert library.results.topLevelItemCount() == 0
    assert library.stop()
