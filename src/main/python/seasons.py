"""
Season progress edits on top of gvas.py.

Save layout (SeasonSave):
  Seasons  map of season guid -> struct with XP, Tokens (scrip), RewardsClaimed, ...
           the game omits fields that hold their default, so XP and Tokens may be missing
"""
import gvas
from gvas import Prop

# season number -> guid as stored in the save (the game's SaveGameID on Season_NN.json, byte-swapped)
SEASON_GUIDS = {
    0: "96037450EC27D444882251F6D40125FE",
    1: "A47D407EC0E4364892CE2E03DE7DF0B3",
    2: "B860B55F1D1BB54D8EE2E41FDA9F5838",
    3: "D8810F6C76D374419AE6A18EF5B3BA26",
    4: "0A3AE2198CA5B649B56E4E11D6762AC6",
    5: "82F3091744BBDE4DB1A0C6766C0716EF",
    6: "E1BF9763D4582E4FB4F6DE7F40554632",
}
LATEST_SEASON = max(SEASON_GUIDS)

# order of the leading fields in a season struct, used to place a field the game left out
FIELD_ORDER = ["CountSeasonContentDisabled", "CountSeasonContentReenabled", "XP", "Tokens"]


def _seasons(save):
    prop = save.find("SeasonSave", "Seasons")
    if prop is None:
        raise ValueError("save has no SeasonSave")
    return prop.value


def _season_fields(save, guid):
    guid = guid.upper()
    for key, fields in _seasons(save):
        if key.upper() == guid:
            return fields
    return None


def _int_value(fields, name):
    prop = fields.get(name)
    return prop.value if prop is not None else 0


def _set_int(fields, name, value):
    prop = fields.get(name)
    if prop is not None:
        prop.value = value
        return
    before = FIELD_ORDER[: FIELD_ORDER.index(name)]
    position = 0
    for i, p in enumerate(fields):
        if p.name in before:
            position = i + 1
    fields.insert(position, Prop.int_(name, value))


def get_season(save, guid):
    """returns {"xp": int, "scrip": int}, or None when the save has no entry for that season"""
    fields = _season_fields(save, guid)
    if fields is None:
        return None
    return {"xp": _int_value(fields, "XP"), "scrip": _int_value(fields, "Tokens")}


def set_season(save, guid, xp, scrip):
    """returns False (and changes nothing) when the save has no entry for that season"""
    fields = _season_fields(save, guid)
    if fields is None:
        return False
    _set_int(fields, "XP", xp)
    _set_int(fields, "Tokens", scrip)
    return True


def read_season(data, guid):
    try:
        return get_season(gvas.loads(data), guid)
    except ValueError:
        return None


def apply_season(data, guid, xp, scrip):
    """returns the save bytes with that season's XP and scrip written into them"""
    save = gvas.loads(data)
    try:
        if not set_season(save, guid, xp, scrip):
            return data
    except ValueError:
        return data
    return gvas.dumps(save)
