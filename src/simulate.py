import numpy as np

from temple import Temple
from incursion import Incursion


def simulate(temple: Temple):
    # May want to createa a clone of client to save the state while testing what can happen
    # Generates random incursions
    temple.update_architects_in_temple() # Updates architect locations
    incursion_area_level = temple.calc_minimum_area_level_for_max()
    while temple.incursions_remaining > 0: # Simulate completing incursions
        temple.incursion = generate_incursion(temple) # Generates new options and a slot
        slot = temple.layout.get_slot_with(temple.incursion.room)
        temple.slots_selected_in_map.append(slot)
        temple.make_decisions()

        # print(client.incursions_remaining, client.calc_minimum_area_level_for_max(), incursion_area_level)
        temple.total_incursion_area_levels += incursion_area_level
        temple.highest_incursion_area_level = max(temple.highest_incursion_area_level, incursion_area_level) # Not very relevant for simulation
        
        complete_incursion(temple) # Completes an incursion (choosing an room option, opening a door, etc)
        temple.incursions_remaining -= 1

        if len(temple.slots_selected_in_map) == 4 or temple.leave_map_early: # TODO: This should read from atlas passives
            temple.slots_selected_in_map = []
            incursion_area_level = temple.calc_minimum_area_level_for_max()
        
        temple.reset_decisions()
        
    temple.complete_temple() # Performs a few final steps before finishing
    return temple


def select_random_waiting_architect(temple: Temple):
    if "Waiting" not in temple.architects.values:
        raise ValueError("There are no more waiting architects to choose from, but an attempt was made.")
    architect = np.random.choice(temple.architects.index[temple.architects == "Waiting"])
    temple.architects[architect] = "Non-Resident"
    return architect


def generate_incursion(temple: Temple):
    slot = temple.layout.select_random_slot_for_incursion(temple.slots_selected_in_map)
    room = temple.layout.get_room_in_slot(slot)

    if room.tier == 0:
        right_option = room.swap(select_random_waiting_architect(temple))
    else:
        right_option = room.upgrade()

    left_option = room.swap(select_random_waiting_architect(temple))

    return Incursion(room=room, right_option=right_option, left_option=left_option)


def complete_incursion(temple: Temple):
    slot = temple.layout.get_slot_with(temple.incursion.room)
    temple.layout.set_room_in_slot(slot, temple.selected_option)
    temple.update_architects_in_temple()
    
    if len(temple.priority_doors) > 0:
        # Assume one Stone of Passage per Incursion
        temple.layout.open_door(slot, temple.priority_doors[0])


if __name__ == "__main__":
    test = Temple.generate()
    test = simulate(test)
    print(test)
    print()
    print(test.itemize())
