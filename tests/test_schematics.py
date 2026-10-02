import pytest
import gvas
import schematics

SAMPLES_WITH_SCHEMATICS = [
    "tests/sample_save1.sav",
    "tests/sample_save2.sav",
    "tests/sample_save3.sav",
]
A, B, C = "AB" * 16, "CD" * 16, "EF" * 16


def load(path):
    with open(path, "rb") as f:
        return f.read()


def owned(data):
    return schematics.get_owned_schematics(gvas.loads(data))


@pytest.mark.parametrize("save_path", SAMPLES_WITH_SCHEMATICS)
def test_rewriting_the_current_list_changes_nothing(save_path):
    data = load(save_path)
    assert schematics.apply_unforged(data, owned(data)) == data


def test_add_creates_the_list_and_clearing_removes_it_again():
    data = load("tests/sample_save3.sav")
    assert owned(data) == []

    with_two = schematics.apply_unforged(data, [A, B])
    assert owned(with_two) == [A, B]
    assert len(schematics.apply_unforged(data, [A])) + 16 == len(with_two)  # 16 bytes per guid

    # the container sizes have to follow the edit, so the result must survive a round trip
    assert gvas.dumps(gvas.loads(with_two)) == with_two

    assert schematics.apply_unforged(with_two, []) == data


def test_list_can_grow_shrink_and_reorder():
    data = load("tests/sample_save3.sav")
    one = schematics.apply_unforged(data, [A])
    three = schematics.apply_unforged(one, [A, B, C])
    assert owned(three) == [A, B, C]
    assert owned(schematics.apply_unforged(three, [C, A])) == [C, A]
    assert schematics.apply_unforged(three, [A]) == one


def test_guids_are_stored_uppercase():
    data = load("tests/sample_save3.sav")
    assert owned(schematics.apply_unforged(data, ["ab" * 16])) == [A]


def test_save_without_schematics_is_left_alone():
    data = load("tests/no_perk_points_pre.sav")
    assert gvas.loads(data).find("SchematicSave") is None
    assert schematics.apply_unforged(data, [A]) == data
