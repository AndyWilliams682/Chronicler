
from src.slot import Slot
from src.room import Room
from src.incursion import Incursion
from src.temple_layout import TempleLayout
from src.constants import *


def choose_incursion_room(incursion: Incursion):
    left = incursion.left_option.architect
    right = incursion.right_option.architect

    output = incursion.right_option # Assume upgrade is better unless...
    # The new room is more impactful or more valuable
    if ARCHITECTS["Valuable"][left] > ARCHITECTS["Valuable"][right]:
        output = incursion.left_option
    elif ARCHITECTS["Impactful"][left] and not ARCHITECTS["Impactful"][right] and ARCHITECTS["Valuable"][right] is False:
        output = incursion.left_option
    
    return output


# Add ability to ignore apex
def calc_tie_breakers(layout: TempleLayout):
    tie_breakers = {}
    adj_numbers = {}
    for slot in layout.slot_map.index:
        adj_rooms = (layout.connection_map[slot] == 0).sum() + 1 - layout.slot_map["Fixed"][slot]
        if layout.connection_map[slot][Slot(2, 0)] == 0:
            adj_rooms -= 1
        if layout.connection_map[slot][Slot(0, 4)] == 0:
            adj_rooms -= 1
        if adj_rooms not in adj_numbers.keys():
            adj_numbers[adj_rooms] = 0
        tie_breakers[slot] = adj_rooms * 10 + adj_numbers[adj_rooms]
        adj_numbers[adj_rooms] += 1
    return tie_breakers


TIE_BREAKERS = calc_tie_breakers(TempleLayout())

# Add ability to ignore apex
def get_door_priority(layout: TempleLayout, slot: Slot):
    adjacent_rooms = set([slot])
    for connection_room in layout.get_connected_slots(slot, include_reference=True):
        adjacent_rooms = adjacent_rooms.union(set(layout.connection_map.index[layout.connection_map[connection_room] != -1]))
        adjacent_rooms -= set(layout.slot_map.index[layout.slot_map["Fixed"] == True])
    return len(adjacent_rooms) + TIE_BREAKERS[slot] / 100


def choose_which_doors_to_open(room: Room, layout: TempleLayout):
    # Need to consider ignoring the apex as it provides no benefit for other rooms
    slot = layout.get_slot_with(room)
    closed_slots = layout.get_adjacent_and_disconnected_slots(slot)
    closed_slots = sorted(closed_slots, key=lambda other_slot: get_door_priority(layout, other_slot))
    # doors = [temple.slot_map["Room"][slot] for slot in doors] # This returns the rooms instead of the slots
    return closed_slots


def choose_to_leave_map_early(selected_room):
    # Maximizing odds of getting the valuable room again.
    if ARCHITECTS["Valuable"][selected_room.architect] > 0:
        return True
    return False
