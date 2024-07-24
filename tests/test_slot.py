import pytest
import pandas as pd

from src.slot import Slot, chronicle_key


def test_from_str():
    output = Slot.from_str("1F0")
    assert output == Slot(0, 1)


def test_distance_to():
    output = Slot(1, 1).distance_to(Slot(0, 4))
    assert output == 3
    output = Slot(1, 1).distance_to(Slot(1, 1))
    assert output == 0


def test_pick_rightmost():
    output = Slot(1, 1).pick_rightmost(Slot(0, 1))
    assert output == Slot(0, 1)
    output = Slot(2, 1).pick_rightmost(Slot(3, 0))
    assert output == Slot(2, 1)


def test_relative_direction_from():
    straight = Slot(0, 3).relative_direction_from(Slot(1, 3))
    up = Slot(0, 2).relative_direction_from(Slot(0, 1))
    down = Slot(2, 2).relative_direction_from(Slot(3, 1))
    assert straight == "—"
    assert up == "\\"
    assert down == "/"
    with pytest.raises(ValueError):
        Slot(2, 2).relative_direction_from(Slot(0, 4))


def test_get_adjacent_slot():
    slot = Slot(1, 2)
    assert slot.get_adjacent_slot("—") == Slot(2, 2)
    assert slot.get_adjacent_slot("\\") == Slot(1, 3)
    assert slot.get_adjacent_slot("/") == Slot(2, 1)
    assert slot.get_adjacent_slot("r—") == Slot(0, 2)
    assert slot.get_adjacent_slot("r\\") == Slot(0, 3)
    assert slot.get_adjacent_slot("r/") == Slot(1, 1)


def test_get_chronicle_position():
    assert Slot(0, 4).chronicle_order == 12
    assert Slot(3, 0).chronicle_order == -3


def test_chronicle_key():
    assert chronicle_key(pd.Index([Slot(0, 1)]))[0] == 3
