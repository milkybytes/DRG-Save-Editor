import collections
import json

COST_KEYS = {"credits", "bismor", "croppa", "enor", "jadiz", "magnite", "umanite"}
CLASSES = {"Driller", "Engineer", "Gunner", "Scout"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_entries(data):
    for guid, entry in data.items():
        assert len(guid) == 32 and guid == guid.upper() and int(guid, 16) >= 0, guid
        assert entry["class"] in CLASSES, (guid, entry)
        assert entry["weapon"] and entry["name"], (guid, entry)
        assert set(entry["cost"]) == COST_KEYS, (guid, entry)
    # the editor's tree is keyed by class, group and name, so entries must not share all three
    counts = collections.Counter((e["class"], e["weapon"], e["name"]) for e in data.values())
    assert max(counts.values()) == 1, [k for k, n in counts.items() if n > 1]


def test_overclocks():
    overclocks = load("guids.json")
    check_entries(overclocks)
    # every overclock costs credits plus exactly three materials
    for entry in overclocks.values():
        assert sum(1 for k, v in entry["cost"].items() if k != "credits" and v) == 3, entry


def test_cosmetics():
    cosmetics = load("cosmetics.json")
    check_entries(cosmetics)
    assert all(e["cosmetic"] and e["weapon"].startswith("Cosmetic - ") for e in cosmetics.values())
    # each cosmetic is one schematic per class
    per_item = collections.Counter((e["weapon"], e["name"]) for e in cosmetics.values())
    assert set(per_item.values()) == {4}


def test_overclocks_and_cosmetics_do_not_share_guids():
    assert not set(load("guids.json")) & set(load("cosmetics.json"))
