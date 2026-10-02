"""Nothing can be edited until a save is open, and the window says so."""
import shutil

import theme
import ui_main
from PySide6.QtWidgets import QFileDialog


def test_class_images_are_found():
    for name in ui_main.CLASSES:
        pixmap = theme.class_pixmap(name, 40)
        assert pixmap is not None and not pixmap.isNull() and pixmap.width() <= 40
        assert not theme.class_icon(name).isNull()


def test_without_a_save_everything_is_disabled_and_the_welcome_page_is_shown(qapp):
    import main

    window = main.create_window()
    assert all(not button.isEnabled() for button in window.nav_buttons)
    assert all(not button.isChecked() for button in window.nav_buttons)
    assert window.pages.currentIndex() == ui_main.WELCOME_PAGE
    assert window.page_title.text() == "Welcome"
    assert not window.actionSave_changes.isEnabled()
    assert window.actionOpen_Save_File.isEnabled()  # the one thing that works
    window.close()


def test_opening_a_save_enables_the_pages(qapp, tmp_path, monkeypatch):
    import main

    window = main.create_window()
    save = tmp_path / "Player.sav"
    shutil.copy("tests/sample_save3.sav", save)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(save), "")))
    main.open_file()

    assert all(button.isEnabled() for button in window.nav_buttons)
    assert window.pages.currentIndex() == 0 and window.nav_buttons[0].isChecked()
    assert window.page_title.text() == "Classes"

    # opening another save keeps the page that is being looked at
    window.nav_buttons[3].click()
    main.open_file()
    assert window.pages.currentIndex() == 3
    window.close()


def test_a_built_exe_looks_for_the_images_next_to_itself(tmp_path, monkeypatch):
    import os
    import sys

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "DRG Save Editor.exe"))
    assert os.path.normpath(theme.images_dir()) == os.path.normpath(tmp_path / "images")
