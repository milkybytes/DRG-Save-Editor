import os
import sys

# the interface tests run without a display
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# main.py runs as a script with its own folder on the path, so its sibling modules
# (gvas, campaigns, ...) are imported by bare name. Do the same for the tests.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "main", "python")
)

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    import theme

    app = QApplication.instance() or QApplication([])
    theme.apply(app)
    return app


@pytest.fixture
def editor(qapp, tmp_path, monkeypatch):
    """the real window with a copy of a sample save already open; yields (main module, window, path of the copy)"""
    import shutil
    from PySide6.QtWidgets import QFileDialog
    import main

    window = main.create_window()
    save = tmp_path / "Player.sav"
    shutil.copy("tests/sample_save3.sav", save)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(save), "")))
    main.open_file()
    yield main, window, save
    window.close()
