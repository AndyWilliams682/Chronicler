import pytest

from temple import Temple
from slot import Slot
from room import Room


@pytest.fixture()
def temple():
    return Temple.from_vision_output({
        "layout": {
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
        },
        "incursion": {
            "room": "PASSAGEWAYS",
            "left_option": "STRONGBOX CHAMBER",
            "right_option": "TORMENT CELLS"
        },
        "remaining": 12
    })


def test_update_slot_from_vision_output(temple):
    vision_output = {
        "layout": {
            "0F1": { "Name": "EXPLOSIVES ROOM", "Connections": ["—", "r\\"] }
        },
        "incursion": {
            "room": "PITS",
            "left_option": "CORRUPTION CHAMBER",
            "right_option": "ROYAL MEETING ROOM"
        },
        "remaining": 11
    }
    temple.update_slot_from_vision_output(vision_output)
    assert temple.incursions_remaining == 11
    assert temple.incursion.room == Room("hh", 0)
    assert temple.layout.slot_map["Room"][Slot(1, 0)] == Room("EX", 1)
    assert temple.layout.connection_map[Slot(1, 0)][Slot(0, 1)] == 1


def test_make_decisions(temple):
    output = temple.make_decisions()
    assert output == (Room("TS", 1), False, [Slot(1, 1), Slot(1, 2)])


def test_calc_minimum_area_level_for_max(temple):
    assert temple.calc_minimum_area_level_for_max() == 83
    temple.highest_incursion_area_level = 83
    temple.total_incursion_area_levels += 83
    temple.incursions_remaining -= 1
    assert temple.calc_minimum_area_level_for_max() == 73
    temple.total_incursion_area_levels += 83 * 3
    temple.incursions_remaining -= 3
    assert temple.calc_minimum_area_level_for_max() == 68
    temple.incursions_remaining = 0
    assert temple.calc_minimum_area_level_for_max() == 0


def test_get_temple_area_level(temple):
    temple.highest_incursion_area_level = 83
    temple.incursions_remaining -= 4
    temple.total_incursion_area_levels += 72 * 4
    assert temple.get_temple_area_level() == 82
    temple.total_incursion_area_levels += 83
    assert temple.get_temple_area_level() == 83


def test_itemize(temple):
    temple.highest_incursion_area_level = 82
    temple.total_incursion_area_levels = 73 * 12
    temple.incursions_remaining = 0
    assert temple.itemize() == 'Chronicle of Atzoatl\n====================\nArea Level 82\n--------------------\nOpen Rooms:\nANTECHAMBER\nCELLAR\nPASSAGEWAYS\nSACRIFICIAL CHAMBER (Tier 1)\nTOMBS\nAPEX OF ATZOATL\n\nObstructed Rooms:\nBANQUET HALL\nHALLS\nCLOISTER\nCHASM\nCORRUPTION CHAMBER (Tier 1)\nPITS\n'
