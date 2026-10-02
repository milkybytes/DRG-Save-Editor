"""Promotions are picked as a tier and a level within it; Legendary has no upper limit."""
import gvas
import player
import pytest
import seasons

DWARVES = ("driller", "engineer", "gunner", "scout")


@pytest.mark.parametrize(
    "count, tier, level",
    [
        (0, "None", None),
        (1, "Bronze", 1),
        (3, "Bronze", 3),
        (4, "Silver", 1),
        (9, "Gold", 3),
        (10, "Platinum", 1),
        (13, "Diamond", 1),
        (15, "Diamond", 3),
        (16, "Legendary", 1),
        (18, "Legendary", 3),
        (19, "Legendary", 4),  # what used to be "Legendary 3+"
        (40, "Legendary", 25),
        (500, "Legendary", 485),
    ],
)
def test_the_number_of_promotions_round_trips(editor, count, tier, level):
    main, window, save = editor
    main.set_promo("scout", count)
    assert window.scout_promo_box.currentText() == tier
    if level is None:
        assert not window.scout_promo_level.isEnabled()
    else:
        assert window.scout_promo_level.isEnabled() and window.scout_promo_level.value() == level
    assert main.promo_count("scout") == count


def test_only_legendary_goes_past_three(editor):
    main, window, save = editor
    spin = window.driller_promo_level
    window.driller_promo_box.setCurrentText("Gold")
    assert (spin.minimum(), spin.maximum()) == (1, 3)
    window.driller_promo_box.setCurrentText("Legendary")
    assert spin.minimum() == 1 and spin.maximum() >= 999
    spin.setValue(77)
    assert main.promo_count("driller") == 15 + 77
    window.driller_promo_box.setCurrentText("Silver")
    assert spin.value() == 3  # clamped to what the tier has
    window.driller_promo_box.setCurrentText("None")
    assert main.promo_count("driller") == 0


def test_the_opened_save_shows_its_promotions(editor):
    main, window, save = editor
    for dwarf in DWARVES:
        assert main.promo_count(dwarf) == main.stats["xp"][dwarf]["promo"]
    assert not window.actionSave_changes.isEnabled()


def test_a_promotion_beyond_legendary_3_is_saved_as_picked(editor):
    main, window, save = editor
    window.gunner_promo_box.setCurrentText("Legendary")
    window.gunner_promo_level.setValue(25)
    assert window.actionSave_changes.isEnabled()
    main.save_changes()
    assert player.read(gvas.loads(save.read_bytes()))["xp"]["gunner"]["promo"] == 15 + 25
    assert main.promo_count("gunner") == 40  # and it reads back the same


def test_changing_the_level_alone_counts_as_a_change_and_updates_the_rank(editor):
    main, window, save = editor
    main.set_promo("scout", 16)
    main.reset_values()
    rank = window.classes_group.text()
    window.scout_promo_box.setCurrentText("Legendary")
    window.scout_promo_level.setValue(window.scout_promo_level.value() + 1)
    assert window.actionSave_changes.isEnabled()
    assert window.classes_group.text() != rank  # each promotion is 25 levels of rank


def test_season_zero_is_not_offered(editor):
    main, window, save = editor
    numbers = [window.season_picker.itemText(i) for i in range(window.season_picker.count())]
    assert numbers[0].startswith("Season 1") and numbers[-1].startswith("Season 6")
    assert "Season 0" not in numbers
    assert window.season_picker.findData(seasons.SEASON_GUIDS[0]) == -1
