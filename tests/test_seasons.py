import gvas
import seasons

SAMPLE = "tests/sample_save3.sav"
SEASON_1 = seasons.SEASON_GUIDS[1]  # the only season the samples have an entry for


def load(path=SAMPLE):
    with open(path, "rb") as f:
        return f.read()


def test_every_season_guid_is_a_32_digit_hex_string():
    for guid in seasons.SEASON_GUIDS.values():
        assert len(guid) == 32 and int(guid, 16) >= 0
    assert len(set(seasons.SEASON_GUIDS.values())) == len(seasons.SEASON_GUIDS)


def test_read_and_rewrite_without_changes():
    data = load()
    season = seasons.read_season(data, SEASON_1)
    assert set(season) == {"xp", "scrip"}
    assert seasons.apply_season(data, SEASON_1, season["xp"], season["scrip"]) == data


def test_write_changes_only_that_season():
    data = load()
    new = seasons.apply_season(data, SEASON_1, 123456, 789)
    assert seasons.read_season(new, SEASON_1) == {"xp": 123456, "scrip": 789}
    assert gvas.dumps(gvas.loads(new)) == new


def test_season_the_save_does_not_have_is_left_alone():
    data = load()
    missing = seasons.SEASON_GUIDS[6]
    assert seasons.read_season(data, missing) is None
    assert seasons.apply_season(data, missing, 5, 5) == data


def test_save_without_season_data_is_left_alone():
    data = load("tests/no_perk_points_pre.sav")
    assert seasons.read_season(data, SEASON_1) is None
    assert seasons.apply_season(data, SEASON_1, 5, 5) == data


def test_fields_the_game_omitted_are_created_in_order():
    save = gvas.loads(load())
    fields = seasons._season_fields(save, SEASON_1)
    fields.remove_named("XP")
    fields.remove_named("Tokens")
    data = gvas.dumps(save)
    assert seasons.read_season(data, SEASON_1) == {"xp": 0, "scrip": 0}

    new = seasons.apply_season(data, SEASON_1, 4000, 12)
    assert seasons.read_season(new, SEASON_1) == {"xp": 4000, "scrip": 12}
    names = [p.name for p in seasons._season_fields(gvas.loads(new), SEASON_1)]
    assert names.index("XP") < names.index("Tokens") < names.index("RewardsClaimed")
