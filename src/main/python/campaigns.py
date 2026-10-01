"""
Campaign (assignment) edits on top of gvas.py.

Save layout (CampaignSave):
  ActiveCampaign     struct {CampaignID: Guid, Progress: int}; default-valued fields are omitted
  CompletedCampaigns array of Guid

The editor works on a small "state" dict so the UI does not have to touch the save tree:
  {"active": (guid, progress) or None, "completed": [guid, ...]}
"""
import json

import gvas
from gvas import Prop, PropList


# Weekly assignments are tracked by the game in per-week structs we don't edit, so the editor
# leaves them alone: they are hidden from the list and kept as-is in CompletedCampaigns.
HIDDEN_GUIDS = {
    "B7903625E3092B429A8441A4C50E38B9",  # Weekly Core Hunt
    "EA8179EFA8FCD343A46E0EAD0114B8F1",  # Weekly Priority Assignment
}


def _campaign_save(save):
    prop = save.find("CampaignSave")
    if prop is None:
        raise ValueError("save has no CampaignSave")
    return prop.value


def get_active_campaign(save):
    """returns (campaign guid, progress) or None when no campaign is active"""
    active = _campaign_save(save).get("ActiveCampaign")
    if active is None:
        return None
    guid = active.value.get("CampaignID")
    if guid is None:
        return None
    progress = active.value.get("Progress")
    return guid.value, (progress.value if progress is not None else 0)


def get_completed_campaigns(save):
    completed = _campaign_save(save).get("CompletedCampaigns")
    return list(completed.value) if completed is not None else []


def set_completed_campaigns(save, guids):
    campaign = _campaign_save(save)
    guids = [g.upper() for g in guids]
    completed = campaign.get("CompletedCampaigns")
    if completed is not None:
        completed.value[:] = guids
    elif guids:
        # the game omits the list while it is empty, so it may need creating
        prop = Prop.guid_array("CompletedCampaigns", guids)
        active = campaign.get("ActiveCampaign")
        campaign.insert(campaign.index(active) + 1 if active is not None else len(campaign), prop)


def clear_active_campaign(save):
    _campaign_save(save).remove_named("ActiveCampaign")


def set_active_campaign(save, guid, progress=0):
    """sets (or replaces) the active campaign; creates the ActiveCampaign field if the save had none"""
    campaign = _campaign_save(save)
    fields = PropList([Prop.guid("CampaignID", guid)])
    if progress:
        fields.append(Prop.int_("Progress", progress))
    prop = Prop(
        "ActiveCampaign",
        "StructProperty",
        fields,
        struct="ActiveCampaignItem",
        sguid=b"\x00" * 16,
        pguid=None,
    )
    active = campaign.get("ActiveCampaign")
    if active is not None:
        campaign[campaign.index(active)] = prop
    else:
        campaign.insert(0, prop)


# ---- state used by the editor UI


def read_state(data):
    save = gvas.loads(data)
    return {
        "active": get_active_campaign(save),
        "completed": get_completed_campaigns(save),
    }


def complete_active_in_state(state):
    """marks the active assignment as completed and clears the active slot; returns its guid, or None if none was active"""
    if state["active"] is None:
        return None
    guid = state["active"][0]
    if guid not in state["completed"]:
        state["completed"].append(guid)
    state["active"] = None
    return guid


def set_active_in_state(state, guid, progress=0):
    """sets a state dict's active campaign; drops it from completed if it was marked as such"""
    guid = guid.upper()
    state["active"] = (guid, progress)
    if guid in state["completed"]:
        state["completed"].remove(guid)


def apply_state(data, state):
    """returns the save bytes with the campaign state written into them"""
    save = gvas.loads(data)
    set_completed_campaigns(save, state["completed"])
    if state["active"] is None:
        clear_active_campaign(save)
    else:
        set_active_campaign(save, *state["active"])
    return gvas.dumps(save)


def load_catalog(path):
    """{GUID: {"name": ..., "prefix": ...}} from a json file; a missing or broken file means an empty catalog"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k.upper(): v for k, v in raw.items()}
