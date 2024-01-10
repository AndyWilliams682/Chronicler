import vision
import pandas as pd
from math import floor, ceil
import json
import matplotlib.pyplot as plt


# Maps room names to their "theme" (such as weapons) and their tier (0 to 3)
with open("Rooms.json") as f:
    ROOM_DATA = json.load(f)

# The temple has a fixed shape
ROOMS_PER_LAYER = [3, 4, 3, 2, 1]

# For printing connections
CONNECTION_CHARACTERS = ['/', '—', '\\'] # Down, left, and up


class Temple():
    def __init__(self, hsv_temple_menu):
        # 1F0 is the second layer from the bottom, first room on the right (it is in the first slice)
        # 0F1 is the lowest layer, first room on the right (it is in the second slice)
        # A slice is a line of rooms going from top left to bottom right (\). The right-most slice is slice 0
        empty_rooms = ['0F1', '0F2', '0F3', '1F0', '1F1', '1F2', '1F3', '2F0', '2F1', '2F2', '3F0', '3F1', '4F0']
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
        self.layout = pd.DataFrame(empty_connections, columns=empty_rooms, index=empty_rooms)
        self.room_map = dict()
        self.connections = []
        self.open_rooms = []

        self.chosen_incursion_room = '---'
        self.incursion_options = ('---', '---')

        self.incursions_remaining = 0

        self.read_from_temple_menu(hsv_temple_menu)
    
    def read_from_temple_menu(self, hsv_temple_menu):
        # Rectangles that define the outlines of each room
        room_boxes = vision.get_room_boxes(hsv_temple_menu)

        # Average room dimensions (excluding the chosen room)
        average_room_height = ceil((sum(room[3] for room in room_boxes) - min(room[3] for room in room_boxes)) / (len(room_boxes) - 1))
        average_room_width = ceil((sum(room[2] for room in room_boxes) - min(room[2] for room in room_boxes)) / (len(room_boxes) - 1))

        # Average gap between normal (non-chosen) rooms
        vertical_gap = min(room_boxes[-2][1], room_boxes[-3][1]) - room_boxes[-1][1] - average_room_height # Provides consistency if 3F0 or 3F1 are chosen
        horizontal_gap = abs(room_boxes[-3][0] - room_boxes[-2][0]) - average_room_width
        if average_room_height - room_boxes[-3][3] > 1 or average_room_height - room_boxes[-2][3] > 1: # Checking if either room in layer 3 is chosen
            horizontal_gap = abs(room_boxes[-5][0] - room_boxes[-4][0]) - average_room_width # Using rooms 2F0 and 2F1 instead of 3F0 and 3F1 for accurate gap

        # Reference points/lengths for the incursion submenu (top right corner of Temple screen)
        incursion_submenu_x = floor(room_boxes[-1][0] + (3 / 2) * average_room_width + horizontal_gap) # Fixed distance from Apex x
        incursion_submenu_y = 0 # Top of the temple screen crop
        incursion_submenu_h = room_boxes[-1][1] + 2 * average_room_height + vertical_gap # Fixed distance from Apex y, since this starts at y = 0
        incursion_submenu_w = len(hsv_temple_menu[0]) - incursion_submenu_x # Difference from max x and submenu x
        self.incursion_options = vision.read_incursion_submenu(hsv_temple_menu[incursion_submenu_y:incursion_submenu_y + incursion_submenu_h, incursion_submenu_x:incursion_submenu_x + incursion_submenu_w])
        self.incursion_options = tuple(map(get_room_abbreviation, self.incursion_options))

        # Reference points/lengths for the incursions remaining (near the bottom of the Temple screen)
        incursions_remaining_x = room_boxes[-1][0] - horizontal_gap
        incursions_remaining_y = room_boxes[-1][1] + 5 * (average_room_height + vertical_gap)
        incursions_remaining_w = 2 * horizontal_gap + average_room_width
        incursions_remaining_h = average_room_height
        self.incursions_remaining = vision.read_incursions_remaining(hsv_temple_menu[incursions_remaining_y:incursions_remaining_y + incursions_remaining_h, incursions_remaining_x:incursions_remaining_x + incursions_remaining_w])

        # Important reference points/lengths for the temple
        temple_layer_h = average_room_height + vertical_gap
        temple_apex_y = min(room[1] for room in room_boxes) - floor(vertical_gap / 2) # Apex y is the minumum y for the temple
        layer_room_w = average_room_width + horizontal_gap
        temple_leftmost_x = min(room[0] for room in room_boxes) - floor(horizontal_gap / 2) # x value of furthest left room
        layer_leftmost_x = temple_leftmost_x

        # Iterating over the room boxes to read each room and identify any leftward connections to other rooms
        prev_layer = -1
        for room in room_boxes:
            x, y, w, h = room
            room_layer = 4 - round((y - temple_apex_y) / temple_layer_h)
            if room_layer == prev_layer + 1:
                prev_layer = room_layer
                layer_leftmost_x = temple_leftmost_x + (4 - ROOMS_PER_LAYER[room_layer]) * (1 / 2) * (average_room_width + horizontal_gap)

            room_slice = ROOMS_PER_LAYER[room_layer] - round((x - layer_leftmost_x) / layer_room_w) - 1 + (room_layer == 0)
            room_slot = f'{room_layer}F{room_slice}'
            
            room_name = vision.read_room_text(hsv_temple_menu[y+round(0.4 * h):y+h, x:x+w])

            # Catching OCR issues
            if room_name not in ROOM_DATA.keys():
                print('Something went wrong!', [room_name])
                vision.read_room_text(hsv_temple_menu[y+round(0.4 * h):y+h, x:x+w], debug=True)
            
            abbreviation = get_room_abbreviation(room_name)
            self.room_map[room_slot] = abbreviation
            
            # The chosen room has a smaller box than the typical room, so it is easy to catch here
            if average_room_height - h > 1:
                self.chosen_incursion_room = abbreviation
            
            # Only checks for connections on the left-side of the room. This ensures each connection is only read once.
            room_connection_hsv = hsv_temple_menu[y - vertical_gap:y + h + vertical_gap, x - horizontal_gap:x + round(w / 2)]
            room_connection_hsv[vertical_gap:h + vertical_gap, horizontal_gap:round(w / 2) + horizontal_gap] = (0, 0, 0)
            connection_ys = [0, vertical_gap, h + vertical_gap, h + 2 * vertical_gap]
            direction = -2
            for region_idx in range(len(connection_ys) - 1):
                region_idx = len(connection_ys) - region_idx - 1
                direction += 1
                # Only checks for a connection if there is another room to connect to in that direction from the current room
                # Ex: There cannot be rooms below the lowest layer, so that direction is not checked for layer 0
                if ((direction == -1 and room_layer > 0 and room_slice < 3) or \
                    (direction == 0 and room_slice < ROOMS_PER_LAYER[room_layer] - 1 + (room_layer == 0)) or \
                    (direction == 1 and (room_layer == 0 or room_slice < ROOMS_PER_LAYER[room_layer] - 1))) and \
                    vision.connection_present(room_connection_hsv[connection_ys[region_idx - 1]:connection_ys[region_idx]]):
                        adj_room_slot = get_left_adjacent_room_slot(direction, room_slot)
                        connection_char = CONNECTION_CHARACTERS[direction + 1]
                        self.layout[room_slot][adj_room_slot] = 1
                        self.layout[adj_room_slot][room_slot] = 1
                        self.connections.append((room_slot, adj_room_slot, connection_char))
        
        # May want to remove for easier tracking between Incursions
        self.layout.rename(self.room_map, inplace=True, axis=0)
        self.layout.rename(self.room_map, inplace=True, axis=1)

        self.get_open_rooms()

    def get_open_rooms(self):
        """
        Open rooms are rooms that can be reached from the Entrance. They are found using a DFS.
        """
        self.open_rooms = ['ENT']
        for room in self.open_rooms:
            connections = self.layout.index[self.layout[room] == 1]
            for room in connections:
                if room not in self.open_rooms:
                    self.open_rooms.append(room)
    
    def __str__(self):
        """
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
           1 Incursions Remaining
             LN1 <-- hh0 --> IR1
        
        For each layer, adds a room line and a connections line below it (excluding the last layer).
        Adds connections between rooms as / - \.
        Open rooms are surrounded by (). Obstructed rooms use [].
        The chosen incursion room is highlighted with * *.
        After the temple layout, the incursions remaining and incursion options are displayed as well.
        """
        temple_string = ''
        layer_idx = 4
        rooms_in_layer = ROOMS_PER_LAYER[layer_idx]
        room_line = (4 - rooms_in_layer) * '    '
        processed_rooms = 0
        for room_idx in range(len(self.layout.columns)):
            room_idx = len(self.layout.columns) - room_idx - 1
            room = self.layout.columns[room_idx]
            if room in self.open_rooms:
                room_str = f' ({room})  ' # Opened rooms
            else:
                room_str = f' [{room}]  ' # Obstructed rooms
            if room == self.chosen_incursion_room:
                room_str = room_str.replace(' ', '*', 2) # Highlighting the chosen incursion room
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
        for connection in self.connections:
            reference_room = connection[0]
            connection_type = connection[2]
            room_idx = temple_string.find(self.room_map[reference_room])
            if connection_type == '—':
                idx_offset = -3 # Same layer
            elif connection_type == '/':
                idx_offset = 32 # Down a layer
            else:
                idx_offset = -34 # Up a layer
            temple_list[room_idx + idx_offset] = connection_type
        
        temple_string = ''.join(temple_list)
        incursions_remaining_line = f'{self.incursions_remaining} Incursions Remaining'
        incursions_remaining_line = ' ' * floor((32 - len(incursions_remaining_line) - 1) / 2) + incursions_remaining_line
        temple_string += incursions_remaining_line.ljust(32) + '\n'

        submenu_line = '      ' + self.incursion_options[0] + ' <-- ' + self.chosen_incursion_room + ' --> ' + self.incursion_options[1]
        temple_string += submenu_line.ljust(32)
        return temple_string


def get_room_abbreviation(room_name):
    # Abbreviation is currently set as the theme (two letters, AB) and the room tier (a number)
    # For example, Vault is the tier 1 currency ($$) room, so it is referenced as '$$1'
    # Tier zero rooms are assigned lowercase letters (Pits is hh0).
    # Some rooms have special abbreviations (Entrance ENT, Apex of Atzoatl APX)
    return ROOM_DATA[room_name]["Theme"] + str(ROOM_DATA[room_name]["Tier"])


def get_left_adjacent_room_slot(vertical_direction, room_slot):
    """
    Gets the adjacent room on the left in the vertical direction (-1 is down and left, 0 is straight left, 1 is up and left).
    Room slot is in format xFy, where x is the room's layer and y is the room's slice. The output is also formatted this way.
    """
    adjacent_layer = int(room_slot[0]) + vertical_direction # +1, 0, -1 for above, left, below
    adjacent_slice = int(room_slot[-1]) + (vertical_direction < 1) # Does not change when moving up and left
    return f'{adjacent_layer}F{adjacent_slice}'
