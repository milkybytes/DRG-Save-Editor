"""Credits, perk points, resources and class XP and promotions, including for saves that lack them."""
import copy

import gvas
import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

import player

SAMPLES = ["tests/sample_save1.sav", "tests/sample_save2.sav", "tests/sample_save3.sav", "tests/no_perk_points_pre.sav"]
DRILLER = "9EDD56F1EEBCC5488D5B5E5B80B62DB4"


def load(path="tests/sample_save3.sav"):
    return open(path, "rb").read()


def read(data):
    return player.read(gvas.loads(data))


def lower_dict(values):
    return copy.deepcopy(values)


@pytest.mark.parametrize("path", SAMPLES)
def test_rewriting_what_was_read_changes_nothing(path):
    data = load(path)
    assert player.apply_to_bytes(data, read(data)) == data


def test_the_sample_reads_sensibly():
    values = read(load())
    assert values["misc"]["credits"] == 427436384 and values["misc"]["perks"] == 18
    assert values["xp"]["driller"] == {"xp": 187102, "promo": 4}
    assert values["minerals"]["bismor"] == 135338 and values["brewing"]["yeast"] == 82025
    assert values["misc"]["phazyonite"] == 0  # this save never owned any


def test_values_are_written_and_read_back():
    data = load()
    values = read(data)
    values["misc"]["credits"] = 1234
    values["misc"]["perks"] = 0
    values["minerals"]["umanite"] = 99
    values["misc"]["phazyonite"] = 55  # a resource the save did not have yet
    values["xp"]["scout"] = {"xp": 777, "promo": 20}
    again = read(player.apply_to_bytes(data, values))
    assert again == values
    # the file is still well formed
    saved = player.apply_to_bytes(data, values)
    assert gvas.dumps(gvas.loads(saved)) == saved


def test_promotions_also_set_the_levels_they_are_worth():
    data = load()
    values = read(data)
    values["xp"]["gunner"]["promo"] = 7
    entry = [e for e in gvas.loads(player.apply_to_bytes(data, values)).find("CharacterSaves").value
             if e.get("SaveGameID").value == "AE56E180FEC0C44D96FA29C28366B97B"][0]
    assert entry.get("TimesRetired").value == 7 and entry.get("RetiredCharacterLevels").value == 175


def test_an_untouched_fractional_resource_is_left_alone():
    save = gvas.loads(load())
    owned = save.find("Resources", "OwnedResources")
    owned.value[0] = (owned.value[0][0], 12.5)
    data = gvas.dumps(save)
    assert player.apply_to_bytes(data, read(data)) == data  # not rounded to 12


# ---- a new player's save: the game leaves out everything that is still zero


def stripped(*changes):
    save = gvas.loads(load())
    for change in changes:
        change(save)
    return gvas.dumps(save)


def drop_credits(save):
    save.props.remove_named("Credits")


def drop_perks(save):
    save.props.remove_named("PerkPoints")


def drop_some_resources(save):
    owned = save.find("Resources", "OwnedResources")
    owned.value[:] = owned.value[:3]


def drop_resources_entirely(save):
    save.props.remove_named("Resources")


def drop_driller_xp(save):
    for entry in save.find("CharacterSaves").value:
        if entry.get("SaveGameID").value == DRILLER:
            entry.remove_named("XP")
            entry.remove_named("TimesRetired")
            entry.remove_named("RetiredCharacterLevels")


def drop_driller_entirely(save):
    chars = save.find("CharacterSaves")
    chars.value[:] = [e for e in chars.value if e.get("SaveGameID").value != DRILLER]


def drop_all_classes(save):
    save.props.remove_named("CharacterSaves")


@pytest.mark.parametrize(
    "change, check",
    [
        (drop_credits, lambda v: v["misc"]["credits"] == 0),
        (drop_perks, lambda v: v["misc"]["perks"] == 0),
        (drop_some_resources, lambda v: v["misc"]["phazyonite"] == 0 and v["minerals"]["croppa"] == 0),
        (drop_resources_entirely, lambda v: all(x == 0 for g in ("minerals", "brewing") for x in v[g].values())),
        (drop_driller_xp, lambda v: v["xp"]["driller"] == {"xp": 0, "promo": 0}),
        (drop_driller_entirely, lambda v: v["xp"]["driller"] == {"xp": 0, "promo": 0}),
        (drop_all_classes, lambda v: all(c == {"xp": 0, "promo": 0} for c in v["xp"].values())),
    ],
)
def test_missing_entries_read_as_zero_not_garbage(change, check):
    values = read(stripped(change))
    assert check(values)
    assert all(v >= 0 for g in ("minerals", "brewing", "misc") for v in values[g].values())


@pytest.mark.parametrize(
    "change",
    [drop_credits, drop_perks, drop_some_resources, drop_resources_entirely, drop_driller_xp, drop_driller_entirely, drop_all_classes],
)
def test_nothing_is_written_for_things_that_are_still_zero(change):
    data = stripped(change)
    assert player.apply_to_bytes(data, read(data)) == data  # no entries invented for zeros


@pytest.mark.parametrize(
    "change",
    [drop_credits, drop_perks, drop_some_resources, drop_resources_entirely, drop_driller_xp, drop_driller_entirely, drop_all_classes],
)
def test_setting_values_creates_what_is_missing(change):
    data = stripped(change)
    values = read(data)
    values["misc"]["credits"] = 500
    values["misc"]["perks"] = 3
    values["minerals"]["bismor"] = 40
    values["brewing"]["yeast"] = 8
    values["misc"]["phazyonite"] = 2
    for dwarf in values["xp"]:
        values["xp"][dwarf] = {"xp": 1500, "promo": 2}
    saved = player.apply_to_bytes(data, values)
    assert read(saved) == values
    assert gvas.dumps(gvas.loads(saved)) == saved  # well formed, sizes and all


def test_created_properties_go_where_the_game_puts_them():
    data = stripped(drop_credits, drop_perks, drop_all_classes, drop_resources_entirely)
    values = read(data)
    values["misc"]["credits"], values["misc"]["perks"], values["minerals"]["bismor"] = 10, 1, 5
    values["xp"]["scout"] = {"xp": 100, "promo": 0}
    names = [p.name for p in gvas.loads(player.apply_to_bytes(data, values)).props]
    assert names.index("PerkPoints") < names.index("CharacterSaves") < names.index("Credits") < names.index("Resources")


def test_a_save_that_spells_the_class_id_the_old_way(tmp_path):
    # older saves call it SavegameID
    data = load("tests/no_perk_points_pre.sav")
    values = read(data)
    assert values["xp"]["scout"]["xp"] == 145607
    values["xp"]["scout"]["xp"] = 5
    assert read(player.apply_to_bytes(data, values))["xp"]["scout"]["xp"] == 5


# ---- in the editor


def test_opening_a_save_with_things_missing_shows_zeros(editor, tmp_path, monkeypatch):
    main, window, save = editor
    other = tmp_path / "New.sav"
    other.write_bytes(stripped(drop_credits, drop_some_resources, drop_driller_entirely))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(other), "")))
    main.open_file()
    assert window.credits_text.text() == "0"
    assert window.phazy_text.text() == "0" and window.croppa_text.text() == "0"
    assert window.driller_xp.text() == "0"
    assert not window.actionSave_changes.isEnabled()

    window.credits_text.setText("250")
    window.phazy_text.setText("12")
    main.save_changes()
    saved = read(other.read_bytes())
    assert saved["misc"]["credits"] == 250 and saved["misc"]["phazyonite"] == 12


def test_a_file_that_is_not_a_save_is_refused(editor, tmp_path, monkeypatch):
    main, window, save = editor
    junk = tmp_path / "junk.sav"
    junk.write_bytes(b"this is not a save file")
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: shown.append(a[1])))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(junk), "")))
    before = window.driller_xp.text()
    main.open_file()
    assert shown == ["Can't open this file"]
    assert main.file_name == str(save)  # what was open stays open
    assert window.driller_xp.text() == before
    assert not junk.with_name("junk.sav.old").exists()  # and no backup of the junk
