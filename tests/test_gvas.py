import pytest
import gvas
import campaigns

SAMPLES = [
    "tests/sample_save1.sav",
    "tests/sample_save2.sav",
    "tests/sample_save3.sav",
    "tests/no_perk_points_pre.sav",
    "tests/no_perk_points_post.sav",
]


def load(path):
    with open(path, "rb") as f:
        return f.read()


@pytest.mark.parametrize("save_path", SAMPLES)
def test_round_trip_is_byte_identical(save_path):
    data = load(save_path)
    assert gvas.dumps(gvas.loads(data)) == data


def test_container_sizes_follow_edits():
    data = load("tests/sample_save3.sav")
    save = gvas.loads(data)
    forged = save.find("SchematicSave", "ForgedSchematics")
    forged.value.append("00" * 15 + "01")

    edited = gvas.dumps(save)
    assert len(edited) == len(data) + 16

    reparsed = gvas.loads(edited)
    assert reparsed.find("SchematicSave", "ForgedSchematics").value == forged.value
    assert gvas.dumps(reparsed) == edited


def test_complete_active_campaign():
    data = load("tests/sample_save3.sav")
    save = gvas.loads(data)
    guid, progress = campaigns.get_active_campaign(save)
    assert progress == 2
    completed_before = campaigns.get_completed_campaigns(save)
    assert guid not in completed_before

    assert campaigns.complete_active_campaign(save) == guid

    reparsed = gvas.loads(gvas.dumps(save))
    assert campaigns.get_active_campaign(reparsed) is None
    assert campaigns.get_completed_campaigns(reparsed) == completed_before + [guid]


def test_complete_with_no_active_campaign_is_a_noop():
    save = gvas.loads(load("tests/sample_save3.sav"))
    campaigns.complete_active_campaign(save)
    snapshot = gvas.dumps(save)
    assert campaigns.complete_active_campaign(save) is None
    assert gvas.dumps(save) == snapshot


def test_state_round_trip_and_apply():
    data = load("tests/sample_save3.sav")
    state = campaigns.read_state(data)
    assert state["active"][1] == 2

    # writing an unchanged state must not alter the save
    assert campaigns.apply_state(data, state) == data

    guid = campaigns.complete_active_in_state(state)
    assert state["active"] is None and state["completed"][-1] == guid

    new_state = campaigns.read_state(campaigns.apply_state(data, state))
    assert new_state == state


def test_uncheck_and_add_arbitrary_campaigns():
    data = load("tests/sample_save3.sav")
    state = campaigns.read_state(data)
    removed = state["completed"].pop(0)
    state["completed"].append("AB" * 16)

    new_state = campaigns.read_state(campaigns.apply_state(data, state))
    assert removed not in new_state["completed"]
    assert new_state["completed"][-1] == "AB" * 16
    assert new_state["active"] == state["active"]  # untouched


def test_completed_list_is_created_when_the_save_has_none():
    save = gvas.loads(load("tests/sample_save3.sav"))
    campaign = save.find("CampaignSave").value
    campaign.remove_named("CompletedCampaigns")
    data = gvas.dumps(save)

    state = campaigns.read_state(data)
    assert state["completed"] == []
    state["completed"] = ["CD" * 16]
    assert campaigns.read_state(campaigns.apply_state(data, state))["completed"] == ["CD" * 16]


def test_catalog_file(tmp_path):
    good = tmp_path / "campaigns.json"
    good.write_text('{"ab" : {"name": "Some Campaign", "prefix": "SC"}}')
    assert campaigns.load_catalog(str(good)) == {
        "AB": {"name": "Some Campaign", "prefix": "SC"}
    }
    assert campaigns.load_catalog(str(tmp_path / "missing.json")) == {}
