import pandas as pd
import numpy as np
from random import randint, shuffle

from slot import Slot
from room import Room
from constants import ROOM_DATA, ARCHITECTS


# The temple has a fixed shape
ROOMS_PER_LAYER = [3, 4, 3, 2, 1]
ALL_SLOTS = []
for r in range(len(ROOMS_PER_LAYER)):
    if r == 0:
        ALL_SLOTS += [Slot(q + 1, r) for q in range(ROOMS_PER_LAYER[r])]
    else:
        ALL_SLOTS += [Slot(q, r) for q in range(ROOMS_PER_LAYER[r])]


SCARAB_CONNECTION_FACTOR = [
    2 / 3, # 1 upgradeable connection
    5 / 9, # 2
    4 / 9, # 3
    29 / 81, # 4
    358 / 1215, # 5
    181 / 729 # 6, the max possible
]


class TempleLayout():
    def __init__(self):
        # 1F0 is the second layer from the bottom, first room on the right (it is in the first diag)
        # 0F1 is the lowest layer, first room on the right (it is in the second diag)
        # A diag is a line of rooms going from top left to bottom right (\). The right-most diag is diag 0
        empty_connections = [
            #01  02  03  10  11  12  13  20  21  22  30  31  40
            [-1,  0, -1,  0,  0, -1, -1, -1, -1, -1, -1, -1, -1], # 0F1
            [ 0, -1,  0, -1,  0,  0, -1, -1, -1, -1, -1, -1, -1], # 0F2 (ENTRANCE)
            [-1,  0, -1, -1, -1,  0,  0, -1, -1, -1, -1, -1, -1], # 0F3
            [ 0, -1, -1, -1,  0, -1, -1,  0, -1, -1, -1, -1, -1], # 1F0
            [ 0,  0, -1,  0, -1,  0, -1,  0,  0, -1, -1, -1, -1], # 1F1
            [-1,  0,  0, -1,  0, -1,  0, -1,  0,  0, -1, -1, -1], # 1F2
            [-1, -1,  0, -1, -1,  0, -1, -1, -1,  0, -1, -1, -1], # 1F3
            [-1, -1, -1,  0,  0, -1, -1, -1,  0, -1,  0, -1, -1], # 2F0
            [-1, -1, -1, -1,  0,  0, -1,  0, -1,  0,  0,  0, -1], # 2F1
            [-1, -1, -1, -1, -1,  0,  0, -1,  0, -1, -1,  0, -1], # 2F2
            [-1, -1, -1, -1, -1, -1, -1,  0,  0, -1, -1,  0,  0], # 3F0
            [-1, -1, -1, -1, -1, -1, -1, -1,  0,  0,  0, -1,  0], # 3F1
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1,  0,  0, -1], # 4F0 (APEX OF ATZOATL)
        ]
        self.connection_map = pd.DataFrame(empty_connections, columns=ALL_SLOTS, index=ALL_SLOTS)
        self.slot_map = pd.DataFrame(index=ALL_SLOTS)
        self.slot_map["Room"] = Room()
        self.slot_map["Open"] = False
        self.slot_map.loc[Slot(2, 0), "Open"] = True # Entrance is always open
        self.slot_map["Fixed"] = False
        self.slot_map.loc[Slot(2, 0), "Fixed"] = True # Entrance cannot be changed
        self.slot_map.loc[Slot(0, 4), "Fixed"] = True # Apex of Atzoatl cannot be changed
    
    def generate():
        cls = TempleLayout()
        all_rooms = ROOM_DATA.apply(lambda room: Room(room["Theme"], room["Tier"]), axis=1)
        rooms = list(all_rooms[(ROOM_DATA["Tier"] == 0) & (ROOM_DATA["Fixed"] == False)])
        # The number of Tier 1 rooms is either random chance, or there is a limit, or both?
        # Mathematically, the number of tier one rooms is between 1 and 10 to avoid locking the process
        #     There are only 10 t0 rooms, so there must always be at least one t1 room
        #     If a person gets 11 t1 rooms, and double upgrades all of them, they run out of slots to select for Incursions
        rooms.append(all_rooms[ROOM_DATA["Tier"] == 1].sample().values[0])
        shuffle(rooms)
        rooms.insert(1, Room("ENT", 0))
        rooms.append(Room("APX", 0))
        cls.slot_map["Room"] = rooms

        # Unsure if there is any logic for how these are generated initially
        cls.connection_map = generate_random_connections(cls, 3, 0)
        cls.update_open_slots()

        return cls
    
    def from_dict(vision_output):
        cls = TempleLayout()
        for slot_str in vision_output:
            slot = Slot.from_str(slot_str)
            cls.set_room_in_slot(slot, Room.from_name(vision_output[slot_str]["Name"]))
            
            for direction in vision_output[slot_str]["Connections"]:
                other_slot = slot.get_adjacent_slot(direction)
                cls.open_door(slot, other_slot)
        cls.update_open_slots()
        return cls
    
    # May need to update with a different argument setup
    def from_list(rooms: list):
        cls = TempleLayout()
        if len(rooms) > 13:
            raise ValueError(f"There can only be 13 rooms in a temple, got {len(rooms)}")
        for idx in range(len(cls.connection_map.columns)):
            slot = cls.connection_map.columns[idx]
            room = rooms[idx]
            if slot == "0F2" and room != "ENT":
                raise ValueError(f"The bottom-most room must be the entrance, got {room}")
            if slot == "4F0" and room != "APX":
                raise ValueError(f"The top-most room must be the Apex of Atzoatl, got {room}")
            cls.slot_map.loc[slot, "Room"] = Room.from_abbreviation(room)
            if cls.slot_map.loc[slot, "Room"].tier == 3:
                cls.slot_map.loc[slot, "Fixed"] = True
        return cls
    
    def update_slot_from_vision_output(self, slot_str, vision_output):
        slot = Slot.from_str(slot_str)
        self.set_room_in_slot(slot, Room.from_name(vision_output["Name"]))
        for direction in vision_output["Connections"]:
            other_slot = slot.get_adjacent_slot(direction)
            self.open_door(slot, other_slot)
        self.update_open_slots()
    
    # Given a room or architect, get the slot
    def get_slot_with(self, room_or_architect: Room or str) -> Slot:
        if isinstance(room_or_architect, Room):
            slot = self.slot_map[self.slot_map["Room"] == room_or_architect].index
        elif isinstance(room_or_architect, str):
            slot = self.slot_map[self.slot_map["Room"].apply(lambda room: room.architect) == room_or_architect]["Room"].index
        if len(slot) == 0:
            return None
        return slot[0]
    
    # Given a slot, get the room (which also encodes the architect)
    def get_room_in_slot(self, slot: Slot) -> Room:
        return self.slot_map["Room"][slot]
    
    # Updates a slot in the temple with a new room
    def set_room_in_slot(self, slot, new_room):
        self.slot_map.loc[slot, "Room"] = new_room
        if new_room.tier == 3:
            self.slot_map.loc[slot, "Fixed"] = True
    
    # Performs a search from a starting slot and finds other slots based on the arguments
    def get_slots_from(self, reference_slot: Slot, adjacent: bool, connected: bool = None, include_reference: bool = False):
        output = [reference_slot]

        condition = [1, 0] # Any adjacent rooms
        if connected is True:
            condition = [1] # Only connected rooms
        elif connected is False:
            condition = [0] # Only disconnected rooms
        
        for slot in output:
            for connected_slot in self.connection_map.index[self.connection_map[slot].isin(condition)]:
                if connected_slot not in output:
                    output.append(connected_slot)
            if adjacent:
                break # Depth of 1, only adjacent rooms
        
        if include_reference is False:
            output = output[1:] # Ignoring the starting slot
        
        return pd.Series(output)
    
    def get_adjacent_slots(self, slot: Slot):
        return self.get_slots_from(slot, adjacent=True)
    
    def get_connected_slots(self, slot: Slot, include_reference: bool = False):
        return self.get_slots_from(slot, adjacent=False, connected=True, include_reference=include_reference)
    
    def get_adjacent_and_disconnected_slots(self, slot: Slot):
        # This search is more specific because it requires searching for indirectly connected adjacent slots
        return [adj_slot for adj_slot in self.get_adjacent_slots(slot) if adj_slot not in self.get_slots_from(slot, adjacent=False, connected=True).values]
    
    # Might remove these since they aren't used much and the arguments speak for themselves
    def get_adjacent_and_connected_slots(self, slot: Slot):
        return self.get_slots_from(slot, adjacent=True, connected=True)
    
    def update_open_slots(self):
        for slot in self.get_connected_slots(Slot(2, 0)):
            self.slot_map.loc[slot, "Open"] = True
    
    def open_door(self, slot_1, slot_2):
        if not self.are_adjacent(slot_1, slot_2):
            raise ValueError(f"Attempted to connect two non-adjacent slots {slot_1} and {slot_2}")
        
        self.connection_map.loc[slot_1, slot_2 ] = 1
        self.connection_map.loc[slot_2, slot_1] = 1

        self.update_open_slots() # Must check every time because multiple rooms can become open!

    def select_random_slot_for_incursion(self, slots_seleted_in_map):
        output = self.slot_map.index[self.slot_map["Fixed"] == False]
        output = [slot for slot in output if slot not in slots_seleted_in_map]
        return np.random.choice(output)
    
    def get_doors_to_open(self, reference_slot: Slot):
        output = 4 # Max value possible
        connected_slots = self.get_connected_slots(reference_slot, include_reference=True)
        for open_slot in self.slot_map[self.slot_map["Open"] == True].index:
            for slot in connected_slots:
                output = min(open_slot.get_taxicab_distance(slot), output)
        return output
    
    def is_open(self, slot: Slot):
        return self.slot_map["Open"][slot]
    
    def is_potentially_accessible(self, slot: Slot, ex_slot: Slot):
        if slot is None:
            return False # Not present in Temple
        if self.is_open(slot) == False and (ex_slot is None or self.is_open(ex_slot) == False):
            return False # Impossible to open
        return True # Does not consider that the room could take 4 explosives to open, which is only possible for the Apex
    
    def are_adjacent(self, slot_1, slot_2):
        return self.connection_map.loc[slot_1, slot_2] > -1
    
    def are_adjacent_and_connected(self, slot_1, slot_2):
        return self.connection_map.loc[slot_1, slot_2] == 1
    
    def calc_upgrade_multiplier(self, upgrade_slot, other_slot, connections_to_upgrade):
        upgrade_multiplier = 0
        if upgrade_slot is None:
            return upgrade_multiplier

        if self.are_adjacent(upgrade_slot, other_slot):
            upgrade_multiplier += 1 / 3
        if self.are_adjacent_and_connected(upgrade_slot, other_slot):
            upgrade_multiplier += SCARAB_CONNECTION_FACTOR[connections_to_upgrade - 1]

        return upgrade_multiplier
    
    def get_connections_as_tuples(self):
        # Returns a list of tuples, each tuple contains two connected slots
        row_max = 0
        output = []
        for col in self.connection_map:
            current_row = 0
            for row in self.connection_map.index:
                if current_row == row_max:
                    row_max += 1
                    break
                current_row += 1
                if self.connection_map[col][row] == 1:
                    output.append((col, row))
        return output
    
    def apply_upgrade_room(self):
        upgrade_slot = self.get_slot_with("UP")
        if upgrade_slot is None:
            return
        upgrade_room = self.slot_map["Room"][upgrade_slot]
        upgrade_room = upgrade_room.upgrade()
        if upgrade_room.tier == 3:
            adjacent_to_upgrade = self.get_adjacent_slots(upgrade_slot)
            adjacent_to_upgrade = adjacent_to_upgrade[adjacent_to_upgrade.apply(lambda slot: self.slot_map["Room"][slot].tier) > 0]
            for slot in adjacent_to_upgrade:
                self.slot_map.loc[slot, "Room"] = self.slot_map["Room"][slot].upgrade()
            return
        connected_to_upgrade = self.get_adjacent_and_connected_slots(upgrade_slot)
        connected_to_upgrade = connected_to_upgrade[connected_to_upgrade.apply(lambda slot: self.slot_map["Room"][slot].tier) > 0]
        if upgrade_room.tier >= 1 and len(connected_to_upgrade) > 0:
            choice = np.random.choice(connected_to_upgrade)
            self.slot_map.loc[choice, "Room"] = self.slot_map["Room"][choice].upgrade()
            connected_to_upgrade = connected_to_upgrade[connected_to_upgrade != choice]
        if upgrade_room.tier == 2 and len(connected_to_upgrade) > 1:
            choice = np.random.choice(connected_to_upgrade)
            self.slot_map.loc[choice, "Room"] = self.slot_map["Room"][choice].upgrade()
    
    def apply_explosives_room(self):
        explosives_slot = self.get_slot_with("EX")
        if explosives_slot is None or self.slot_map["Open"][explosives_slot] == False:
            return
        number_of_kegs = self.slot_map["Room"][explosives_slot].tier
        obstructed_rooms = self.slot_map["Room"][self.slot_map["Open"] == False]
        obstructed_rooms = obstructed_rooms[obstructed_rooms.apply(lambda room: room.tier > 0)]
        obstructed_rooms = sorted(obstructed_rooms, key=lambda room: ARCHITECTS["Price"][room.architect], reverse=True)
        pass
    
    def __str__(self):
        r"""
        Sample output:
                    (APX)
                    /   \ 
                (CR2) — ($$2)
                /   \   /   \ 
            (PS2) —*(hh0)*— (UP3)
            /           \   /   \ 
        (MM1)   [LF1]   (MN1) — (PP2)
            \               \   /
            (GM1)   (ENT) — (TM2)
        
        For each layer, adds a room line and a connections line below it (excluding the last layer).
        Adds connections between rooms as / - \.
        Open rooms are surrounded by (). Obstructed rooms use [].
        The chosen incursion room is highlighted with * *.
        """
        temple_string = ""
        layer_idx = 4
        rooms_in_layer = ROOMS_PER_LAYER[layer_idx]
        room_line = (4 - rooms_in_layer) * '    '
        processed_rooms = 0
        for slot_idx in range(len(self.connection_map.columns)):
            slot_idx = len(self.connection_map.columns) - slot_idx - 1
            slot = self.connection_map.columns[slot_idx]
            room = self.slot_map["Room"][slot]
            if self.is_open(slot):
                room_str = f' ({room})  ' # Open rooms
            else:
                room_str = f' [{room}]  ' # Obstructed rooms
            room_line += room_str # Adding all rooms in the layer

            processed_rooms += 1
            if processed_rooms == rooms_in_layer: # Start a new layer if the current layer has no rooms left to process
                temple_string += room_line.rstrip().ljust(32) + '\n'
                if layer_idx > 0:
                    temple_string += ''.ljust(32) + '\n' # Placeholder for connections underneath the current layer
                processed_rooms = 0
                layer_idx -= 1
                rooms_in_layer = ROOMS_PER_LAYER[layer_idx]
                room_line = (4 - rooms_in_layer) * '    '

        temple_list = list(temple_string)
        for connection in self.get_connections_as_tuples():
            reference_slot = connection[0].pick_rightmost(connection[1])
            connection_type = connection[0].relative_direction_from(connection[1])
            slot_idx = temple_string.find(str(self.slot_map["Room"][reference_slot]))
            if connection_type == '—':
                idx_offset = -3 # Same layer
            elif connection_type == '/':
                idx_offset = 32 # Down a layer
            else:
                idx_offset = -34 # Up a layer
            temple_list[slot_idx + idx_offset] = connection_type
        
        return ''.join(temple_list)[:-1]


def generate_random_connections(temple, chance, max_connections):
    connections = temple.connection_map
    added_connections = 0
    for col in connections:
        for row in connections:
            if connections[col][row] == 0:
                if randint(1, chance) == 1:
                    connections.loc[col, row] = 1
                    connections.loc[row, col] = 1
                    added_connections += 1
        if added_connections > max_connections:
            break
    return connections


if __name__ == "__main__":
    # room_themes = set()
    # for room in ROOM_DATA.index:
    #     if ROOM_DATA[room]["Theme"].upper() == ROOM_DATA[room]["Theme"] and len(ROOM_DATA[room]["Theme"]) == 2:
    #         room_themes.add(ROOM_DATA[room]["Theme"] + "1")
    # room_themes = list(room_themes)[:11]
    room_themes = ["aa0", "UN1", "cc0", "EX1", "UP1", "AR1", "ee0", "IT1", "GM1", "hh0", "CR1"]
    room_themes.insert(1, "ENT")
    room_themes.append("APX")
    test = TempleLayout.from_list(room_themes)
    test.connection_map = generate_random_connections(test, 5, 4)
    test.update_open_slots()
    print(test)
    print(test.get_door_priority(Slot(1, 2)))
    # test = Temple.generate()
