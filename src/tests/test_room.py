import pytest

from room import Room


def test_from_abbreviation():
    immutable_room = Room.from_abbreviation("ENT")
    normal_room = Room.from_abbreviation("aa0")
    assert immutable_room == Room("ENT", 0)
    assert normal_room == Room("aa", 0)
    with pytest.raises(ValueError):
        Room.from_abbreviation("abcde")


def test_from_name():
    assert Room.from_name("ENTRANCE") == Room("ENT", 0)


def test_chronicle_display():
    assert Room.from_name("ENTRANCE").chronicle_display == "ENTRANCE"
    assert Room.from_name("CORRUPTION CHAMBER").chronicle_display == "CORRUPTION CHAMBER (Tier 1)"


def test_upgrade():
    one_tier = Room("EX", 1).upgrade()
    two_tiers = Room("EX", 1).upgrade(additional_atlas_chance=100)
    capped_at_three = Room("EX", 3).upgrade()
    assert one_tier == Room("EX", 2)
    assert two_tiers == Room("EX", 3)
    assert capped_at_three == Room("EX", 3)
    with pytest.raises(ValueError):
        Room("aa", 0).upgrade()


def test_swap():
    success = Room("aa", 0).swap("UP")
    contested_development = Room("EX", 2).swap("CR", contested_development=True)
    assert success == Room("UP", 1)
    assert contested_development == Room("CR", 3)
    with pytest.raises(ValueError):
        Room("ENT", 0).swap("CR")
    with pytest.raises(ValueError):
        Room("UP", 3).swap("CR")
