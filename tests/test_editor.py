import pytest
from src.main.python.main import make_save_file
import json


@pytest.mark.parametrize(
    "save_path,change_path",
    [
        ("tests/sample_save1.sav", "tests/save_data1.json"),
        ("tests/sample_save2.sav", "tests/save_data2.json"),
        ("tests/sample_save3.sav", "tests/save_data3.json"),
    ],
)
def test_save_changes(save_path, change_path, tmp_path):
    with open(change_path, "r") as d:
        sample_changes = json.loads(d.read())
    sample_changes["misc"].setdefault("phazyonite", 0)

    # the samples predate the phazyonite resource, so the first pass adds it to the save...
    converted = make_save_file(save_path, sample_changes)
    converted_path = tmp_path / "converted.sav"
    converted_path.write_bytes(converted)

    # ...after which writing the same values again must not change a byte
    assert make_save_file(str(converted_path), sample_changes) == converted


# need to update the test data for this, this is supposed to make sure it works right when a save has no perk points
# @pytest.mark.parametrize(
#     "filename",
#     [
#         "no_perk_points",
#     ],
# )
# def test_edge_cases(filename):
#     pre_suffix = "_pre.sav"
#     post_suffix = "_post.sav"
#     data_suffix = "_data.json"

#     with open(f"tests/{filename}{pre_suffix}", "rb") as pre:
#         original_data = pre.read()

#     with open(f"tests/{filename}{post_suffix}", "rb") as post:
#         new_data = post.read()

#     with open(f"tests/{filename}{data_suffix}", "r") as c:
#         changes = json.loads(c.read())

#     changed_data = make_save_file(f"tests/{filename}{pre_suffix}", changes)
#     assert changed_data == new_data
