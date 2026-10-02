"""The Assignments page: edits apply at once and are written when the save is."""
import campaigns
import gvas
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from campaign_page import COL_ASSIGN, COL_DONE, COL_GUID


def saved_state(path):
    return campaigns.read_state(path.read_bytes())


def row_of(page, guid):
    for row in range(page.table.rowCount()):
        if page.table.item(row, COL_GUID).text() == guid:
            return row
    raise AssertionError("no row for " + guid)


def test_the_page_is_part_of_the_window(editor):
    main, window, save = editor
    assert window.page_names[-1] == "Assignments"
    button = window.nav_buttons[-1]
    assert button.isEnabled()
    button.click()
    assert window.pages.currentWidget() is window.campaign_page
    assert window.page_title.text() == "Assignments"
    assert "Progress: 2" in window.campaign_page.active_label.text()  # the sample's active assignment


def test_weekly_assignments_are_not_listed(editor):
    main, window, save = editor
    page = window.campaign_page
    listed = {page.table.item(r, COL_GUID).text() for r in range(page.table.rowCount())}
    assert listed and not listed & campaigns.HIDDEN_GUIDS


def test_completing_the_active_assignment(editor):
    main, window, save = editor
    page = window.campaign_page
    active = page.state["active"][0]
    assert not window.actionSave_changes.isEnabled()

    page.complete_button.click()
    assert page.state["active"] is None and active in page.state["completed"]
    assert main.campaign_state == page.state  # main follows the page
    assert window.actionSave_changes.isEnabled()
    assert page.table.item(row_of(page, active), COL_DONE).checkState() == Qt.Checked

    main.save_changes()
    state = saved_state(save)
    assert state["active"] is None and state["completed"][-1] == active
    assert not window.actionSave_changes.isEnabled()


def test_ticking_and_unticking_done(editor):
    main, window, save = editor
    page = window.campaign_page
    row = next(r for r in range(page.table.rowCount()) if page.table.item(r, COL_DONE).checkState() != Qt.Checked)
    guid = page.table.item(row, COL_GUID).text()

    page.table.item(row, COL_DONE).setCheckState(Qt.Checked)
    assert guid in page.state["completed"] and window.actionSave_changes.isEnabled()
    main.save_changes()
    assert guid in saved_state(save)["completed"]

    page.table.item(row_of(page, guid), COL_DONE).setCheckState(Qt.Unchecked)
    assert window.actionSave_changes.isEnabled()
    page.table.item(row_of(page, guid), COL_DONE).setCheckState(Qt.Checked)  # back to what is saved
    assert not window.actionSave_changes.isEnabled()


def test_assigning(editor):
    main, window, save = editor
    page = window.campaign_page
    row = next(r for r in range(page.table.rowCount()) if page.table.item(r, COL_DONE).checkState() == Qt.Checked)
    guid = page.table.item(row, COL_GUID).text()

    page.table.cellWidget(row, COL_ASSIGN).click()
    assert page.state["active"][0] == guid and guid not in page.state["completed"]
    main.save_changes()
    state = saved_state(save)
    assert state["active"][0] == guid and guid not in state["completed"]


def test_unassigning(editor):
    main, window, save = editor
    window.campaign_page.clear_button.click()
    main.save_changes()
    assert saved_state(save)["active"] is None


def test_adding_an_assignment_by_guid(editor):
    main, window, save = editor
    page = window.campaign_page
    rows = page.table.rowCount()

    page.guid_edit.setText("not a guid")
    page.add_button.click()
    assert "32 hexadecimal" in page.add_status.text() and page.table.rowCount() == rows

    page.guid_edit.setText(next(iter(campaigns.HIDDEN_GUIDS)))
    page.add_button.click()
    assert "managed by the game" in page.add_status.text() and page.table.rowCount() == rows

    guid = "AB" * 16
    page.guid_edit.setText(guid.lower())
    page.add_button.click()
    assert page.table.rowCount() == rows + 1
    page.table.item(row_of(page, guid), COL_DONE).setCheckState(Qt.Checked)
    main.save_changes()
    assert guid in saved_state(save)["completed"]


def test_reset_discards_assignment_edits(editor):
    main, window, save = editor
    page = window.campaign_page
    page.clear_button.click()
    assert page.state["active"] is None
    main.reset_values()
    assert page.state["active"] is not None and main.campaign_state["active"] is not None
    assert not window.actionSave_changes.isEnabled()


def test_a_save_without_assignment_data(editor, monkeypatch):
    main, window, save = editor
    other = save.with_name("NoCampaign.sav")
    data = gvas.loads(open("tests/sample_save3.sav", "rb").read())
    data.props.remove_named("CampaignSave")
    other.write_bytes(gvas.dumps(data))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(other), "")))
    window.nav_buttons[-1].click()
    main.open_file()
    assert main.campaign_state is None
    assert not window.nav_buttons[-1].isEnabled()
    assert window.pages.currentIndex() == 0  # moved off the unavailable page
