from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QPlainTextEdit,
    QTreeWidgetItem,
    QListWidgetItem,
    QMenu,
    QLineEdit,
)
from PySide6.QtGui import QBrush, QColor, QCursor, QFocusEvent
from contextlib import contextmanager
from copy import deepcopy
import sys
import os
import struct
from pprint import pprint as pp
import json
import winreg
import campaigns
import schematics
import seasons
import theme
import ui_main


def data_path(name):
    """data files (guids.json, cosmetics.json, ...) sit next to the exe when frozen, in the working directory otherwise"""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), name)
    return name


class TextEditFocusChecking(QLineEdit):
    """
    Custom single-line text box to allow for event-driven updating of XP totals
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def focusOutEvent(self, e: QFocusEvent) -> None:
        # check for blank text
        box = self.objectName()
        if self.text() == "":
            return super().focusOutEvent(e)
        season = False
        value = int(self.text())

        if box.startswith("driller"):
            dwarf = "driller"
        elif box.startswith("engineer"):
            dwarf = "engineer"
        elif box.startswith("gunner"):
            dwarf = "gunner"
        elif box.startswith("scout"):
            dwarf = "scout"
        elif box.startswith("season"):
            season = True
        else:
            print("abandon all hope, ye who see this message")
            return super().focusOutEvent(e)
        # print(dwarf)

        if season:
            if box.endswith("xp"):
                if value >= 5000:
                    widget.season_xp.setText("4999")
                elif value < 0:
                    widget.season_xp.setText("0")
            elif box.endswith("lvl_text"):
                if value < 0:
                    widget.season_lvl_text.setText("0")
                elif value > 100:
                    widget.season_lvl_text.setText("100")
                    widget.season_xp.setText("0")
        else:
            # decide/calculate how to update based on which box was changed
            if box.endswith("xp"):  # total xp box changed
                # print('main xp')
                total = value
            elif box.endswith("text"):  # dwarf level box changed
                # print('level xp')
                xp, level, rem = get_dwarf_xp(dwarf)
                if xp_table[value - 1] + rem == xp:
                    total = xp
                else:
                    total = xp_table[value - 1]
            elif box.endswith("2"):  # xp for current level changed
                xp, level, rem = get_dwarf_xp(dwarf)
                total = xp_table[level - 1] + value

            update_xp(dwarf, total)  # update relevant xp fields

        return super().focusOutEvent(e)  # call any other stuff that might happen (?)


def get_dwarf_xp(dwarf):
    # gets the total xp, level, and progress to the next level (rem)
    if dwarf == "driller":
        total = int(widget.driller_xp.text())
        level = int(widget.driller_lvl_text.text())
        rem = int(widget.driller_xp_2.text())
    elif dwarf == "engineer":
        total = int(widget.engineer_xp.text())
        level = int(widget.engineer_lvl_text.text())
        rem = int(widget.engineer_xp_2.text())
    elif dwarf == "gunner":
        total = int(widget.gunner_xp.text())
        level = int(widget.gunner_lvl_text.text())
        rem = int(widget.gunner_xp_2.text())
    elif dwarf == "scout":
        total = int(widget.scout_xp.text())
        level = int(widget.scout_lvl_text.text())
        rem = int(widget.scout_xp_2.text())
    else:
        total = rem = level = -1

    return total, level, rem


def update_xp(dwarf, total_xp=0):
    # updates the xp fields for the specified dwarf with the new xp total
    if total_xp > 315000:  # max xp check
        total_xp = 315000
    level, remainder = xp_total_to_level(total_xp)  # transform XP total
    bad_dwarf = False  # check for possible weirdness
    if dwarf == "driller":
        total_box = widget.driller_xp
        level_box = widget.driller_lvl_text
        remainder_box = widget.driller_xp_2
    elif dwarf == "engineer":
        total_box = widget.engineer_xp
        level_box = widget.engineer_lvl_text
        remainder_box = widget.engineer_xp_2
    elif dwarf == "gunner":
        total_box = widget.gunner_xp
        level_box = widget.gunner_lvl_text
        remainder_box = widget.gunner_xp_2
    elif dwarf == "scout":
        total_box = widget.scout_xp
        level_box = widget.scout_lvl_text
        remainder_box = widget.scout_xp_2
    else:
        print("no valid dward specified")
        bad_dwarf = True

    if not bad_dwarf:  # update xp totals
        total_box.setText(str(total_xp))
        level_box.setText(str(level))
        remainder_box.setText(str(remainder))

    update_rank()


def update_rank():
    global stats
    global max_badges
    s_promo = (
        stats["xp"]["scout"]["promo"]
        if int(widget.scout_promo_box.currentIndex()) == max_badges
        else int(widget.scout_promo_box.currentIndex())
    )
    e_promo = (
        stats["xp"]["engineer"]["promo"]
        if int(widget.engineer_promo_box.currentIndex()) == max_badges
        else int(widget.engineer_promo_box.currentIndex())
    )
    g_promo = (
        stats["xp"]["gunner"]["promo"]
        if int(widget.gunner_promo_box.currentIndex()) == max_badges
        else int(widget.gunner_promo_box.currentIndex())
    )
    d_promo = (
        stats["xp"]["driller"]["promo"]
        if int(widget.driller_promo_box.currentIndex()) == max_badges
        else int(widget.driller_promo_box.currentIndex())
    )

    try:
        s_level = int(widget.scout_lvl_text.text())
        e_level = int(widget.engineer_lvl_text.text())
        g_level = int(widget.gunner_lvl_text.text())
        d_level = int(widget.driller_lvl_text.text())
        total_levels = (
            ((s_promo + e_promo + g_promo + d_promo) * 25)
            + s_level
            + e_level
            + g_level
            + d_level
            - 4
        )
        rank = total_levels // 3  # integer division
        rem = total_levels % 3
    except:
        rank = 1
        rem = 0

    try:
        title = rank_titles[rank]
    except:
        title = "Lord of the Deep"

    widget.classes_group.setTitle(f"Classes - Rank {rank+1} {rem}/3, {title}")


@Slot()
def open_file():
    global file_name
    global save_data
    previous_file_name = file_name
    # open file dialog box, start in steam install path if present
    file_name = QFileDialog.getOpenFileName(
        None,
        "Open Save File...",
        steam_path,
        "Player Save Files (*.sav);;All Files (*.*)",
    )[0]
    # print('about to open file')
    if not file_name:
        # dialog cancelled; keep whatever was previously open
        file_name = previous_file_name
        return

    widget.setWindowTitle(f"DRG Save Editor - {file_name}")  # window-dressing
    with open(file_name, "rb") as f:
        save_data = f.read()

    # make a backup of the save file in case of weirdness or bugs
    with open(f"{file_name}.old", "wb") as backup:
        backup.write(save_data)

    # print(f'opened: {file_name}')

    show_save()


def show_save():
    """fills the whole window from save_data"""
    global stats
    global forged_ocs
    global unacquired_ocs
    global unforged_ocs

    season_cache.clear()
    with filling():
        # enable widgets that don't work without a save file present
        widget.set_save_loaded(True)

        # initialize and populate the text fields
        stats = init_values(save_data)
        reset_values()
        update_rank()

        # print('before ocs')
        # parse save file and categorize weapon overclocks
        forged_ocs, unacquired_ocs, unforged_ocs = get_overclocks(save_data, guid_dict)
        # print('after ocs')

        # clear and initialize overclock tree view
        widget.overclock_tree.clear()
        overclock_tree = widget.overclock_tree.invisibleRootItem()
        build_oc_tree(overclock_tree, guid_dict)
        widget.overclock_tree.sortItems(0, Qt.SortOrder.AscendingOrder)

        # populate list of unforged ocs
        unforged_list = widget.unforged_list
        populate_unforged_list(unforged_list, unforged_ocs)
        filter_overclocks()
    mark_clean()


CLASS_ABBREVIATIONS = {"Driller": "D", "Engineer": "E", "Gunner": "G", "Scout": "S"}
CLASS_ORDER = list(CLASS_ABBREVIATIONS)


def overclock_category(entry):
    """the weapon an overclock is for or, for a cosmetic overclock, what kind it is in singular (Victory Pose)"""
    if not entry.get("cosmetic"):
        return entry["weapon"]
    kind = entry["weapon"].replace("Cosmetic - ", "", 1)
    return kind[:-1] if kind.endswith("s") else kind


class UnforgedItem(QListWidgetItem):
    """sorts weapon overclocks first, then cosmetic ones, each by class, category and name"""

    def __init__(self, text, sort_key):
        super().__init__(text)
        self.sort_key = sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key


def unforged_item(guid, entry):
    """a row of the unforged list: class initial, category, then the name, in the class's colour"""
    if not isinstance(entry, dict):  # an overclock we have no data for
        item = UnforgedItem(f"?  ·  Unknown overclock  ·  {guid[:8]}…", (2, 0, "", guid))
        item.setForeground(QBrush(QColor(theme.COLORS["muted"])))
        item.setToolTip(guid)
    else:
        category = overclock_category(entry)
        name = entry["name"]
        icon = theme.class_icon(entry["class"], 24)
        # the class's portrait leads the row; without the image the class initial does
        lead = "" if icon is not None else f"{CLASS_ABBREVIATIONS[entry['class']]}  ·  "
        item = UnforgedItem(
            f"{lead}{category}  ·  {name}",
            (
                1 if entry.get("cosmetic") else 0,
                CLASS_ORDER.index(entry["class"]),
                category.lower(),
                name.lower(),
            ),
        )
        if icon is not None:
            item.setIcon(icon)
        item.setForeground(QBrush(QColor(theme.CLASS_COLORS[entry["class"]])))
        item.setToolTip(f"{entry['class']} · {category}: {name}\n{guid}")
    item.setData(Qt.UserRole, guid)
    return item


def guid_of_list_item(item):
    return item.data(Qt.UserRole)


def populate_unforged_list(list_widget, unforged):
    # populates the list of acquired but unforged overclocks and cosmetics
    list_widget.clear()
    for k, v in unforged.items():
        list_widget.addItem(unforged_item(k, v))
    list_widget.sortItems()


def update_season_data():
    pass


def get_season_data(save_bytes):
    """the selected season's values, or None when this save has no entry for it"""
    return seasons.read_season(save_bytes, season_guid)


def saved_season(guid):
    """what the open save has for a season; read once, since this is asked for on every keystroke"""
    if guid not in season_cache:
        season_cache[guid] = seasons.read_season(save_data, guid)
    return season_cache[guid]


def season_changes():
    """{season guid: values} for every season whose values differ from the save"""
    changes = dict(season_edits)
    if widget.season_xp.isEnabled():  # the season on screen
        typed = season_values_on_screen()
        if typed != saved_season(season_guid):
            changes[season_guid] = typed
        else:
            changes.pop(season_guid, None)
    return changes


def season_values_on_screen():
    return {
        "xp": int(widget.season_xp.text() or 0)
        + xp_per_season_level * int(widget.season_lvl_text.text() or 0),
        "scrip": int(widget.scrip_text.text() or 0),
    }


def show_season(values):
    boxes = (widget.season_xp, widget.season_lvl_text, widget.scrip_text)
    for box in boxes:
        box.setEnabled(values is not None)
    if values is None:  # nothing to edit for a season the save has no entry for
        for box in boxes:
            box.setText("0")
        return
    widget.season_xp.setText(str(values["xp"] % xp_per_season_level))
    widget.season_lvl_text.setText(str(values["xp"] // xp_per_season_level))
    widget.scrip_text.setText(str(values["scrip"]))


@Slot()
def change_season(index):
    global season_guid
    new_guid = widget.season_picker.itemData(index)
    if new_guid is None or new_guid == season_guid:
        return
    if save_data:
        # keep what was typed for the season being left, if it differs from the save
        season_edits.clear()
        season_edits.update(season_changes())
        season_guid = new_guid
        show_season(season_edits.get(new_guid) or saved_season(new_guid))
        update_dirty()
    else:
        season_guid = new_guid


def get_resources(save_bytes):
    # extracts the resource counts from the save file
    # print('getting resources')
    # resource GUIDs
    global resource_guids
    resources = deepcopy(resource_guids)
    guid_length = 16  # length of GUIDs in bytes
    res_marker = (
        b"OwnedResources"  # marks the beginning of where resource values can be found
    )
    res_pos = save_bytes.find(res_marker)
    # print("getting resources")
    for k, v in resources.items():  # iterate through resource list
        # print(f"key: {k}, value: {v}")
        marker = bytes.fromhex(v)
        pos = (
            save_bytes.find(marker, res_pos) + guid_length
        )  # search for the matching GUID
        end_pos = pos + 4  # offset for the actual value
        # extract and unpack the value
        temp = save_bytes[pos:end_pos]
        unp = struct.unpack("f", temp)
        resources[k] = int(unp[0])  # save resource count

    # pp(resources)  # pretty printing for some reason
    return resources


def get_xp(save_bytes):
    # print('getting xp')
    en_marker = b"\x85\xEF\x62\x6C\x65\xF1\x02\x4A\x8D\xFE\xB5\xD0\xF3\x90\x9D\x2E\x03\x00\x00\x00\x58\x50"
    sc_marker = b"\x30\xD8\xEA\x17\xD8\xFB\xBA\x4C\x95\x30\x6D\xE9\x65\x5C\x2F\x8C\x03\x00\x00\x00\x58\x50"
    dr_marker = b"\x9E\xDD\x56\xF1\xEE\xBC\xC5\x48\x8D\x5B\x5E\x5B\x80\xB6\x2D\xB4\x03\x00\x00\x00\x58\x50"
    gu_marker = b"\xAE\x56\xE1\x80\xFE\xC0\xC4\x4D\x96\xFA\x29\xC2\x83\x66\xB9\x7B\x03\x00\x00\x00\x58\x50"

    # start_offset = 0
    xp_offset = 48
    eng_xp_pos = save_bytes.find(en_marker) + xp_offset
    scout_xp_pos = save_bytes.find(sc_marker) + xp_offset
    drill_xp_pos = save_bytes.find(dr_marker) + xp_offset
    gun_xp_pos = save_bytes.find(gu_marker) + xp_offset

    eng_xp = struct.unpack("i", save_bytes[eng_xp_pos : eng_xp_pos + 4])[0]
    scout_xp = struct.unpack("i", save_bytes[scout_xp_pos : scout_xp_pos + 4])[0]
    drill_xp = struct.unpack("i", save_bytes[drill_xp_pos : drill_xp_pos + 4])[0]
    gun_xp = struct.unpack("i", save_bytes[gun_xp_pos : gun_xp_pos + 4])[0]

    num_promo_offset = 108
    eng_num_promo = struct.unpack(
        "i",
        save_bytes[eng_xp_pos + num_promo_offset : eng_xp_pos + num_promo_offset + 4],
    )[0]
    scout_num_promo = struct.unpack(
        "i",
        save_bytes[
            scout_xp_pos + num_promo_offset : scout_xp_pos + num_promo_offset + 4
        ],
    )[0]
    drill_num_promo = struct.unpack(
        "i",
        save_bytes[
            drill_xp_pos + num_promo_offset : drill_xp_pos + num_promo_offset + 4
        ],
    )[0]
    gun_num_promo = struct.unpack(
        "i",
        save_bytes[gun_xp_pos + num_promo_offset : gun_xp_pos + num_promo_offset + 4],
    )[0]

    xp_dict = {
        "engineer": {"xp": eng_xp, "promo": eng_num_promo},
        "scout": {"xp": scout_xp, "promo": scout_num_promo},
        "driller": {"xp": drill_xp, "promo": drill_num_promo},
        "gunner": {"xp": gun_xp, "promo": gun_num_promo},
    }
    # pp(xp_dict)
    return xp_dict


def xp_total_to_level(xp):
    for i in xp_table:
        if xp < i:
            level = xp_table.index(i)
            remainder = xp - xp_table[level - 1]
            return (level, remainder)
    return (25, 0)


def get_credits(save_bytes):
    marker = b"Credits"
    offset = 33
    pos = save_bytes.find(marker) + offset
    money = struct.unpack("i", save_bytes[pos : pos + 4])[0]

    return money


def get_perk_points(save_bytes):
    marker = b"PerkPoints"
    offset = 36
    if save_bytes.find(marker) == -1:
        perk_points = 0
    else:
        pos = save_bytes.find(marker) + offset
        perk_points = struct.unpack("i", save_bytes[pos : pos + 4])[0]

    return perk_points


def build_oc_dict(guid_dict):
    overclocks = dict()

    for v in guid_dict.values():
        try:
            overclocks.update({v["class"]: dict()})
        except:
            pass

    for v in guid_dict.values():
        try:
            overclocks[v["class"]].update({v["weapon"]: dict()})
        except:
            pass

    for k, v in guid_dict.items():
        try:
            overclocks[v["class"]][v["weapon"]].update({v["name"]: k})
        except:
            pass

    return overclocks


class OcItem(QTreeWidgetItem):
    """sorts by name, ignoring case, with the cosmetic groups after the weapons"""

    def __lt__(self, other):
        tree = self.treeWidget()
        if tree is not None and tree.sortColumn() != 0:
            return super().__lt__(other)

        def key(item):
            return (item.text(0).startswith("Cosmetic - "), item.text(0).lower())

        return key(self) < key(other)


def build_oc_tree(tree, source_dict):
    oc_dict = build_oc_dict(source_dict)
    # entry = OcItem(None)
    for char, weapons in oc_dict.items():
        # dwarves[dwarf] = QTreeWidgetItem(tree)
        char_entry = OcItem(None)
        char_entry.setText(0, char)
        for weapon, oc_names in weapons.items():
            weapon_entry = OcItem(None)
            weapon_entry.setText(0, weapon)
            for name, uuid in oc_names.items():
                oc_entry = OcItem(None)
                oc_entry.setText(0, name)
                oc_entry.setText(1, source_dict[uuid]["status"])
                oc_entry.setText(2, uuid)
                weapon_entry.addChild(oc_entry)
            char_entry.addChild(weapon_entry)
        tree.addChild(char_entry)


def get_overclocks(save_bytes, guid_source):
    search_term = b"ForgedSchematics"
    search_end = b"SkinFixupCounter"
    pos = save_bytes.find(search_term)
    end_pos = save_bytes.find(search_end)
    if end_pos == -1:
        search_end = b"bFirstSchematicMessageShown"
        end_pos = save_bytes.find(search_end)

    for i in guid_source.values():
        i["status"] = "Unacquired"

    guids = deepcopy(guid_source)
    if pos > 0:
        oc_data = save_bytes[pos:end_pos]
        oc_list_offset = 141

        # print(f'pos: {pos}, end_pos: {end_pos}')
        # print(f'owned_pos: {owned}, diff: {owned-pos}')
        # unforged = True if oc_data.find(b'Owned') else False
        if oc_data.find(b"Owned") > 0:
            unforged = True
        else:
            unforged = False
        # print(unforged) # bool
        num_forged = struct.unpack("i", save_bytes[pos + 63 : pos + 67])[0]
        forged = dict()
        # print(num_forged)

        for i in range(num_forged):
            uuid = (
                save_bytes[
                    pos
                    + oc_list_offset
                    + (i * 16) : pos
                    + oc_list_offset
                    + (i * 16)
                    + 16
                ]
                .hex()
                .upper()
            )
            try:
                a = guids[uuid]
                guid_source[uuid]["status"] = "Forged"
                a["status"] = "Forged"
                del guids[uuid]
                forged.update({uuid: a})

                # print('success')
            except Exception as e:
                # print(f'Error: {e}')
                pass

        # print('after forged extraction')
        if unforged:
            unforged = dict()
            # print('in unforged loop')
            num_pos = save_bytes.find(b"Owned", pos) + 62
            num_unforged = struct.unpack("i", save_bytes[num_pos : num_pos + 4])[0]
            unforged_pos = num_pos + 77
            for i in range(num_unforged):
                uuid = (
                    save_bytes[unforged_pos + (i * 16) : unforged_pos + (i * 16) + 16]
                    .hex()
                    .upper()
                )
                try:
                    unforged.update({uuid: guids[uuid]})
                    guid_source[uuid]["status"] = "Unforged"
                    unforged[uuid]["status"] = "Unforged"
                except KeyError:
                    unforged.update({uuid: "Cosmetic"})
        else:
            unforged = dict()
    else:
        forged = dict()
        unforged = dict()

    # print('after unforged extraction')
    # print(f'unforged: {unforged}')
    # forged OCs, unacquired OCs, unforged OCs
    return (forged, guids, unforged)


STATUSES = ("Forged", "Unforged", "Unacquired")


def status_summary(counts):
    total = sum(counts.values())
    text = f'{counts["Forged"]}/{total} forged'
    if counts["Unforged"]:
        text += f' · {counts["Unforged"]} unforged'
    return text


def filter_overclocks(*_):
    """applies the search and the class, kind and status filters, and refreshes status colours and counts"""
    status_filter = widget.combo_oc_filter.currentText() or "All"
    class_filter = widget.oc_class_filter.currentText()
    kind_filter = widget.oc_kind_filter.currentText()
    query = widget.oc_search.text().strip().lower()
    muted = QBrush(QColor(theme.COLORS["muted"]))

    totals = dict.fromkeys(STATUSES, 0)
    shown = 0
    root = widget.overclock_tree.invisibleRootItem()
    for i in range(root.childCount()):
        class_item = root.child(i)
        class_counts = dict.fromkeys(STATUSES, 0)
        class_shown = 0
        for j in range(class_item.childCount()):
            group = class_item.child(j)
            group_counts = dict.fromkeys(STATUSES, 0)
            group_shown = 0
            for k in range(group.childCount()):
                leaf = group.child(k)
                guid = leaf.text(2)
                entry = guid_dict.get(guid, {})
                status = entry.get("status", leaf.text(1))
                leaf.setText(1, status)
                leaf.setForeground(1, QBrush(QColor(theme.STATUS_COLORS[status])))
                leaf.setForeground(2, muted)
                group_counts[status] += 1

                visible = (
                    (status_filter == "All" or status == status_filter)
                    and (class_filter == "All classes" or class_item.text(0) == class_filter)
                    and (
                        kind_filter.startswith("All")
                        or (kind_filter == "Cosmetic overclocks") == bool(entry.get("cosmetic"))
                    )
                    and (
                        not query
                        or query in f"{class_item.text(0)} {group.text(0)} {leaf.text(0)} {guid}".lower()
                    )
                )
                leaf.setHidden(not visible)
                group_shown += visible

            group.setText(1, status_summary(group_counts))
            group.setForeground(1, muted)
            group.setHidden(group_shown == 0)
            if query and group_shown:
                group.setExpanded(True)
            class_shown += group_shown
            for status in STATUSES:
                class_counts[status] += group_counts[status]

        class_item.setText(1, status_summary(class_counts))
        class_item.setForeground(1, muted)
        class_item.setHidden(class_shown == 0)
        if query and class_shown:
            class_item.setExpanded(True)
        shown += class_shown
        for status in STATUSES:
            totals[status] += class_counts[status]

    widget.oc_counts.setText(
        f'{shown} of {sum(totals.values())} shown · {totals["Forged"]} forged · '
        f'{totals["Unforged"]} unforged · {totals["Unacquired"]} unacquired'
    )


def selected_leaves(tree):
    """the overclocks that are selected, counting a selected weapon, cosmetic group or class as all of its shown items"""
    leaves, seen = [], set()

    def collect(item):
        if item.isHidden():
            return
        if item.childCount() == 0:
            if item.text(2) and item.text(2) not in seen:
                seen.add(item.text(2))
                leaves.append(item)
            return
        for n in range(item.childCount()):
            collect(item.child(n))

    for item in tree.selectedItems():
        collect(item)
    return leaves


@Slot()
def oc_ctx_menu(pos):
    # oc_context_menu = make_oc_context_menu()
    # global oc_context_menu
    ctx_menu = QMenu(widget.overclock_tree)
    add_act = ctx_menu.addAction("Add Core(s) to Inventory")
    global_pos = QCursor().pos()
    action = ctx_menu.exec(global_pos)
    if action == add_act:
        add_cores()

    # add_act.triggered.connect(add_cores())


@Slot()
def add_cores():
    global unforged_ocs
    global unacquired_ocs
    items_to_add = list()
    for leaf in selected_leaves(widget.overclock_tree):
        guid = leaf.text(2)
        if guid_dict[guid]["status"] != "Unacquired":
            continue
        guid_dict[guid]["status"] = "Unforged"
        unforged_ocs[guid] = guid_dict[guid]
        unacquired_ocs.pop(guid, None)
        items_to_add.append(unforged_item(guid, guid_dict[guid]))

    core_list = widget.unforged_list
    for item in items_to_add:
        core_list.addItem(item)

    core_list.sortItems()
    filter_overclocks()
    widget.statusBar().showMessage(
        f"Added {len(items_to_add)} to the unforged list. Save to write them into your save."
        if items_to_add
        else "Nothing to add: select unacquired overclocks first.",
        6000,
    )
    update_dirty()


@contextmanager
def filling():
    """while the window is being filled from a save the boxes change, but not because the user edited anything"""
    global loading
    loading += 1
    try:
        yield
    finally:
        loading -= 1


def snapshot():
    """everything that would be written, to tell whether anything differs from the last open or save"""
    try:
        values = get_values()
        values.pop("season")  # compared per season below
        return (
            json.dumps(values, sort_keys=True),
            tuple(sorted(unforged_ocs)),
            json.dumps(campaign_state, sort_keys=True),
            json.dumps(season_changes(), sort_keys=True),
        )
    except Exception:  # a box is empty or half typed
        return None


def update_dirty(*_):
    if loading or not file_name:
        return
    current = snapshot()
    widget.set_dirty(current is None or current != saved_snapshot)


def mark_clean():
    global saved_snapshot
    saved_snapshot = snapshot()
    widget.set_dirty(False)


@Slot()
def save_changes():
    if not file_name:
        return  # no save file open yet
    changes = get_values()
    changes["unforged"] = unforged_ocs
    # pp(changes)
    save_file = make_save_file(file_name, changes)
    # the acquired-but-unforged overclocks and cosmetics, as edited in the Overclocks panel
    save_file = schematics.apply_unforged(save_file, list(unforged_ocs))
    # the season on screen, plus any other season edited before switching away from it
    for guid, values in {**season_edits, season_guid: changes["season"]}.items():
        save_file = seasons.apply_season(save_file, guid, values["xp"], values["scrip"])
    season_cache.clear()
    if campaigns_dirty and campaign_state is not None:
        save_file = campaigns.apply_state(save_file, campaign_state)
    with open(file_name, "wb") as f:
        f.write(save_file)

    # what was just written is now the save: Reset goes back to it and nothing is unsaved
    global save_data
    global stats
    save_data = save_file
    season_cache.clear()
    stats = init_values(save_data)
    reset_values()
    widget.statusBar().showMessage("Saved.", 5000)


def make_save_file(file_path, change_data):
    with open(file_path, "rb") as f:
        save_data = f.read()

    new_values = change_data
    global resource_guids
    global season_guid
    # write resources
    resource_bytes = list()
    res_guids = deepcopy(resource_guids)
    resources = {
        "yeast": new_values["brewing"]["yeast"],
        "starch": new_values["brewing"]["starch"],
        "barley": new_values["brewing"]["barley"],
        "bismor": new_values["minerals"]["bismor"],
        "enor": new_values["minerals"]["enor"],
        "malt": new_values["brewing"]["malt"],
        "umanite": new_values["minerals"]["umanite"],
        "jadiz": new_values["minerals"]["jadiz"],
        "croppa": new_values["minerals"]["croppa"],
        "magnite": new_values["minerals"]["magnite"],
        "error": new_values["misc"]["error"],
        "cores": new_values["misc"]["cores"],
        "data": new_values["misc"]["data"],
        "phazyonite": new_values["misc"]["phazyonite"],
    }

    res_marker = b"OwnedResources"
    res_pos = save_data.find(res_marker) + 85
    res_length = struct.unpack("i", save_data[res_pos - 4 : res_pos])[0] * 20
    res_bytes = save_data[res_pos : res_pos + res_length]

    for k, v in resources.items():
        if res_bytes.find(bytes.fromhex(res_guids[k])) > -1:
            pos = res_bytes.find(bytes.fromhex(res_guids[k]))
            res_bytes = (
                res_bytes[: pos + 16] + struct.pack("f", v) + res_bytes[pos + 20 :]
            )
            # print(
            #     f'res: {k}, pos: {pos}, guid: {res_guids[k]}, val: {v}, v bytes: {struct.pack("f", v)}'
            # )

    # print(res_bytes.hex().upper())

    save_data = save_data[:res_pos] + res_bytes + save_data[res_pos + res_length :]

    # write credits
    cred_marker = b"Credits"
    cred_pos = save_data.find(cred_marker) + 33
    cred_bytes = struct.pack("i", new_values["misc"]["credits"])
    save_data = save_data[:cred_pos] + cred_bytes + save_data[cred_pos + 4 :]

    # write perk points
    if new_values["misc"]["perks"] > 0:
        perks_marker = b"PerkPoints"
        perks_bytes = struct.pack("i", new_values["misc"]["perks"])
        if save_data.find(perks_marker) != -1:
            perks_pos = save_data.find(perks_marker) + 36
            save_data = save_data[:perks_pos] + perks_bytes + save_data[perks_pos + 4 :]
        else:
            perks_entry = (
                b"\x0B\x00\x00\x00\x50\x65\x72\x6B\x50\x6F\x69\x6E\x74\x73\x00\x0C\x00\x00\x00\x49\x6E\x74\x50\x72\x6F\x70\x65\x72\x74\x79\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00"
                + perks_bytes
            )
            perks_pos = save_data.find(
                b"\x11\x00\x00\x00\x55\x6E\x4C\x6F\x63\x6B\x65\x64\x4D\x69\x73\x73\x69\x6F\x6E\x73\x00\x0E"
            )
            save_data = (
                save_data[:perks_pos] + perks_entry + save_data[perks_pos:]
            )  # inserting data, not overwriting
    # print(f'2. {len(save_data)}')
    # write XP
    en_marker = b"\x85\xEF\x62\x6C\x65\xF1\x02\x4A\x8D\xFE\xB5\xD0\xF3\x90\x9D\x2E\x03\x00\x00\x00\x58\x50"
    sc_marker = b"\x30\xD8\xEA\x17\xD8\xFB\xBA\x4C\x95\x30\x6D\xE9\x65\x5C\x2F\x8C\x03\x00\x00\x00\x58\x50"
    dr_marker = b"\x9E\xDD\x56\xF1\xEE\xBC\xC5\x48\x8D\x5B\x5E\x5B\x80\xB6\x2D\xB4\x03\x00\x00\x00\x58\x50"
    gu_marker = b"\xAE\x56\xE1\x80\xFE\xC0\xC4\x4D\x96\xFA\x29\xC2\x83\x66\xB9\x7B\x03\x00\x00\x00\x58\x50"
    offset = 48
    eng_xp_pos = save_data.find(en_marker) + offset
    scout_xp_pos = save_data.find(sc_marker) + offset
    drill_xp_pos = save_data.find(dr_marker) + offset
    gun_xp_pos = save_data.find(gu_marker) + offset

    eng_xp_bytes = struct.pack("i", new_values["xp"]["engineer"]["xp"])
    scout_xp_bytes = struct.pack("i", new_values["xp"]["scout"]["xp"])
    drill_xp_bytes = struct.pack("i", new_values["xp"]["driller"]["xp"])
    gun_xp_bytes = struct.pack("i", new_values["xp"]["gunner"]["xp"])

    promo_offset = 108
    levels_per_promo = 25
    promo_levels_offset = 56
    eng_promo_pos = eng_xp_pos + promo_offset
    scout_promo_pos = scout_xp_pos + promo_offset
    drill_promo_pos = drill_xp_pos + promo_offset
    gun_promo_pos = gun_xp_pos + promo_offset

    eng_promo_bytes = struct.pack("i", new_values["xp"]["engineer"]["promo"])
    eng_promo_level_bytes = struct.pack(
        "i", new_values["xp"]["engineer"]["promo"] * levels_per_promo
    )
    scout_promo_bytes = struct.pack("i", new_values["xp"]["scout"]["promo"])
    scout_promo_level_bytes = struct.pack(
        "i", new_values["xp"]["scout"]["promo"] * levels_per_promo
    )
    drill_promo_bytes = struct.pack("i", new_values["xp"]["driller"]["promo"])
    drill_promo_level_bytes = struct.pack(
        "i", new_values["xp"]["driller"]["promo"] * levels_per_promo
    )
    gun_promo_bytes = struct.pack("i", new_values["xp"]["gunner"]["promo"])
    gun_promo_level_bytes = struct.pack(
        "i", new_values["xp"]["gunner"]["promo"] * levels_per_promo
    )

    save_data = save_data[:eng_xp_pos] + eng_xp_bytes + save_data[eng_xp_pos + 4 :]
    save_data = (
        save_data[:eng_promo_pos] + eng_promo_bytes + save_data[eng_promo_pos + 4 :]
    )
    save_data = (
        save_data[: eng_promo_pos + promo_levels_offset]
        + eng_promo_level_bytes
        + save_data[eng_promo_pos + promo_levels_offset + 4 :]
    )

    save_data = (
        save_data[:scout_xp_pos] + scout_xp_bytes + save_data[scout_xp_pos + 4 :]
    )
    save_data = (
        save_data[:scout_promo_pos]
        + scout_promo_bytes
        + save_data[scout_promo_pos + 4 :]
    )
    save_data = (
        save_data[: scout_promo_pos + promo_levels_offset]
        + scout_promo_level_bytes
        + save_data[scout_promo_pos + promo_levels_offset + 4 :]
    )

    save_data = (
        save_data[:drill_xp_pos] + drill_xp_bytes + save_data[drill_xp_pos + 4 :]
    )
    save_data = (
        save_data[:drill_promo_pos]
        + drill_promo_bytes
        + save_data[drill_promo_pos + 4 :]
    )
    save_data = (
        save_data[: drill_promo_pos + promo_levels_offset]
        + drill_promo_level_bytes
        + save_data[drill_promo_pos + promo_levels_offset + 4 :]
    )

    save_data = save_data[:gun_xp_pos] + gun_xp_bytes + save_data[gun_xp_pos + 4 :]
    save_data = (
        save_data[:gun_promo_pos] + gun_promo_bytes + save_data[gun_promo_pos + 4 :]
    )
    save_data = (
        save_data[: gun_promo_pos + promo_levels_offset]
        + gun_promo_level_bytes
        + save_data[gun_promo_pos + promo_levels_offset + 4 :]
    )
    # print(f'3. {len(save_data)}')
    return save_data
    # with open(f"{file_name}", "wb") as t:
    #     t.write(save_data)


@Slot()
def set_all_25():
    update_xp("driller", 315000)
    update_xp("engineer", 315000)
    update_xp("gunner", 315000)
    update_xp("scout", 315000)


@Slot()
def reset_values():
    """the Reset action: back to what the save had"""
    with filling():
        restore_values()
    mark_clean()


def restore_values():
    global stats
    global unforged_ocs
    global unacquired_ocs
    global forged_ocs
    global max_badges
    global xp_per_season_level
    # print('reset values')
    widget.bismor_text.setText(str(stats["minerals"]["bismor"]))
    widget.enor_text.setText(str(stats["minerals"]["enor"]))
    widget.jadiz_text.setText(str(stats["minerals"]["jadiz"]))
    widget.croppa_text.setText(str(stats["minerals"]["croppa"]))
    widget.magnite_text.setText(str(stats["minerals"]["magnite"]))
    widget.umanite_text.setText(str(stats["minerals"]["umanite"]))
    # print('after minerals')

    widget.yeast_text.setText(str(stats["brewing"]["yeast"]))
    widget.starch_text.setText(str(stats["brewing"]["starch"]))
    widget.malt_text.setText(str(stats["brewing"]["malt"]))
    widget.barley_text.setText(str(stats["brewing"]["barley"]))
    # print('after brewing')

    widget.error_text.setText(str(stats["misc"]["error"]))
    widget.core_text.setText(str(stats["misc"]["cores"]))
    widget.credits_text.setText(str(stats["misc"]["credits"]))
    widget.perk_text.setText(str(stats["misc"]["perks"]))
    widget.data_text.setText(str(stats["misc"]["data"]))
    widget.phazy_text.setText(str(stats["misc"]["phazyonite"]))
    # print('after misc')

    widget.driller_xp.setText(str(stats["xp"]["driller"]["xp"]))
    d_xp = xp_total_to_level(stats["xp"]["driller"]["xp"])
    widget.driller_lvl_text.setText(str(d_xp[0]))
    widget.driller_xp_2.setText(str(d_xp[1]))
    widget.driller_promo_box.setCurrentIndex(
        stats["xp"]["driller"]["promo"]
        if stats["xp"]["driller"]["promo"] < max_badges
        else max_badges
    )
    # print('after driller')

    widget.engineer_xp.setText(str(stats["xp"]["engineer"]["xp"]))
    e_xp = xp_total_to_level(stats["xp"]["engineer"]["xp"])
    widget.engineer_lvl_text.setText(str(e_xp[0]))
    widget.engineer_xp_2.setText(str(e_xp[1]))
    widget.engineer_promo_box.setCurrentIndex(
        stats["xp"]["engineer"]["promo"]
        if stats["xp"]["engineer"]["promo"] < max_badges
        else max_badges
    )
    # print('after engineer')

    widget.gunner_xp.setText(str(stats["xp"]["gunner"]["xp"]))
    g_xp = xp_total_to_level(stats["xp"]["gunner"]["xp"])
    widget.gunner_lvl_text.setText(str(g_xp[0]))
    widget.gunner_xp_2.setText(str(g_xp[1]))
    widget.gunner_promo_box.setCurrentIndex(
        stats["xp"]["gunner"]["promo"]
        if stats["xp"]["gunner"]["promo"] < max_badges
        else max_badges
    )
    # print('after gunner')

    widget.scout_xp.setText(str(stats["xp"]["scout"]["xp"]))
    s_xp = xp_total_to_level(stats["xp"]["scout"]["xp"])
    widget.scout_lvl_text.setText(str(s_xp[0]))
    widget.scout_xp_2.setText(str(s_xp[1]))
    widget.scout_promo_box.setCurrentIndex(
        stats["xp"]["scout"]["promo"]
        if stats["xp"]["scout"]["promo"] < max_badges
        else max_badges
    )
    # print('after scout')

    forged_ocs, unacquired_ocs, unforged_ocs = get_overclocks(save_data, guid_dict)
    unforged_list = widget.unforged_list
    populate_unforged_list(unforged_list, unforged_ocs)

    filter_overclocks()
    update_rank()

    # reset season data
    season_edits.clear()
    stats["season"] = get_season_data(save_data)
    show_season(stats["season"])

    load_campaign_state()


def load_campaign_state():
    # campaign edits are kept as a small state dict and only written into the save on save
    global campaign_state
    global campaign_baseline
    global campaigns_dirty
    try:
        campaign_state = campaigns.read_state(save_data)
    except Exception as e:  # unreadable or very old save: just leave campaigns alone
        print(f"campaigns unavailable: {e}")
        campaign_state = None
    campaign_baseline = deepcopy(campaign_state)
    campaigns_dirty = False
    widget.campaign_page.load(campaign_state)
    widget.set_assignments_available(campaign_state is not None)


@Slot(dict)
def campaigns_changed(new_state):
    global campaign_state
    global campaigns_dirty
    campaign_state = new_state
    campaigns_dirty = new_state != campaign_baseline
    update_dirty()


@Slot()
def add_crafting_mats():
    cost = {
        "bismor": 0,
        "croppa": 0,
        "jadiz": 0,
        "enor": 0,
        "magnite": 0,
        "umanite": 0,
        "credits": 0,
    }
    for k, v in unforged_ocs.items():
        print(k, v)
        try:
            for i in v["cost"].keys():
                cost[i] += v["cost"][i]
        except:
            print(f"Cosmetic")
    print(cost)
    add_resources(cost)


def add_resources(res_dict):
    # res_dict is {'bismor': 123, 'credits': 10000, ...}
    try:
        widget.bismor_text.setText(
            str(int(widget.bismor_text.text()) + res_dict["bismor"])
        )
    except:
        pass
    try:
        widget.croppa_text.setText(
            str(int(widget.croppa_text.text()) + res_dict["croppa"])
        )
    except:
        pass
    try:
        widget.enor_text.setText(str(int(widget.enor_text.text()) + res_dict["enor"]))
    except:
        pass
    try:
        widget.jadiz_text.setText(
            str(int(widget.jadiz_text.text()) + res_dict["jadiz"])
        )
    except:
        pass
    try:
        widget.magnite_text.setText(
            str(int(widget.magnite_text.text()) + res_dict["magnite"])
        )
    except:
        pass
    try:
        widget.umanite_text.setText(
            str(int(widget.umanite_text.text()) + res_dict["umanite"])
        )
    except:
        pass
    try:
        widget.barley_text.setText(
            str(int(widget.barley_text.text()) + res_dict["barley"])
        )
    except:
        pass
    try:
        widget.yeast_text.setText(
            str(int(widget.yeast_text.text()) + res_dict["yeast"])
        )
    except:
        pass
    try:
        widget.malt_text.setText(str(int(widget.malt_text.text()) + res_dict["malt"]))
    except:
        pass
    try:
        widget.starch_text.setText(
            str(int(widget.starch_text.text()) + res_dict["starch"])
        )
    except:
        pass
    try:
        widget.error_text.setText(
            str(int(widget.error_text.text()) + res_dict["error"])
        )
    except:
        pass
    try:
        widget.core_text.setText(str(int(widget.core_text.text()) + res_dict["cores"]))
    except:
        pass
    try:
        widget.credits_text.setText(
            str(int(widget.credits_text.text()) + res_dict["credits"])
        )
    except:
        pass


def init_values(save_data):
    # global stats
    # print('init values')
    stats["xp"] = get_xp(save_data)
    stats["misc"] = dict()
    stats["misc"]["credits"] = get_credits(save_data)
    stats["misc"]["perks"] = get_perk_points(save_data)
    resources = get_resources(save_data)
    stats["misc"]["cores"] = resources["cores"]
    stats["misc"]["error"] = resources["error"]
    stats["misc"]["data"] = resources["data"]
    stats["misc"]["phazyonite"] = resources["phazyonite"]
    stats["minerals"] = dict()
    stats["minerals"]["bismor"] = resources["bismor"]
    stats["minerals"]["enor"] = resources["enor"]
    stats["minerals"]["jadiz"] = resources["jadiz"]
    stats["minerals"]["croppa"] = resources["croppa"]
    stats["minerals"]["magnite"] = resources["magnite"]
    stats["minerals"]["umanite"] = resources["umanite"]
    stats["brewing"] = dict()
    stats["brewing"]["yeast"] = resources["yeast"]
    stats["brewing"]["starch"] = resources["starch"]
    stats["brewing"]["barley"] = resources["barley"]
    stats["brewing"]["malt"] = resources["malt"]
    stats["season"] = get_season_data(save_data)

    # print('printing stats')
    # pp(stats)
    return stats


def get_values():
    global stats
    global max_badges
    xp_per_season_level = 5000

    ns = dict()
    ns["minerals"] = dict()
    ns["brewing"] = dict()
    ns["misc"] = dict()
    ns["xp"] = {
        "driller": dict(),
        "gunner": dict(),
        "scout": dict(),
        "engineer": dict(),
    }

    ns["minerals"]["bismor"] = int(widget.bismor_text.text())
    ns["minerals"]["croppa"] = int(widget.croppa_text.text())
    ns["minerals"]["enor"] = int(widget.enor_text.text())
    ns["minerals"]["jadiz"] = int(widget.jadiz_text.text())
    ns["minerals"]["magnite"] = int(widget.magnite_text.text())
    ns["minerals"]["umanite"] = int(widget.umanite_text.text())

    ns["brewing"]["yeast"] = int(widget.yeast_text.text())
    ns["brewing"]["starch"] = int(widget.starch_text.text())
    ns["brewing"]["malt"] = int(widget.malt_text.text())
    ns["brewing"]["barley"] = int(widget.barley_text.text())

    ns["xp"]["driller"]["xp"] = int(widget.driller_xp.text())
    ns["xp"]["engineer"]["xp"] = int(widget.engineer_xp.text())
    ns["xp"]["gunner"]["xp"] = int(widget.gunner_xp.text())
    ns["xp"]["scout"]["xp"] = int(widget.scout_xp.text())

    driller_promo = int(widget.driller_promo_box.currentIndex())
    gunner_promo = int(widget.gunner_promo_box.currentIndex())
    scout_promo = int(widget.scout_promo_box.currentIndex())
    engineer_promo = int(widget.engineer_promo_box.currentIndex())

    ns["xp"]["driller"]["promo"] = (
        driller_promo if driller_promo < max_badges else stats["xp"]["driller"]["promo"]
    )
    ns["xp"]["engineer"]["promo"] = (
        engineer_promo
        if engineer_promo < max_badges
        else stats["xp"]["engineer"]["promo"]
    )
    ns["xp"]["gunner"]["promo"] = (
        gunner_promo if gunner_promo < max_badges else stats["xp"]["gunner"]["promo"]
    )
    ns["xp"]["scout"]["promo"] = (
        scout_promo if scout_promo < max_badges else stats["xp"]["scout"]["promo"]
    )

    ns["misc"]["error"] = int(widget.error_text.text())
    ns["misc"]["cores"] = int(widget.core_text.text())
    ns["misc"]["credits"] = int(widget.credits_text.text())
    ns["misc"]["perks"] = int(widget.perk_text.text())
    ns["misc"]["data"] = int(widget.data_text.text())
    ns["misc"]["phazyonite"] = int(widget.phazy_text.text())

    ns["season"] = season_values_on_screen()

    return ns


@Slot()
def remove_selected_ocs():
    global unforged_ocs
    global unacquired_ocs
    global file_name
    list_items = widget.unforged_list.selectedItems()
    items_to_remove = list()
    for i in list_items:
        items_to_remove.append(guid_of_list_item(i))
        item = widget.unforged_list.row(i)
        widget.unforged_list.takeItem(item)

    remove_ocs(items_to_remove)


def remove_ocs(oc_list):
    global unforged_ocs
    global unacquired_ocs
    global guid_dict

    for i in oc_list:
        oc = unforged_ocs.pop(i)
        if isinstance(oc, dict):
            oc["status"] = "Unacquired"
            guid_dict[i]["status"] = "Unacquired"
            unacquired_ocs[i] = oc
        # overclocks we have no data for are stored as the string "Cosmetic" and aren't in the overclock data,
        # so they're just dropped from the unforged list

    filter_overclocks()
    update_dirty()


@Slot()
def remove_all_ocs():
    global unforged_ocs
    # unforged_ocs = dict()
    items_to_remove = list()
    unforged_list = widget.unforged_list
    for i in range(unforged_list.count()):
        item = unforged_list.item(i)
        items_to_remove.append(guid_of_list_item(item))

    remove_ocs(items_to_remove)
    unforged_list.clear()


# xp_table[i] = XP needed for level i+1
xp_table = [
    0,
    3000,
    7000,
    12000,
    18000,
    25000,
    33000,
    42000,
    52000,
    63000,
    75000,
    88000,
    102000,
    117000,
    132500,
    148500,
    165000,
    182000,
    199500,
    217500,
    236000,
    255000,
    274500,
    294500,
    315000,
]
# ordered list of the promotion ranks (low -> high)
promo_ranks = [
    "None",
    "Bronze 1",
    "Bronze 2",
    "Bronze 3",
    "Silver 1",
    "Silver 2",
    "Silver 3",
    "Gold 1",
    "Gold 2",
    "Gold 3",
    "Platinum 1",
    "Platinum 2",
    "Platinum 3",
    "Diamond 1",
    "Diamond 2",
    "Diamond 3",
    "Legendary 1",
    "Legendary 2",
    "Legendary 3",
    "Legendary 3+",
]
max_badges = len(promo_ranks) - 1

# ordered list of player rank titles (low -> high)
rank_titles = [
    "Greenbeard",
    "Rock Hauler",
    "Cave Runner",
    "Stone Breaker",
    "Pit Delver",
    "Rookie Miner",
    "Rookie Miner",
    "Authorized Miner",
    "Authorized Miner",
    "Senior Miner",
    "Senior Miner",
    "Professional Miner",
    "Professional Miner",
    "Veteran Miner",
    "Veteran Miner",
    "Expert Miner",
    "Expert Miner",
    "Elite Miner",
    "Elite Miner",
    "Elite Miner",
    "Supreme Miner",
    "Supreme Miner",
    "Supreme Miner",
    "Master Miner",
    "Master Miner",
    "Master Miner",
    "Epic Miner",
    "Epic Miner",
    "Epic Miner",
    "Epic Miner",
    "Legendary Miner",
    "Legendary Miner",
    "Legendary Miner",
    "Legendary Miner",
    "Legendary Miner",
    "Mythic Miner",
    "Mythic Miner",
    "Mythic Miner",
    "Mythic Miner",
    "Mythic Miner",
    "Stone Guard",
    "Stone Guard",
    "Stone Guard",
    "Stone Guard",
    "Stone Guard",
    "Honor Guard",
    "Honor Guard",
    "Honor Guard",
    "Honor Guard",
    "Honor Guard",
    "Iron Guard",
    "Iron Guard",
    "Iron Guard",
    "Iron Guard",
    "Iron Guard",
    "Giant Guard",
    "Giant Guard",
    "Giant Guard",
    "Giant Guard",
    "Giant Guard",
    "Night Carver",
    "Night Carver",
    "Night Carver",
    "Night Carver",
    "Night Carver",
    "Longbeard",
    "Longbeard",
    "Longbeard",
    "Longbeard",
    "Longbeard",
    "Gilded Master",
    "Gilded Master",
    "Gilded Master",
    "Gilded Master",
    "Gilded Master",
]

season_guids = seasons.SEASON_GUIDS

# global variable definitions
forged_ocs = dict()
unforged_ocs = dict()
unacquired_ocs = dict()
stats = dict()
file_name = ""
save_data = b""
xp_per_season_level = 5000
season_guid = seasons.SEASON_GUIDS[seasons.LATEST_SEASON]
season_edits = dict()  # season guid -> values typed for a season that was switched away from
season_cache = dict()  # season guid -> the values the open save has for it
loading = 0  # above zero while the window is being filled from a save
saved_snapshot = None  # what snapshot() returned at the last open or save
campaign_baseline = None  # the assignments as the save has them
campaign_state = None
campaign_catalog = dict()
campaigns_dirty = False
resource_guids = {
    "yeast": "078548B93232C04085F892E084A74100",
    "starch": "72312204E287BC41815540A0CF881280",
    "barley": "22DAA757AD7A8049891B17EDCC2FE098",
    "bismor": "AF0DC4FE8361BB48B32C92CC97E21DE7",
    "enor": "488D05146F5F754BA3D4610D08C0603E",
    "malt": "41EA550C1D46C54BBE2E9CA5A7ACCB06",
    "umanite": "5F2BCF8347760A42A23B6EDC07C0941D",
    "jadiz": "22BC4F7D07D13E43BFCA81BD9C14B1AF",
    "croppa": "8AA7FB43293A0B49B8BE42FFE068A44C",
    "magnite": "AADED8766C227D408032AFD18D63561E",
    "error": "5828652C9A5DE845A9E2E1B8B463C516",
    "cores": "A10CB2853871FB499AC854A1CDE2202C",
    "data": "99FA526AD87748459498905A278693F6",
    "phazyonite": "67668AAE828FDB48A9111E1B912DBFA4",
}

def create_window():
    """builds the window, loads the reference data and connects everything up"""
    global widget, guid_dict, campaign_catalog, steam_path
    global file_name, save_data, season_guid, campaign_state, campaigns_dirty
    global loading, saved_snapshot, campaign_baseline

    # a new window starts without a save and on the newest season
    file_name = ""
    save_data = b""
    season_guid = seasons.SEASON_GUIDS[seasons.LATEST_SEASON]
    season_edits.clear()
    campaign_state = None
    campaigns_dirty = False
    campaign_baseline = None
    loading = 0
    saved_snapshot = None
    season_cache.clear()

    # load reference data
    with open(data_path("guids.json"), "r") as g:
        guid_dict = json.loads(g.read())
    # cosmetics are listed next to the weapons, as one group per kind (Beards, Victory Poses, ...)
    try:
        with open(data_path("cosmetics.json"), "r") as c:
            guid_dict.update(json.loads(c.read()))
    except OSError:
        pass  # without it, cosmetics are still kept in the save, they just show up as their guid

    try:
        # find the install path for the steam version
        steam_reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path = winreg.QueryValueEx(steam_reg, "SteamPath")[0]
        steam_path += "/steamapps/common/Deep Rock Galactic/FSD/Saved/SaveGames"
    except:
        steam_path = "."

    widget = ui_main.build_main_window(TextEditFocusChecking)
    campaign_catalog = campaigns.load_catalog(data_path("campaigns.json"))

    # set column names for overclock treeview
    widget.overclock_tree.setHeaderLabels(["Name", "Status", "GUID"])

    # populate the promotion drop downs
    promo_boxes = [
        widget.driller_promo_box,
        widget.gunner_promo_box,
        widget.engineer_promo_box,
        widget.scout_promo_box,
    ]
    for i in promo_boxes:
        for j in promo_ranks:
            i.addItem(j)

    # one entry per season; the newest is selected
    for number, guid in season_guids.items():
        current = " (current)" if number == seasons.LATEST_SEASON else ""
        widget.season_picker.addItem(f"Season {number}{current}", guid)
    widget.season_picker.setCurrentIndex(widget.season_picker.findData(season_guid))

    # populate the status filter for overclocks and cosmetics
    sort_labels = ["All", "Unforged", "Forged", "Unacquired"]
    for i in sort_labels:
        widget.combo_oc_filter.addItem(i)

    # connect functions to buttons and actions
    widget.actionOpen_Save_File.triggered.connect(open_file)
    widget.actionSave_changes.triggered.connect(save_changes)
    widget.actionSet_All_Classes_to_25.triggered.connect(set_all_25)
    widget.actionAdd_overclock_crafting_materials.triggered.connect(add_crafting_mats)
    widget.actionReset_to_original_values.triggered.connect(reset_values)
    widget.campaign_page.set_catalog(campaign_catalog)
    widget.campaign_page.changed.connect(campaigns_changed)
    widget.combo_oc_filter.currentTextChanged.connect(filter_overclocks)
    widget.oc_class_filter.currentTextChanged.connect(filter_overclocks)
    widget.oc_kind_filter.currentTextChanged.connect(filter_overclocks)
    widget.oc_search.textChanged.connect(filter_overclocks)
    widget.add_cores_button.clicked.connect(add_cores)
    widget.remove_all_ocs.clicked.connect(remove_all_ocs)
    widget.remove_selected_ocs.clicked.connect(remove_selected_ocs)
    widget.driller_promo_box.currentIndexChanged.connect(update_rank)
    widget.engineer_promo_box.currentIndexChanged.connect(update_rank)
    widget.gunner_promo_box.currentIndexChanged.connect(update_rank)
    widget.scout_promo_box.currentIndexChanged.connect(update_rank)
    widget.season_picker.currentIndexChanged.connect(change_season)

    # anything typed or picked in the value boxes means unsaved changes (unless it is back to what the save had)
    for edit in widget.data_edits:
        edit.textChanged.connect(update_dirty)
    for combo in widget.data_combos:
        combo.currentIndexChanged.connect(update_dirty)
    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    theme.apply(app)
    create_window()
    widget.show()
    sys.exit(app.exec())
