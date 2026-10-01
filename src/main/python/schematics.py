"""
Unforged ("owned") schematic edits on top of gvas.py.

Save layout (SchematicSave):
  ForgedSchematics  array of Guid, everything that has been forged
  OwnedSchematics   array of Guid, acquired but not forged yet (overclocks and cosmetics alike);
                    the game omits the property while the list is empty
"""
import gvas
from gvas import Prop


def _schematic_save(save):
    prop = save.find("SchematicSave")
    if prop is None:
        raise ValueError("save has no SchematicSave")
    return prop.value


def get_owned_schematics(save):
    owned = _schematic_save(save).get("OwnedSchematics")
    return list(owned.value) if owned is not None else []


def set_owned_schematics(save, guids):
    schematics = _schematic_save(save)
    guids = [g.upper() for g in guids]
    owned = schematics.get("OwnedSchematics")
    if not guids:
        schematics.remove_named("OwnedSchematics")
    elif owned is not None:
        owned.value[:] = guids
    else:
        forged = schematics.get("ForgedSchematics")
        position = schematics.index(forged) + 1 if forged is not None else len(schematics)
        schematics.insert(position, Prop.guid_array("OwnedSchematics", guids))


def apply_unforged(data, guids):
    """returns the save bytes with the unforged list replaced by guids"""
    save = gvas.loads(data)
    if save.find("SchematicSave") is None:  # very new saves have no schematics at all
        return data
    set_owned_schematics(save, guids)
    return gvas.dumps(save)
