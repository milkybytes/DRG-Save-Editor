"""The Resources page: icons on every row, Phazyonite with the minerals, no Data Cells box."""
import theme
import ui_main
from PySide6.QtWidgets import QLabel


def test_every_resource_icon_loads_and_fits_its_slot():
    for box_name in theme.RESOURCE_ICONS:
        pixmap = theme.resource_pixmap(box_name)
        assert pixmap is not None and not pixmap.isNull(), box_name
        assert max(pixmap.width(), pixmap.height()) <= 28


def test_every_box_on_the_resources_page_has_an_icon():
    boxes = [name for name, _ in ui_main.MINERALS + ui_main.BREWING + ui_main.MISC]
    assert sorted(boxes) == sorted(theme.RESOURCE_ICONS)


def test_phazyonite_is_listed_with_the_minerals():
    assert ("phazy_text", "Phazyonite") in ui_main.MINERALS
    assert ("phazy_text", "Phazyonite") not in ui_main.MISC


def test_data_cells_cannot_be_edited(editor):
    main, window, save = editor
    assert not hasattr(window, "data_text")
    labels = {label.text() for label in window.findChildren(QLabel)}
    assert "Data Cells" not in labels


def test_saving_leaves_the_data_cells_as_they_were(editor):
    main, window, save = editor
    before = main.get_resources(save.read_bytes())
    window.bismor_text.setText("4321")
    main.save_changes()
    after = main.get_resources(save.read_bytes())
    assert after["data"] == before["data"]
    assert after["bismor"] == 4321
    assert main.stats["misc"]["data"] == before["data"]


def test_the_page_shows_a_picture_next_to_each_resource(editor):
    main, window, save = editor
    pictures = [
        label for label in window.pages.widget(1).findChildren(QLabel)
        if label.pixmap() is not None and not label.pixmap().isNull()
    ]
    assert len(pictures) == len(theme.RESOURCE_ICONS)
