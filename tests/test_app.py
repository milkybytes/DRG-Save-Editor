"""The editor driven through its widgets, the way the buttons do it, on a copy of a sample save."""
import collections
import json
import re

import gvas
import schematics
import seasons
from PySide6.QtWidgets import QFileDialog


def leaves(tree):
    """(class, group, leaf item) for every overclock in the tree"""
    root = tree.invisibleRootItem()
    for i in range(root.childCount()):
        cls = root.child(i)
        for j in range(cls.childCount()):
            group = cls.child(j)
            for k in range(group.childCount()):
                yield cls, group, group.child(k)


def find_leaf(tree, cls_name, group_name, status="Unacquired"):
    for cls, group, leaf in leaves(tree):
        if cls.text(0) == cls_name and group.text(0) == group_name and leaf.text(1) == status:
            return leaf
    raise AssertionError("no %s leaf in %s / %s" % (status, cls_name, group_name))


def visible(tree):
    return [leaf for _, _, leaf in leaves(tree) if not leaf.isHidden()]


def owned(path):
    return schematics.get_owned_schematics(gvas.loads(path.read_bytes()))


def test_every_widget_main_uses_exists(editor):
    main, window, _ = editor
    with open("src/main/python/main.py", encoding="utf-8") as f:
        used = set(re.findall(r"^\s*(?!#).*?\bwidget\.(\w+)", f.read(), re.M))
    missing = sorted(n for n in used if not hasattr(window, n))
    assert not missing


def test_opening_a_save_fills_the_window(editor):
    main, window, _ = editor
    assert window.pages.isEnabled() and not window.actionSave_changes.isEnabled()  # nothing to save yet
    assert window.driller_xp.text().isdigit() and window.bismor_text.text().isdigit()
    total = len(main.guid_dict)
    assert window.oc_counts.text().startswith("%d of %d shown" % (total, total))
    classes = [window.overclock_tree.topLevelItem(i).text(0) for i in range(window.overclock_tree.topLevelItemCount())]
    assert classes == ["Driller", "Engineer", "Gunner", "Scout"]


def test_cosmetic_groups_sort_after_the_weapons(editor):
    main, window, _ = editor
    driller = window.overclock_tree.topLevelItem(0)
    names = [driller.child(i).text(0) for i in range(driller.childCount())]
    first_cosmetic = next(i for i, n in enumerate(names) if n.startswith("Cosmetic - "))
    assert all(n.startswith("Cosmetic - ") for n in names[first_cosmetic:])
    assert names[:first_cosmetic] == sorted(names[:first_cosmetic], key=str.lower)


def test_add_a_cosmetic_save_reopen_and_remove_it(editor):
    main, window, save = editor
    leaf = find_leaf(window.overclock_tree, "Driller", "Cosmetic - Beards")
    guid = leaf.text(2)
    leaf.setSelected(True)
    main.add_cores()
    assert window.unforged_list.count() == 1 and window.unforged_count.text() == "1"
    assert leaf.text(1) == "Unforged"

    main.save_changes()
    assert owned(save) == [guid]

    main.open_file()  # read it back in
    assert window.unforged_list.count() == 1
    assert window.unforged_list.item(0).data(0x0100) == guid

    main.remove_all_ocs()
    assert window.unforged_list.count() == 0 and window.unforged_count.text() == "0"
    main.save_changes()
    assert owned(save) == []
    assert find_leaf(window.overclock_tree, "Driller", "Cosmetic - Beards").text(1) == "Unacquired"


def test_unforged_list_is_sorted_labelled_and_coloured(editor):
    main, window, _ = editor
    tree = window.overclock_tree
    wanted = [
        find_leaf(tree, "Scout", "Nishanka Boltshark X-80"),
        find_leaf(tree, "Driller", "Cosmetic - Victory Poses"),
        find_leaf(tree, "Gunner", "Armskore Coil Gun"),
        find_leaf(tree, "Driller", "Cryo Cannon"),
    ]
    for leaf in wanted:
        leaf.setSelected(True)
    main.add_cores()

    items = [window.unforged_list.item(i) for i in range(window.unforged_list.count())]
    names = [item.text() for item in items]
    classes = [main.guid_dict[item.data(0x0100)]["class"] for item in items]
    # weapon overclocks first (by class), cosmetic overclocks after; the class portrait and the category lead each row
    assert classes == ["Driller", "Gunner", "Scout", "Driller"]
    assert names[0].startswith("Cryo Cannon  ·  ")
    assert names[1].startswith("Armskore Coil Gun  ·  ")
    assert names[2].startswith("Nishanka Boltshark X-80  ·  ")
    assert names[3].startswith("Victory Pose  ·  ")
    assert all(not item.icon().isNull() for item in items)

    import theme
    colours = [item.foreground().color().name().lower() for item in items]
    assert colours == [theme.CLASS_COLORS[c].lower() for c in classes]


def test_an_overclock_can_be_added_and_removed_selected(editor):
    main, window, save = editor
    leaf = find_leaf(window.overclock_tree, "Driller", "Cryo Cannon")
    guid = leaf.text(2)
    leaf.setSelected(True)
    main.add_cores()
    main.save_changes()
    assert owned(save) == [guid]

    window.unforged_list.selectAll()
    main.remove_selected_ocs()
    main.save_changes()
    assert owned(save) == []


def test_selecting_a_group_adds_everything_shown_in_it(editor):
    main, window, save = editor
    window.oc_class_filter.setCurrentText("Driller")
    window.oc_kind_filter.setCurrentText("Cosmetic overclocks")
    cosmetics = json.load(open("cosmetics.json", encoding="utf-8"))
    forged = set(gvas.loads(save.read_bytes()).find("SchematicSave", "ForgedSchematics").value)
    beards = [
        g
        for g, e in cosmetics.items()
        if e["class"] == "Driller" and e["weapon"] == "Cosmetic - Beards" and g not in forged
    ]
    assert beards and len(beards) < 36  # some are forged already in the sample, and those are not added again

    driller = window.overclock_tree.topLevelItem(0)
    group = next(driller.child(i) for i in range(driller.childCount()) if driller.child(i).text(0) == "Cosmetic - Beards")
    group.setSelected(True)
    main.add_cores()
    main.save_changes()
    assert sorted(owned(save)) == sorted(beards)


def test_filters_and_search(editor):
    main, window, _ = editor
    tree = window.overclock_tree
    everything = len(visible(tree))

    window.oc_search.setText("wave cooker")
    assert {leaf.parent().text(0) for leaf in visible(tree)} == {"Colette Wave Cooker"}
    assert len(visible(tree)) == 6

    window.oc_search.setText("")
    window.oc_kind_filter.setCurrentText("Cosmetic overclocks")
    assert visible(tree) and all(l.parent().text(0).startswith("Cosmetic - ") for l in visible(tree))
    window.oc_kind_filter.setCurrentText("Weapon overclocks")
    assert visible(tree) and not any(l.parent().text(0).startswith("Cosmetic - ") for l in visible(tree))

    window.oc_kind_filter.setCurrentIndex(0)
    window.oc_class_filter.setCurrentText("Scout")
    assert {leaf.parent().parent().text(0) for leaf in visible(tree)} == {"Scout"}
    window.oc_class_filter.setCurrentIndex(0)
    assert len(visible(tree)) == everything

    window.combo_oc_filter.setCurrentText("Unforged")
    assert visible(tree) == []  # the sample save has nothing acquired but unforged


def test_season_picker(editor):
    main, window, save = editor
    # the sample only has an entry for season 1, so the newest season has nothing to edit
    assert window.season_picker.currentData() == seasons.SEASON_GUIDS[6]
    assert not window.season_xp.isEnabled()

    window.season_picker.setCurrentIndex(window.season_picker.findData(seasons.SEASON_GUIDS[1]))
    assert window.season_xp.isEnabled()
    window.season_lvl_text.setText("7")
    window.season_xp.setText("123")
    window.scrip_text.setText("45")
    main.save_changes()
    assert seasons.read_season(save.read_bytes(), seasons.SEASON_GUIDS[1]) == {"xp": 7 * 5000 + 123, "scrip": 45}


def test_cancelling_the_open_dialog_keeps_the_open_save(editor, monkeypatch):
    main, window, save = editor
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: ("", "")))
    main.open_file()
    assert main.file_name == str(save)
    main.save_changes()  # still works
