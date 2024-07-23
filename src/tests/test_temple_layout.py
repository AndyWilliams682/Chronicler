import pytest

from temple_layout import TempleLayout
from slot import Slot
from room import Room


@pytest.fixture()
def layout():
    return TempleLayout.from_dict({
        "0F1": {"Name": "ANTECHAMBER", "Connections": ["—"]},
        "0F2": {"Name": "ENTRANCE", "Connections": []},
        "0F3": {"Name": "BANQUET HALL", "Connections": []},
        "1F0": {"Name": "CELLAR", "Connections": ["/", "\\"]},
        "1F1": {"Name": "CHASM", "Connections": []},
        "1F2": {"Name": "CLOISTER", "Connections": ["—"]},
        "1F3": {"Name": "HALLS", "Connections": []},
        "2F0": {"Name": "PASSAGEWAYS", "Connections": ["\\"]},
        "2F1": {"Name": "PITS", "Connections": []},
        "2F2": {"Name": "CORRUPTION CHAMBER", "Connections": []},
        "3F0": {"Name": "TOMBS", "Connections": ["\\"]},
        "3F1": {"Name": "SACRIFICIAL CHAMBER", "Connections": []},
        "4F0": {"Name": "APEX OF ATZOATL", "Connections": ["/"]}
    })


def test_from_dict(layout):
    assert layout.slot_map["Open"].sum() == 7


def test_update_slot_from_vision_output(layout):
    vision_otput = { "Name": "EXPLOSIVES ROOM", "Connections": ["—", "r\\"] }
    layout.update_slot_from_vision_output("0F1", vision_otput)
    assert layout.slot_map["Room"][Slot(1, 0)] == Room("EX", 1)
    assert layout.connection_map[Slot(1, 0)][Slot(0, 1)] == 1


def test_get_slot_with(layout):
    room_output = layout.get_slot_with(Room("CR", 1))
    architect_output = layout.get_slot_with("UN")
    not_present = layout.get_slot_with("EX")
    assert room_output == Slot(2, 2)
    assert architect_output == Slot(1, 3)
    assert not_present == None


def test_get_room_in_slot(layout):
    output = layout.get_room_in_slot(Slot(0, 4))
    assert output == Room("APX", 0)


def test_set_room_in_slot(layout):
    layout.set_room_in_slot(Slot(1, 0), Room("AR", 3))
    assert layout.slot_map["Room"][Slot(1, 0)] == Room("AR", 3)
    assert layout.slot_map["Fixed"][Slot(1, 0)] == True


def test_get_adjacent_slots(layout):
    output = layout.get_adjacent_slots(Slot(2, 2))
    assert set(output) == set([Slot(1, 3), Slot(1, 2), Slot(3, 1), Slot(2, 1)])


def test_get_connected_slots(layout):
    with_ref = layout.get_connected_slots(Slot(2, 0), include_reference=True)
    without_ref = layout.get_connected_slots(Slot(2, 0))
    assert set(with_ref) == set([Slot(2, 0), Slot(1, 0), Slot(0, 1), Slot(0, 2), Slot(0, 3), Slot(0, 4), Slot(1, 3)])
    assert set(without_ref) == set([Slot(1, 0), Slot(0, 1), Slot(0, 2), Slot(0, 3), Slot(0, 4), Slot(1, 3)])


def test_get_adjacent_and_disconnected_slots(layout):
    output = layout.get_adjacent_and_disconnected_slots(Slot(0, 1))
    assert output == [Slot(1, 1)]


def test_get_adjacent_and_connected_slots(layout):
    output = layout.get_adjacent_and_connected_slots(Slot(0, 2))
    assert set(output) == set([Slot(0, 1), Slot(0, 3)])


def test_open_door(layout):
    layout.open_door(Slot(2, 0), Slot(3, 0))
    assert layout.slot_map["Open"].sum() == 8
    with pytest.raises(ValueError):
        layout.open_door(Slot(2, 0), Slot(0, 4))


def test_select_random_slot_for_incursion(layout):
    layout.slot_map["Fixed"] = True
    layout.slot_map.loc[Slot(1, 0), "Fixed"] = False
    layout.slot_map.loc[Slot(3, 0), "Fixed"] = False
    slots_selected_in_map = [Slot(3, 0)]
    output = layout.select_random_slot_for_incursion(slots_selected_in_map)
    assert output == Slot(1, 0)


def test_is_open(layout):
    assert layout.is_open(Slot(2, 0)) == True
    assert layout.is_open(Slot(3, 0)) == False


def test_are_adjacent(layout):
    assert layout.are_adjacent(Slot(2, 0), Slot(3, 0)) == True
    assert layout.are_adjacent(Slot(2, 0), Slot(0, 4)) == False


def test_are_adjacent_and_connected(layout):
    assert layout.are_adjacent_and_connected(Slot(2, 0), Slot(1, 0)) == True
    assert layout.are_adjacent_and_connected(Slot(2, 0), Slot(3, 0)) == False


def test_calc_upgrade_multiplier(layout):
    layout.set_room_in_slot(Slot(0, 2), Room("UP", 3))
    adjacent = layout.calc_upgrade_multiplier(Slot(0, 2), Slot(1, 2), 2)
    adjacent_and_connected = layout.calc_upgrade_multiplier(Slot(0, 2), Slot(0, 3), 2)
    no_upgrade = layout.calc_upgrade_multiplier(None, Slot(1, 2), 0)
    assert adjacent == 1 / 3
    assert adjacent_and_connected == (1 / 3) + (5 / 9)
    assert no_upgrade == 0


def test_get_connections_as_tuples(layout):
    output = layout.get_connections_as_tuples()
    assert set(output) == set([
        (Slot(2, 0), Slot(1, 0)),
        (Slot(0, 1), Slot(1, 0)),
        (Slot(0, 2), Slot(0, 1)),
        (Slot(0, 3), Slot(0, 2)),
        (Slot(0, 4), Slot(0, 3)),
        (Slot(0, 4), Slot(1, 3)),
        (Slot(3, 1), Slot(2, 1))
    ])
