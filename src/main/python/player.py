"""
Credits, perk points, resources and the classes' XP and promotions, read and written through gvas.py.

The game leaves out anything that holds its default, so a new player's save may have no Credits, no entry for a
resource that was never owned, or no XP for a class. Those read as 0, and are created when a value is set.

Save layout:
  Credits, PerkPoints         IntProperty on the save itself
  Resources.OwnedResources    map of resource guid -> amount (a float), only for resources that were owned
  CharacterSaves              one entry per class that was played: SaveGameID, XP, TimesRetired (the number of
                              promotions) and RetiredCharacterLevels (always 25 per promotion)
"""
import gvas
from gvas import Prop, PropList

RESOURCE_GUIDS = {
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

# which group of the values dict each resource is in
RESOURCE_GROUPS = {
    **dict.fromkeys(("bismor", "croppa", "enor", "jadiz", "magnite", "umanite"), "minerals"),
    **dict.fromkeys(("yeast", "starch", "barley", "malt"), "brewing"),
    **dict.fromkeys(("cores", "error", "data", "phazyonite"), "misc"),
}

CLASS_GUIDS = {
    "engineer": "85EF626C65F1024A8DFEB5D0F3909D2E",
    "scout": "30D8EA17D8FBBA4C95306DE9655C2F8C",
    "driller": "9EDD56F1EEBCC5488D5B5E5B80B62DB4",
    "gunner": "AE56E180FEC0C44D96FA29C28366B97B",
}

LEVELS_PER_PROMOTION = 25

# the order the game writes properties in, to put a created one where it belongs
SAVE_ORDER = ["PerkPoints", "CharacterSaves", "Credits", "Resources"]
CHARACTER_ORDER = ["savegameid", "xp", "hascompletedretirementcampaign", "timesretired", "retiredcharacterlevels"]


def _get_int(props, name):
    prop = props.get(name)
    return prop.value if prop is not None else 0


def _position(props, name, order, key=lambda n: n):
    """where a property called name goes: before the first present property that the game writes after it"""
    rank = order.index(key(name))
    for i, prop in enumerate(props):
        if key(prop.name) in order and order.index(key(prop.name)) > rank:
            return i
    return len(props)


def _set_int(props, name, value, order, key=lambda n: n):
    prop = props.get(name)
    if prop is not None:
        prop.value = value
    elif value != 0:  # the game leaves a zero out, so there is nothing to do for one
        props.insert(_position(props, name, order, key), Prop.int_(name, value))


# ---- classes


def _entry_guid(entry):
    for prop in entry:
        if prop.name.lower() == "savegameid":  # older saves spell it SavegameID
            return prop.value.upper()
    return None


def _name_in(entry, lowercase_name, default):
    """a property's name as the entry spells it (the game's capitalisation has changed between versions)"""
    for prop in entry:
        if prop.name.lower() == lowercase_name:
            return prop.name
    return default


def _character_entries(save):
    prop = save.find("CharacterSaves")
    return {} if prop is None else {_entry_guid(e): e for e in prop.value}


def _new_character_array():
    return Prop(
        "CharacterSaves",
        "ArrayProperty",
        [],
        inner="StructProperty",
        pguid=None,
        inner_name="CharacterSaves",
        inner_type="StructProperty",
        struct="CharacterSave",
        sguid=b"\x00" * 16,
        inner_pguid=None,
    )


# ---- resources


def _owned_resources(save):
    resources = save.find("Resources")
    return None if resources is None else resources.value.get("OwnedResources")


def _new_resources(owned_items):
    owned = Prop(
        "OwnedResources",
        "MapProperty",
        owned_items,
        key_type="StructProperty",
        value_type="FloatProperty",
        pguid=None,
    )
    return Prop(
        "Resources",
        "StructProperty",
        PropList([owned]),
        struct="ResourcesSave",
        sguid=b"\x00" * 16,
        pguid=None,
    )


# ---- reading and writing


def read(save):
    """the values dict the editor works with: xp, misc, minerals and brewing"""
    values = {
        "xp": {},
        "misc": {"credits": _get_int(save.props, "Credits"), "perks": _get_int(save.props, "PerkPoints")},
        "minerals": {},
        "brewing": {},
    }
    entries = _character_entries(save)
    for dwarf, guid in CLASS_GUIDS.items():
        entry = entries.get(guid)
        values["xp"][dwarf] = {
            "xp": _get_int(entry, "XP") if entry is not None else 0,
            "promo": _get_int(entry, "TimesRetired") if entry is not None else 0,
        }
    owned = dict(_owned_resources(save).value) if _owned_resources(save) is not None else {}
    for name, guid in RESOURCE_GUIDS.items():
        values[RESOURCE_GROUPS[name]][name] = int(owned.get(guid, 0))
    return values


def apply(save, values):
    """writes the values dict into the save; anything the save did not have yet is created"""
    _set_int(save.props, "Credits", values["misc"]["credits"], SAVE_ORDER)
    _set_int(save.props, "PerkPoints", values["misc"]["perks"], SAVE_ORDER)

    # ---- classes
    entries = _character_entries(save)
    for dwarf, guid in CLASS_GUIDS.items():
        xp = values["xp"][dwarf]["xp"]
        promo = values["xp"][dwarf]["promo"]
        entry = entries.get(guid)
        if entry is None:
            if xp == 0 and promo == 0:
                continue
            if save.find("CharacterSaves") is None:
                save.props.insert(_position(save.props, "CharacterSaves", SAVE_ORDER), _new_character_array())
            entry = PropList([Prop.guid("SaveGameID", guid)])
            save.find("CharacterSaves").value.append(entry)
        _set_int(entry, _name_in(entry, "xp", "XP"), xp, CHARACTER_ORDER, key=str.lower)
        _set_int(entry, _name_in(entry, "timesretired", "TimesRetired"), promo, CHARACTER_ORDER, key=str.lower)
        _set_int(
            entry,
            _name_in(entry, "retiredcharacterlevels", "RetiredCharacterLevels"),
            promo * LEVELS_PER_PROMOTION,
            CHARACTER_ORDER,
            key=str.lower,
        )

    # ---- resources
    wanted = {RESOURCE_GUIDS[n]: values[RESOURCE_GROUPS[n]][n] for n in RESOURCE_GUIDS}
    owned = _owned_resources(save)
    if owned is None:
        added = [(g, float(v)) for g, v in wanted.items() if v > 0]
        if not added:
            return
        resources = save.find("Resources")
        if resources is None:
            save.props.insert(_position(save.props, "Resources", SAVE_ORDER), _new_resources(added))
        else:
            resources.value.append(_new_resources(added).value[0])
        return
    items = owned.value
    index = {guid: i for i, (guid, _) in enumerate(items)}
    for guid, amount in wanted.items():
        if guid in index:
            if int(items[index[guid]][1]) != amount:  # leave an untouched value alone, fractions and all
                items[index[guid]] = (guid, float(amount))
        elif amount > 0:
            items.append((guid, float(amount)))


def apply_to_bytes(data, values):
    save = gvas.loads(data)
    apply(save, values)
    return gvas.dumps(save)
