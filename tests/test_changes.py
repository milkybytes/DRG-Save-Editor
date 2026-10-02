"""Save and Reset only do something while there are unsaved changes."""
import seasons
from PySide6.QtWidgets import QFileDialog


def test_save_is_only_enabled_with_unsaved_changes(editor):
    main, window, save = editor
    assert not window.actionSave_changes.isEnabled()
    assert not window.actionReset_to_original_values.isEnabled()
    assert window.dirty_label.isHidden()

    original = window.bismor_text.text()
    window.bismor_text.setText("12345")
    assert window.actionSave_changes.isEnabled() and window.actionReset_to_original_values.isEnabled()
    assert not window.dirty_label.isHidden()

    window.bismor_text.setText(original)  # typed back to what the save has: nothing to save after all
    assert not window.actionSave_changes.isEnabled()
    assert window.dirty_label.isHidden()

    window.bismor_text.setText("12345")
    main.save_changes()
    assert not window.actionSave_changes.isEnabled()
    assert window.bismor_text.text() == "12345"


def test_every_kind_of_edit_counts(editor):
    main, window, save = editor

    window.driller_promo_box.setCurrentIndex(1 if window.driller_promo_box.currentIndex() != 1 else 2)
    assert window.actionSave_changes.isEnabled()
    main.reset_values()
    assert not window.actionSave_changes.isEnabled()

    main.set_all_25()
    assert window.actionSave_changes.isEnabled()
    main.reset_values()
    assert not window.actionSave_changes.isEnabled()

    driller = window.overclock_tree.topLevelItem(0)
    group = next(driller.child(i) for i in range(driller.childCount()) if driller.child(i).text(0) == "Cryo Cannon")
    group.child(0).setSelected(True)
    main.add_cores()
    assert window.actionSave_changes.isEnabled()
    main.remove_all_ocs()  # back to nothing unforged, which is what the save has
    assert not window.actionSave_changes.isEnabled()


def test_season_edits_count(editor):
    main, window, save = editor
    window.season_picker.setCurrentIndex(window.season_picker.findData(seasons.SEASON_GUIDS[1]))
    assert not window.actionSave_changes.isEnabled()  # looking at another season changes nothing
    window.scrip_text.setText("99")
    assert window.actionSave_changes.isEnabled()
    window.season_picker.setCurrentIndex(window.season_picker.findData(seasons.SEASON_GUIDS[6]))
    assert window.actionSave_changes.isEnabled()  # the edit to season 1 is still pending


def test_reset_after_a_save_goes_back_to_what_was_saved(editor):
    main, window, save = editor
    window.bismor_text.setText("777")
    main.save_changes()
    window.bismor_text.setText("5")
    main.reset_values()
    assert window.bismor_text.text() == "777"
    assert not window.actionSave_changes.isEnabled()


def test_the_backup_is_not_overwritten_by_saving(editor):
    main, window, save = editor
    backup = save.with_name(save.name + ".old")
    before = backup.read_bytes()
    window.bismor_text.setText("777")
    main.save_changes()
    assert backup.read_bytes() == before
    assert save.read_bytes() != before


def test_opening_another_save_starts_clean(editor, tmp_path, monkeypatch):
    main, window, save = editor
    window.bismor_text.setText("1")
    assert window.actionSave_changes.isEnabled()

    other = tmp_path / "Other.sav"
    other.write_bytes(open("tests/sample_save1.sav", "rb").read())
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(other), "")))
    main.open_file()
    assert not window.actionSave_changes.isEnabled()
    assert window.windowTitle().endswith("Other.sav")
